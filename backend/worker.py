import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import SessionLocal
from .contest_service import calculate_attempt_score
from .model import Attempt, Submission, SubmissionKind, SubmissionStatus, TestCase
from .redis_client import redis
from .vm import mini_machine


async def worker():

    try:
        while True:

            # Poll with a Redis-side timeout so the async client never sits on a stale blocking read.
            job = await redis.brpop(
                "submission_queue",
                timeout=1,
            )
            if job is None:
                continue

            submission_id = int(job[1])

            # Use the configured session factory so worker DB access matches the API DATABASE_URL.
            async with SessionLocal() as db:

                result = await judge(
                    submission_id,
                    db
                )

            if not result:
                continue

            await publish_status(submission_id, result["status"])
    finally:
        # Close the Redis connection when the worker is stopped during local testing.
        await redis.aclose()


async def judge(
    submission_id: int,
    db: AsyncSession
):

    query = await db.execute(
        select(Submission).where(
            Submission.id == submission_id
        )
    )

    submission = query.scalar_one_or_none()

    if not submission:
        return None

    submission.status = SubmissionStatus.RUNNING
    await db.commit()
    await publish_status(submission.id, SubmissionStatus.RUNNING)

    test_case_query = await db.execute(
        select(TestCase).where(
            TestCase.question_id == submission.question_id,
            *(
                (TestCase.is_hidden.is_(False),)
                if submission.kind == SubmissionKind.RUN
                else ()
            ),
        )
    )

    test_cases = (
        test_case_query
        .scalars()
        .all()
    )

    # Pass the whole submission so the VM can read code and language consistently.
    response = await mini_machine(submission, test_cases)

    submission.status = response["status"]
    if (
        submission.kind == SubmissionKind.SUBMIT
        and submission.attempt_id is not None
        and submission.status == SubmissionStatus.ACCEPTED
    ):
        await db.flush()
        attempt = await db.get(Attempt, submission.attempt_id)
        if attempt is not None:
            attempt.score = await calculate_attempt_score(db, attempt.id)

    await db.commit()

    return response


async def publish_status(
    submission_id: int,
    status: SubmissionStatus,
) -> None:
    await redis.publish(
        "submission_updates",
        json.dumps({
            "submission_id": submission_id,
            "status": status.value,
        }),
    )


if __name__ == "__main__":
    import asyncio

    try:
        asyncio.run(worker())
    except KeyboardInterrupt:
        pass
