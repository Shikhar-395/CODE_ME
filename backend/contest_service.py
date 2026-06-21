from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import distinct, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .model import (
    Attempt,
    Question,
    Submission,
    SubmissionKind,
    SubmissionStatus,
    Test,
    User,
    UserRole,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def attempt_status(attempt: Attempt | None, now: datetime | None = None) -> str:
    if attempt is None:
        return "not_started"
    current = as_utc(now or utc_now())
    if attempt.submitted_at is not None:
        return (
            "expired"
            if as_utc(attempt.submitted_at) >= as_utc(attempt.expires_at)
            else "completed"
        )
    if current >= as_utc(attempt.expires_at):
        return "expired"
    return "active"


async def calculate_attempt_score(db: AsyncSession, attempt_id: int) -> int:
    score = await db.scalar(
        select(func.count(distinct(Submission.question_id))).where(
            Submission.attempt_id == attempt_id,
            Submission.kind == SubmissionKind.SUBMIT,
            Submission.status == SubmissionStatus.ACCEPTED,
        )
    )
    return int(score or 0)


async def sync_attempt(
    db: AsyncSession,
    attempt: Attempt | None,
    now: datetime | None = None,
) -> Attempt | None:
    if attempt is None:
        return None
    current = as_utc(now or utc_now())
    if attempt.submitted_at is None and current >= as_utc(attempt.expires_at):
        attempt.submitted_at = attempt.expires_at
        attempt.score = await calculate_attempt_score(db, attempt.id)
        await db.commit()
        await db.refresh(attempt)
    return attempt


async def get_user_attempt(
    db: AsyncSession,
    *,
    user_id: int,
    test_id: int,
    sync: bool = True,
) -> Attempt | None:
    attempt = await db.scalar(
        select(Attempt).where(
            Attempt.user_id == user_id,
            Attempt.test_id == test_id,
        )
    )
    if sync:
        return await sync_attempt(db, attempt)
    return attempt


async def require_question_access(
    db: AsyncSession,
    *,
    question: Question,
    user: User,
) -> Attempt | None:
    if user.role == UserRole.ADMIN:
        return None

    attempt = await get_user_attempt(
        db,
        user_id=user.id,
        test_id=question.test_id,
    )
    if attempt is None:
        raise HTTPException(
            status_code=403,
            detail="Start this contest before opening its problems.",
        )
    return attempt


async def resolve_submission_attempt(
    db: AsyncSession,
    *,
    question: Question,
    user: User,
) -> Attempt | None:
    attempt = await require_question_access(db, question=question, user=user)
    if attempt is None:
        return None
    if attempt_status(attempt) == "active":
        return attempt
    return None


async def start_attempt(
    db: AsyncSession,
    *,
    test: Test,
    user: User,
) -> Attempt:
    existing = await get_user_attempt(
        db,
        user_id=user.id,
        test_id=test.id,
    )
    if existing is not None:
        return existing

    started_at = utc_now()
    attempt = Attempt(
        started_at=started_at,
        expires_at=started_at + timedelta(minutes=test.duration),
        score=0,
        user_id=user.id,
        test_id=test.id,
    )
    db.add(attempt)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        concurrent = await get_user_attempt(
            db,
            user_id=user.id,
            test_id=test.id,
        )
        if concurrent is None:
            raise
        return concurrent
    await db.refresh(attempt)
    return attempt
