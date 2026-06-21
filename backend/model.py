from enum import Enum
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

class SubmissionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    ACCEPTED = "accepted"
    WRONG_ANSWER = "wrong_answer"
    TLE = "tle"
    COMPILE_ERROR = "compile_error"
    RUNTIME_ERROR = "runtime_error"

class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class SubmissionKind(str, Enum):
    RUN = "run"
    SUBMIT = "submit"

class Language(str, Enum):
    CPP = "cpp"
    PYTHON = "python"
    JAVA = "java"
    # Keep the API enum aligned with language_config.py runner entries.
    JAVASCRIPT = "javascript"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    created_tests: Mapped[list["Test"]] = relationship(back_populates="creator")
    attempts: Mapped[list["Attempt"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    submissions: Mapped[list["Submission"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class Test(Base):
    __tablename__ = "tests"

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    creator: Mapped["User"] = relationship(back_populates="created_tests")
    questions: Mapped[list["Question"]] = relationship(back_populates="test", cascade="all, delete-orphan")
    attempts: Mapped[list["Attempt"]] = relationship(back_populates="test", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[Difficulty] = mapped_column(
        SQLEnum(Difficulty),
        default=Difficulty.EASY,
        nullable=False,
    )
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"), nullable=False)
    test: Mapped["Test"] = relationship(back_populates="questions")
    test_cases: Mapped[list["TestCase"]] = relationship(back_populates="question", cascade="all, delete-orphan")
    submissions: Mapped[list["Submission"]] = relationship(back_populates="question", cascade="all, delete-orphan")

class TestCase(Base):
    __tablename__ = "test_cases"

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True)
    input_data: Mapped[str] = mapped_column(Text, nullable=False)
    output_data: Mapped[str] = mapped_column(Text, nullable=False)
    is_hidden: Mapped[bool] = mapped_column(default=True, nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    question: Mapped["Question"] = relationship(back_populates="test_cases")

class Attempt(Base):
    __tablename__ = "attempts"
    __table_args__ = (
        UniqueConstraint("user_id", "test_id", name="uq_attempt_user_test"),
    )

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"), nullable=False)
    user: Mapped["User"] = relationship(back_populates="attempts")
    test: Mapped["Test"] = relationship(back_populates="attempts")
    submissions: Mapped[list["Submission"]] = relationship(back_populates="attempt")

class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[Language] = mapped_column(SQLEnum(Language), nullable=False)
    status: Mapped[SubmissionStatus] = mapped_column(
        SQLEnum(SubmissionStatus),
        default=SubmissionStatus.PENDING,
        nullable=False,
    )
    kind: Mapped[SubmissionKind] = mapped_column(
        SQLEnum(SubmissionKind),
        default=SubmissionKind.SUBMIT,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=lambda: datetime.now(timezone.utc))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    attempt_id: Mapped[int | None] = mapped_column(
        ForeignKey("attempts.id", ondelete="SET NULL"),
        nullable=True,
    )
    user: Mapped["User"] = relationship(back_populates="submissions")
    question: Mapped["Question"] = relationship(back_populates="submissions")
    attempt: Mapped["Attempt | None"] = relationship(back_populates="submissions")
