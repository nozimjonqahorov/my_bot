from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, BigInteger, Text, Boolean, String, DateTime, func

from config import DB_PATH
import os
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"ssl": "require"}
)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    telegram_id = Column(BigInteger, primary_key=True, index=True)
    role = Column(String, nullable=False, default="student")  # 'student' or 'teacher'

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(BigInteger, nullable=False)
    is_anonymous = Column(Boolean, nullable=False)
    text_content = Column(Text, nullable=True)
    file_id = Column(Text, nullable=True)
    file_type = Column(String, nullable=True)  # 'text', 'voice', 'video', 'document'
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Answer(Base):
    __tablename__ = "answers"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    question_id = Column(Integer, nullable=False, unique=True)
    teacher_id = Column(BigInteger, nullable=False)
    text_content = Column(Text, nullable=True)
    file_id = Column(Text, nullable=True)
    file_type = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
