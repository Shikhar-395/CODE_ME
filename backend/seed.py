import asyncio
import os

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .auth import hash_password, verify_password
from .database import SessionLocal, engine
from .model import Base, Question, Submission, Test, TestCase, User, UserRole
from .seed_catalog import CATALOG, validate_catalog

RETIRED_SEED_QUESTIONS = {
    "Interview Challenge Pack": {
        "First Unique Character",
        "Array Intersection",
    },
}


def seed_credentials() -> tuple[str, str, str]:
    name = os.getenv("SEED_ADMIN_NAME", "Singh").strip()
    username = os.getenv("SEED_ADMIN_USERNAME", "").strip()
    password = os.getenv("SEED_ADMIN_PASSWORD", "")
    if not username or not password:
        raise RuntimeError(
            "SEED_ADMIN_USERNAME and SEED_ADMIN_PASSWORD are required "
            "when seeding demo data."
        )
    return name, username, password


async def seed_demo_data(
    session_factory: async_sessionmaker[AsyncSession] = SessionLocal,
) -> dict[str, int]:
    validate_catalog()
    name, username, password = seed_credentials()
    created = {"users": 0, "tests": 0, "questions": 0, "test_cases": 0}

    async with session_factory() as db:
        admin = await db.scalar(select(User).where(User.username == username))
        if admin is None:
            admin = User(
                name=name,
                username=username,
                password=hash_password(password),
                role=UserRole.ADMIN,
            )
            db.add(admin)
            await db.flush()
            created["users"] += 1
        else:
            admin.name = name
            admin.role = UserRole.ADMIN
            valid, upgraded_hash = verify_password(password, admin.password)
            if not valid:
                admin.password = hash_password(password)
            elif upgraded_hash:
                admin.password = upgraded_hash

        for contest_seed in CATALOG:
            test = await db.scalar(
                select(Test).where(Test.title == contest_seed.title)
            )
            if test is None:
                test = Test(
                    title=contest_seed.title,
                    description=contest_seed.description,
                    duration=contest_seed.duration,
                    created_by=admin.id,
                )
                db.add(test)
                await db.flush()
                created["tests"] += 1
            else:
                test.description = contest_seed.description
                test.duration = contest_seed.duration
                test.created_by = admin.id

            retired_titles = RETIRED_SEED_QUESTIONS.get(contest_seed.title, set())
            if retired_titles:
                retired_questions = (
                    await db.execute(
                        select(Question).where(
                            Question.test_id == test.id,
                            Question.title.in_(retired_titles),
                        )
                    )
                ).scalars().all()
                for retired in retired_questions:
                    has_submissions = await db.scalar(
                        select(Submission.id)
                        .where(Submission.question_id == retired.id)
                        .limit(1)
                    )
                    if has_submissions is None:
                        await db.delete(retired)

            for question_seed in contest_seed.questions:
                question = await db.scalar(
                    select(Question).where(
                        Question.test_id == test.id,
                        Question.title == question_seed.title,
                    )
                )
                if question is None:
                    question = Question(
                        title=question_seed.title,
                        description=question_seed.description,
                        difficulty=question_seed.difficulty,
                        test_id=test.id,
                    )
                    db.add(question)
                    await db.flush()
                    created["questions"] += 1
                else:
                    question.description = question_seed.description
                    question.difficulty = question_seed.difficulty

                existing_cases = (
                    await db.execute(
                        select(TestCase).where(
                            TestCase.question_id == question.id
                        )
                    )
                ).scalars().all()
                expected_by_key = {
                    (case.input_data, case.is_hidden): case
                    for case in question_seed.cases
                }
                existing_by_key: dict[tuple[str, bool], TestCase] = {}
                for existing in existing_cases:
                    key = (existing.input_data, existing.is_hidden)
                    expected = expected_by_key.get(key)
                    if expected is None or key in existing_by_key:
                        await db.delete(existing)
                        continue
                    existing.output_data = expected.output_data
                    existing_by_key[key] = existing

                for case_seed in question_seed.cases:
                    key = (case_seed.input_data, case_seed.is_hidden)
                    if key in existing_by_key:
                        continue
                    db.add(
                        TestCase(
                            input_data=case_seed.input_data,
                            output_data=case_seed.output_data,
                            is_hidden=case_seed.is_hidden,
                            question_id=question.id,
                        )
                    )
                    created["test_cases"] += 1

        await db.commit()

    return created


async def main() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    created = await seed_demo_data()
    print(
        "Demo seed complete: "
        + ", ".join(f"{key}={value}" for key, value in created.items())
    )


if __name__ == "__main__":
    asyncio.run(main())
