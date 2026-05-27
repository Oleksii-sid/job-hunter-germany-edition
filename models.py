import os
from sqlalchemy import create_engine, Column, Integer, String, Text, Date, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# 🔹 URL бази (Docker)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://user_admin:secret_password@db:5432/jobs_db",
)

# 🔹 Engine (з налаштуваннями стабільності)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    future=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
)

Base = declarative_base()


# ================================
# 📌 Вакансії
# ================================
class Vacancy(Base):
    __tablename__ = "vacancies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), unique=True, index=True, nullable=False)
    city = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    ai_cover_letter = Column(Text, nullable=True)
    status = Column(String(50), default="new", index=True)

    # Використовуємо функцію сервера для часу
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# ================================
# 📌 Користувач (Згідно з DIN 5008 та DSGVO)
# ================================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    academic_title = Column(String(50))  # Напр. Dr., M.Sc.
    birth_date = Column(Date)

    # Розділена адреса для правильної "шапки" листа
    street = Column(String(200))
    house_number = Column(String(20))
    zip_code = Column(String(20))
    city = Column(String(100))

    email = Column(String(300), unique=True, index=True)
    phone = Column(String(50))
    linkedin = Column(String(300))

    # Згода на обробку даних (DSGVO)
    consent_given = Column(Boolean, default=False)
    consent_date = Column(DateTime, server_default=func.now())

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Зв'язки
    education = relationship("Education", back_populates="user", cascade="all, delete")
    experience = relationship("Experience", back_populates="user", cascade="all, delete")
    skills = relationship("Skill", back_populates="user", cascade="all, delete")
    languages = relationship("Language", back_populates="user", cascade="all, delete")
    documents = relationship("Document", back_populates="user", cascade="all, delete")


# ================================
# 📌 Освіта, Досвід, Навички
# ================================
class Education(Base):
    __tablename__ = "education"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    school_name = Column(String(300))
    degree = Column(String(200))  # Напр. Bachelor, Master
    field = Column(String(200))  # Спеціальність
    start_date = Column(Date)
    end_date = Column(Date)
    user = relationship("User", back_populates="education")


class Experience(Base):
    __tablename__ = "experience"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    company = Column(String(300))
    position = Column(String(300))
    start_date = Column(Date)
    end_date = Column(Date)
    description = Column(Text)  # Опис обов'язків (важливо для ШІ)
    user = relationship("User", back_populates="experience")


class Skill(Base):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    skill_name = Column(String(200))
    level = Column(String(50))  # Напр. Advanced, Expert
    user = relationship("User", back_populates="skills")


# ================================
# 📌 Мови (Критично для Німеччини)
# ================================
class Language(Base):
    __tablename__ = "languages"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    language_name = Column(String(100))  # German, English
    level = Column(String(50))  # A2, B2, C1, Native
    user = relationship("User", back_populates="languages")


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    doc_type = Column(String(100))  # CV, Diploma, Certificate
    file_path = Column(Text)
    uploaded_at = Column(DateTime, server_default=func.now())
    user = relationship("User", back_populates="documents")


# ================================
# 📌 Системні налаштування
# ================================
class CompanySite(Base):
    __tablename__ = "company_sites"
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(200), nullable=False)
    career_url = Column(String(1000), unique=True, nullable=False)
    job_container_selector = Column(String(300))
    is_active = Column(Boolean, default=True)
    last_scanned = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    # Створює всі таблиці, яких ще немає в БД
    Base.metadata.create_all(bind=engine)
