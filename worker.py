import logging
from sqlalchemy.orm import Session
from models import SessionLocal, Vacancy
# Імпорт StepStone працює, Indeed закоментований
from parser import search_stepstone #, search_indeed_selenium
import asyncio

logging.basicConfig(level=logging.INFO)

async def process_new_jobs(keyword: str, city: str):
    logging.info(f"🔄 Worker: Починаю парсинг для {keyword} у {city}...")
    db: Session = SessionLocal()

    try:
        # 🔹 1. Парсимо StepStone (Playwright)
        stepstone_jobs = await search_stepstone(keyword, city)

        # 🔹 2. Тимчасово створюємо порожній список для Indeed
        # Це потрібно, щоб код нижче не "падав"
        indeed_jobs = []

        # Коли захочеш повернути Indeed, розкоментуй код нижче:
        """
        loop = asyncio.get_running_loop()
        indeed_jobs = await loop.run_in_executor(
            None,
            lambda: search_indeed_selenium(keyword, city, limit=5)
        )
        """

        # 🔹 3. Об'єднуємо результати
        found_jobs = stepstone_jobs + indeed_jobs
        logging.info(f"🔎 Знайдено вакансій: {len(found_jobs)}")

        if not found_jobs:
            logging.info("⚠️ Вакансії не знайдені")
            return

        for job in found_jobs:
            try:
                url = job.get("url")
                title = job.get("title")
                if not url or not title:
                    continue

                # 🔹 Перевірка на дублікати
                exists = db.query(Vacancy).filter(Vacancy.url == url).first()
                if exists:
                    continue

                # 🔹 Зберігаємо вакансію
                new_vacancy = Vacancy(
                    title=title,
                    url=url,
                    city=city,
                    status="new",
                )
                db.add(new_vacancy)
                logging.info(f"✅ Додано в базу: {title}")

            except Exception as e:
                logging.error(f"Помилка обробки вакансії: {e}")
                continue

        db.commit()
        logging.info("💾 Всі нові вакансії збережені.")

    except Exception as e:
        db.rollback()
        logging.error(f"❌ Критична помилка Worker: {e}")

    finally:
        db.close()
        logging.info("🏁 Роботу Worker завершено.")
