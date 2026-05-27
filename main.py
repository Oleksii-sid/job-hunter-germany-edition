import logging
import asyncio
import os

from fastapi import FastAPI, Request, Form, BackgroundTasks, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

# Імпорти моделей (додано User та супутні)
from models import Vacancy, User, Education, Experience, Skill, Language, init_db, get_db
from worker import process_new_jobs
from ai_service import generate_cover_letter

app = FastAPI(title="Job Parser AI")
templates = Jinja2Templates(directory="templates")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.on_event("startup")
def startup_event():
    logger.info("🚀 Ініціалізація бази даних...")
    init_db()


# ================= 1. DASHBOARD =================
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    vacancies = db.query(Vacancy).order_by(Vacancy.id.desc()).all()
    user = db.query(User).first()  # Перевіряємо чи є профіль
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "vacancies": vacancies, "user": user}
    )


# ================= 2. ПРОФІЛЬ КОРИСТУВАЧА =================
@app.get("/profile", response_class=HTMLResponse)
async def get_profile(request: Request, db: Session = Depends(get_db)):
    user = db.query(User).first()
    return templates.TemplateResponse("profile.html", {"request": request, "user": user})


@app.post("/profile/save")
async def save_profile(
        first_name: str = Form(...),
        last_name: str = Form(...),
        email: str = Form(...),
        city: str = Form(...),
        street: str = Form(...),
        zip_code: str = Form(...),
        db: Session = Depends(get_db)
):
    user = db.query(User).first()
    if not user:
        user = User()

    user.first_name = first_name
    user.last_name = last_name
    user.email = email
    user.city = city
    user.street = street
    user.zip_code = zip_code

    db.add(user)
    db.commit()
    return RedirectResponse(url="/profile", status_code=303)


# ================= 3. ПАРСИНГ ТА ГЕНЕРАЦІЯ =================
@app.post("/start_search")
async def start_search(bt: BackgroundTasks, keyword: str = Form(...), city: str = Form(...)):
    bt.add_task(process_new_jobs, keyword, city)
    return RedirectResponse(url="/", status_code=303)


@app.post("/generate/{v_id}")
async def create_letter(v_id: int, db: Session = Depends(get_db)):
    try:
        letter_text = await generate_cover_letter(v_id, db)
        if not letter_text:
            return JSONResponse({"status": "error", "message": "AI failed"}, status_code=500)

        vacancy = db.query(Vacancy).filter(Vacancy.id == v_id).first()
        db.refresh(vacancy)
        return JSONResponse({"status": "ok", "cover_letter": vacancy.ai_cover_letter})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


# ================= 4. ОНОВЛЕНЕ ОЧИЩЕННЯ (З ГАЛОЧКОЮ) =================
@app.post("/clear")
async def clear_database(
        db: Session = Depends(get_db),
        delete_user: bool = Form(False)  # Отримуємо статус галочки
):
    try:
        # Завжди видаляємо вакансії
        db.query(Vacancy).delete()

        if delete_user:
            # Видаляємо все, включаючи профіль
            db.query(Education).delete()
            db.query(Experience).delete()
            db.query(Skill).delete()
            db.query(Language).delete()
            db.query(User).delete()
            logger.info("🗑️ Базу та особисті дані повністю очищено")
        else:
            logger.info("✅ Вакансії видалено, профіль збережено")

        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Помилка очищення: {e}")

    return RedirectResponse(url="/", status_code=303)
