from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    Integer,
    String,
    Text,
    ForeignKey,
    Enum as SQLEnum,
    DateTime,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from database import Base


# =====================
# ENUMS
# =====================

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class SubmissionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    ACCEPTED = "accepted"
    WRONG_ANSWER = "wrong_answer"
    TLE = "tle"
    COMPILE_ERROR = "compile_error"
    RUNTIME_ERROR = "runtime_error"


class Language(str, Enum):
    CPP = "cpp"
    PYTHON = "python"
    JAVA = "java"


# =====================
# USER
# =====================

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    username: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False
    )

    password: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        default=UserRole.USER
    )

    created_tests: Mapped[list["Test"]] = relationship(
        back_populates="creator"
    )

    attempts: Mapped[list["Attempt"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

    submissions: Mapped[list["Submission"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )


# =====================
# TEST / ASSESSMENT
# =====================

class Test(Base):
    __tablename__ = "tests"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    title: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )

    duration_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    creator: Mapped["User"] = relationship(
        back_populates="created_tests"
    )

    questions: Mapped[list["Question"]] = relationship(
        back_populates="test",
        cascade="all, delete-orphan"
    )

    attempts: Mapped[list["Attempt"]] = relationship(
        back_populates="test",
        cascade="all, delete-orphan"
    )


# =====================
# QUESTION
# =====================

class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    title: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    test_id: Mapped[int] = mapped_column(
        ForeignKey(
            "tests.id",
            ondelete="CASCADE"
        )
    )

    test: Mapped["Test"] = relationship(
        back_populates="questions"
    )

    test_cases: Mapped[list["TestCase"]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan"
    )

    submissions: Mapped[list["Submission"]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan"
    )


# =====================
# TEST CASE
# =====================

class TestCase(Base):
    __tablename__ = "test_cases"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    input_data: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    expected_output: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    is_hidden: Mapped[bool] = mapped_column(
        default=True
    )

    question_id: Mapped[int] = mapped_column(
        ForeignKey(
            "questions.id",
            ondelete="CASCADE"
        )
    )

    question: Mapped["Question"] = relationship(
        back_populates="test_cases"
    )


# =====================
# ATTEMPT
# =====================

class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    score: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        )
    )

    test_id: Mapped[int] = mapped_column(
        ForeignKey(
            "tests.id",
            ondelete="CASCADE"
        )
    )

    user: Mapped["User"] = relationship(
        back_populates="attempts"
    )

    test: Mapped["Test"] = relationship(
        back_populates="attempts"
    )


# =====================
# SUBMISSION
# =====================

class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    code: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    language: Mapped[Language] = mapped_column(
        SQLEnum(Language)
    )

    status: Mapped[SubmissionStatus] = mapped_column(
        SQLEnum(SubmissionStatus),
        default=SubmissionStatus.PENDING
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        )
    )

    question_id: Mapped[int] = mapped_column(
        ForeignKey(
            "questions.id",
            ondelete="CASCADE"
        )
    )

    user: Mapped["User"] = relationship(
        back_populates="submissions"
    )

    question: Mapped["Question"] = relationship(
        back_populates="submissions"
    )