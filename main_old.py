import logging
import asyncio

from fastapi import FastAPI, Request, Form, BackgroundTasks, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

# Переконайся, що ці файли існують в тій же папці
from models import Vacancy, init_db, get_db
from worker import process_new_jobs
from ai_service import generate_cover_letter

# ================= LOGGING =================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================= APP =================
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# ✅ Підключаємо роутери (переконайся, що файл routers/email_router.py існує)
try:
    from routers.email_router import router as email_router

    app.include_router(email_router)
except ImportError:
    logger.warning("⚠️ Email router не знайдено, пропускаємо...")


# ================= DB INIT =================
# ВАЖЛИВО: init_db() має викликатися при старті,
# але іноді краще робити це через lifespan або перевіряти DATABASE_URL
@app.on_event("startup")
def startup_event():
    logger.info("🚀 Ініціалізація бази даних...")
    init_db()


# =====================================================
# 🏠 DASHBOARD
# =====================================================
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    # Використовуємо спрощений запит без expire_all, якщо це не критично
    vacancies = db.query(Vacancy).order_by(Vacancy.id.desc()).all()
    logger.info(f"📊 Перевірка бази: знайдено {len(vacancies)} вакансій")

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "vacancies": vacancies}
    )


# =====================================================
# 🔍 START PARSING
# =====================================================
@app.post("/start_search")
async def start_search(
        bt: BackgroundTasks,
        keyword: str = Form(...),
        city: str = Form(...)
):
    logger.info(f"🚀 Отримано сигнал на парсинг: {keyword} у {city}")

    # Запускаємо воркер у фоні
    bt.add_task(process_new_jobs, keyword, city)

    # 303 See Other — правильний статус для редіректу після POST
    return RedirectResponse(url="/", status_code=303)


# =====================================================
# 🤖 GENERATE COVER LETTER (FIXED)
# =====================================================
@app.post("/generate/{v_id}")
async def create_letter(v_id: int, db: Session = Depends(get_db)):
    logger.info(f"🤖 Генерація листа для вакансії ID: {v_id}")

    vacancy = db.query(Vacancy).filter(Vacancy.id == v_id).first()
    if not vacancy:
        raise HTTPException(status_code=404, detail="Vacancy not found")

    try:
        # Переконайся, що функція generate_cover_letter в ai_service.py — асинхронна (async def)
        await generate_cover_letter(vacancy, db)

        # Обов'язково робимо commit, щоб зберегти лист у базу
        db.commit()
        db.refresh(vacancy)

        return JSONResponse({
            "status": "ok",
            "cover_letter": vacancy.ai_cover_letter
        })

    except Exception as e:
        logger.exception("❌ Помилка генерації листа")
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=500
        )


# =====================================================
# 🗑 CLEAR DATABASE
# =====================================================
@app.get("/clear")
async def clear_jobs(db: Session = Depends(get_db)):
    try:
        db.query(Vacancy).delete()
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Помилка очищення бази: {e}")
    return RedirectResponse(url="/", status_code=303)
