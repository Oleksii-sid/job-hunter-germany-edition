import os
import logging
import google.generativeai as genai
from sqlalchemy.orm import Session
from models import Vacancy

# Ініціалізація
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)


async def generate_cover_letter(vacancy_id: int, db: Session):
    """
    Стабільна генерація листа. Працюємо через ID, щоб уникнути помилок сесії.
    """
    if not api_key:
        logging.error("❌ API Key missing")
        return None

    # 1. Отримуємо об'єкт з бази (refresh гарантує актуальність даних)
    vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
    if not vacancy:
        logging.error(f"❌ Vacancy {vacancy_id} not found")
        return None

    # 2. Очищення та підготовка даних (важливо!)
    title = str(vacancy.title or "Software Entwickler")
    company = str(getattr(vacancy, 'company', 'unbekanntes Unternehmen') or 'unbekanntes Unternehmen')
    city = str(vacancy.city or "Deutschland")
    description = str(vacancy.description or "")[:2000]  # Обмежуємо довжину

    # Визначаємо привітання
    contact = getattr(vacancy, "contact_name", None)
    greeting = f"Sehr geehrte/r {contact}," if contact else "Sehr geehrte Damen und Herren,"

    model = genai.GenerativeModel('gemini-1.5-flash')  # Використовуємо актуальну назву моделі

    prompt = f"""
Du bist ein deutscher Karriere-Coach. Erstelle ein Anschreiben nach DIN 5008.
STELLE: {title}
FIRMA: {company}
STADT: {city}
INFO: {description}

REGELN:
- Betreff: Bewerbung als {title}
- Anrede: {greeting}
- Sprache: Deutsch (professionell).
- Ende: "Mit freundlichen Grüßen", danach [Vorname Nachname].
- NUR den Text des Briefes ausgeben.
"""

    try:
        # 3. Сама генерація
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,  # Менше творчості, більше ділового стилю
                candidate_count=1
            )
        )

        if not response.text:
            raise ValueError("Empty AI response")

        # 4. Запис у базу
        vacancy.ai_cover_letter = response.text.strip()
        vacancy.status = "AI_GENERATED"

        db.add(vacancy)
        db.commit()
        logging.info(f"✅ Success for ID {vacancy_id}")
        return vacancy.ai_cover_letter

    except Exception as e:
        db.rollback()  # Скасовуємо зміни при помилці
        logging.error(f"❌ Error for ID {vacancy_id}: {str(e)}")
        return None