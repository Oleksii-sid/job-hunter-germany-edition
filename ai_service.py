import os
import logging
from google import genai
from sqlalchemy.orm import Session
from models import Vacancy, User

logger = logging.getLogger(__name__)

# Ініціалізація сучасного клієнта Google GenAI
# Ключ автоматично шукається в системній змінній GEMINI_API_KEY
client = genai.Client()


async def generate_cover_letter(vacancy_id: int, db: Session) -> str:
    try:
        # 1. Отримуємо вакансію з БД
        vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
        if not vacancy:
            logger.error(f"❌ Вакансію з ID {vacancy_id} не знайдено в БД")
            return ""

        # 2. Отримуємо профіль користувача
        user = db.query(User).first()
        user_info = "Кандидат ще не заповнив профіль. Напиши загальний шаблон листа."
        if user:
            user_info = f"""
            Ім'я та Прізвище: {user.first_name} {user.last_name}
            Email: {user.email}
            Адреса: {user.street}, {user.zip_code} {user.city}, Germany
            """

        # 3. Формуємо промпт
        prompt_text = f"""
        You are an expert career coach. Write a professional Anschreiben (Cover Letter) in German.
        Follow standard German business etiquette (DIN 5008 alignment).

        ### APPLICANT PROFILE:
        {user_info}

        ### JOB VACANCY DETAILS:
        Title: {vacancy.title}
        Company: {vacancy.company}
        Location: {vacancy.location}
        Description: {vacancy.description}
        """

        logger.info(f"🧠 Надсилаємо запит до Gemini для вакансії ID {vacancy_id}...")

        # 4. Виклик актуальної моделі за новим синтаксисом (генерація тексту є синхронною/блокуючою у genai клієнті)
        response = client.models.generate_content(
            model='gemini-2.5-flash',  # Найновіша швидка модель
            contents=prompt_text,
        )

        cover_letter_text = response.text
        if not cover_letter_text:
            logger.error("❌ ШІ повернув порожню відповідь")
            return ""

        # 5. Зберігаємо в БД
        vacancy.ai_cover_letter = cover_letter_text
        db.commit()

        logger.info(f"✅ Лист для ID {vacancy_id} успішно збережено!")
        return cover_letter_text

    except Exception as e:
        db.rollback()
        logger.error(f"💥 Критична помилка в generate_cover_letter: {str(e)}")
        return ""
