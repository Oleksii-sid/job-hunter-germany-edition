import os
import logging
from openai import AsyncOpenAI
from sqlalchemy.orm import Session
from models import Vacancy, User

logger = logging.getLogger(__name__)

# Ініціалізація асинхронного клієнта OpenAI
# Ключ автоматично береться з системної змінної OPENAI_API_KEY
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def generate_cover_letter(vacancy_id: int, db: Session) -> str:
    try:
        # 1. Отримуємо вакансію з бази даних
        vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
        if not vacancy:
            logger.error(f"❌ Вакансію з ID {vacancy_id} не знайдено в БД")
            return ""

        # 2. Отримуємо профіль користувача
        user = db.query(User).first()

        # Створюємо текстовий блок профілю (захист на випадок, якщо профіль пустий)
        user_info = "Кандидат ще не заповнив профіль. Напиши загальний шаблон листа."
        if user:
            user_info = f"""
            Ім'я та Прізвище: {user.first_name} {user.last_name}
            Email: {user.email}
            Адреса: {user.street}, {user.zip_code} {user.city}, Germany
            """

        # 3. Формуємо промпт для ШІ під німецькі стандарти (DIN 5008)
        system_prompt = (
            "You are an expert career coach helping a candidate apply for a job in Germany. "
            "Write a highly professional Anschreiben (Cover Letter) in German. Follow standard German business etiquette. "
            "Do not use placeholders like [Date] or [Company Address] if info is missing—skip them or format cleanly."
        )

        user_prompt = f"""
        Write a cover letter based on this information:

        ### APPLICANT PROFILE:
        {user_info}

        ### JOB VACANCY DETAILS:
        Title: {vacancy.title}
        Company: {vacancy.company}
        Location: {vacancy.location}
        Description: {vacancy.description}

        Requirements for the response:
        1. Language: GERMAN.
        2. Professional, confident, and polite tone.
        3. Match applicant details with job requirements convincingly.
        """

        logger.info(f"🧠 Надсилаємо запит до OpenAI для вакансії ID {vacancy_id}...")

        # 4. Асинхронний запит до API OpenAI (сучасний синтаксис)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",  # Оптимальна та швидка модель
            messages=[
                {"role": "system", content: system_prompt},
                {"role": "user", content: user_prompt}
            ],
            temperature=0.7
        )

        # 5. Витягуємо текст відповіді
        cover_letter_text = response.choices[0].message.content
        if not cover_letter_text:
            logger.error("❌ ШІ повернув порожню відповідь")
            return ""

        # 6. Записуємо результат у вакансію та зберігаємо в БД
        vacancy.ai_cover_letter = cover_letter_text
        db.commit()

        logger.info(f"✅ Супровідний лист для ID {vacancy_id} успішно згенеровано та збережено!")
        return cover_letter_text

    except Exception as e:
        db.rollback()  # Скасовуємо транзакцію у разі помилки БД
        logger.error(f"💥 Критична помилка в generate_cover_letter: {str(e)}")
        return ""
