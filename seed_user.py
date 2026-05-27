import os
from datetime import date
from sqlalchemy.orm import Session
from models import SessionLocal, User, Education, Experience, Skill, Language

def seed_user():
    db: Session = SessionLocal()
    try:
        # 1. Перевіряємо, чи вже є користувач
        existing_user = db.query(User).filter(User.email == "user@example.com").first()
        if existing_user:
            print("⚠️ Користувач вже існує в базі.")
            return

        print("🚀 Починаємо заповнення профілю...")

        # 2. Створюємо основного користувача
        new_user = User(
            first_name="Oleksandr",
            last_name="New",
            academic_title="M.Sc.",  # Якщо є ступінь
            birth_date=date(1990, 1, 1),
            street="Mustermannstraße",
            house_number="10",
            zip_code="54290",
            city="Trier",
            email="user@example.com",
            phone="+49 123 4567890",
            linkedin="https://linkedin.com",
            consent_given=True
        )
        db.add(new_user)
        db.flush()  # Отримуємо ID користувача для зв'язків

        # 3. Додаємо освіту
        edu = Education(
            user_id=new_user.id,
            school_name="National Technical University",
            degree="Master of Science",
            field="Computer Science",
            start_date=date(2008, 9, 1),
            end_date=date(2013, 6, 30)
        )
        db.add(edu)

        # 4. Додаємо досвід (важливо для ШІ)
        exp = Experience(
            user_id=new_user.id,
            company="Tech Solutions GmbH",
            position="Python Developer",
            start_date=date(2019, 1, 1),
            end_date=date(2023, 12, 31),
            description="Entwicklung von Web-Scrapern, Automatisierung von Prozessen mit Python und FastAPI."
        )
        db.add(exp)

        # 5. Додаємо навички
        skills = [
            Skill(user_id=new_user.id, skill_name="Python", level="Expert"),
            Skill(user_id=new_user.id, skill_name="Docker", level="Advanced"),
            Skill(user_id=new_user.id, skill_name="PostgreSQL", level="Advanced"),
            Skill(user_id=new_user.id, skill_name="FastAPI", level="Expert")
        ]
        db.add_all(skills)

        # 6. Додаємо мови (критично для Німеччини)
        languages = [
            Language(user_id=new_user.id, language_name="Deutsch", level="B2"),
            Language(user_id=new_user.id, language_name="English", level="C1"),
            Language(user_id=new_user.id, language_name="Ukrainian", level="Native")
        ]
        db.add_all(languages)

        db.commit()
        print("✅ Профіль успішно створено!")

    except Exception as e:
        db.rollback()
        print(f"❌ Помилка: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_user()
