import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, Date, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# 🔹 URL базы (Docker)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://user_admin:secret_password@db:5432/jobs_db",
)

# 🔹 Engine (стабилен к разрывам соединения)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    future=True,
)

# 🔹 Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
)

Base = declarative_base()

# ================================
# 📌 Vacancy model
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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


# ========================================================
# 📌 CompanySite model
# ========================================================
class CompanySite(Base):
    __tablename__ = "company_sites"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(200), nullable=False, index=True)
    career_url = Column(String(1000), unique=True, nullable=False, index=True)
    job_container_selector = Column(String(300), nullable=True)
    title_selector = Column(String(300), nullable=True)
    link_selector = Column(String(300), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    last_scanned = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


# ================================
# 📌 User (соискатель)
# ================================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    full_name = Column(String(300))
    birth_date = Column(Date)
    address = Column(Text)
    email = Column(String(300))
    phone = Column(String(50))
    linkedin = Column(String(300))

    consent_given = Column(Boolean, default=False)
    consent_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    education = relationship("Education", back_populates="user", cascade="all, delete")
    experience = relationship("Experience", back_populates="user", cascade="all, delete")
    skills = relationship("Skill", back_populates="user", cascade="all, delete")
    documents = relationship("Document", back_populates="user", cascade="all, delete")


# ================================
# 📌 Education
# ================================
class Education(Base):
    __tablename__ = "education"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    school_name = Column(String(300))
    degree = Column(String(200))
    field = Column(String(200))
    start_date = Column(Date)
    end_date = Column(Date)
    certificate_file = Column(Text)  # путь к PDF

    user = relationship("User", back_populates="education")


# ================================
# 📌 Experience
# ================================
class Experience(Base):
    __tablename__ = "experience"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    company = Column(String(300))
    position = Column(String(300))
    start_date = Column(Date)
    end_date = Column(Date)
    description = Column(Text)

    user = relationship("User", back_populates="experience")


# ================================
# 📌 Skill
# ================================
class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    skill_name = Column(String(200))
    level = Column(String(50))  # начальный/средний/продвинутый

    user = relationship("User", back_populates="skills")


# ================================
# 📌 Document
# ================================
class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    doc_type = Column(String(100))  # diploma, certificate, anerkennung
    file_path = Column(Text)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="documents")


# ================================
# 📌 FastAPI dependency
# ================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ================================
# 📌 init tables
# ================================
def init_db():
    Base.metadata.create_all(bind=engine)