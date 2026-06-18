import asyncio
import os
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .auth import hash_password, verify_password
from .database import SessionLocal, engine
from .model import Base, Question, Test, TestCase, User, UserRole


@dataclass(frozen=True)
class SeedCase:
    input_data: str
    output_data: str
    is_hidden: bool


@dataclass(frozen=True)
class SeedQuestion:
    title: str
    description: str
    cases: tuple[SeedCase, ...]


@dataclass(frozen=True)
class SeedTest:
    title: str
    description: str
    duration: int
    questions: tuple[SeedQuestion, ...]


DEMO_TESTS = (
    SeedTest(
        title="Arrays & Strings Foundations",
        description="Warm up with essential array and string techniques.",
        duration=45,
        questions=(
            SeedQuestion(
                title="Two Sum Indices",
                description=(
                    "Given n integers and a target, print the zero-based indices "
                    "of the first pair whose values add to the target. Input: n "
                    "and target on the first line, followed by n integers. "
                    "Print the two indices in increasing order."
                ),
                cases=(
                    SeedCase("4 9\n2 7 11 15\n", "0 1\n", False),
                    SeedCase("3 6\n3 2 4\n", "1 2\n", False),
                    SeedCase("5 10\n1 8 5 2 9\n", "0 4\n", True),
                    SeedCase("4 0\n-3 4 3 90\n", "0 2\n", True),
                ),
            ),
            SeedQuestion(
                title="Reverse Words",
                description=(
                    "Read one line of text and print its words in reverse order. "
                    "Collapse repeated spaces and do not add leading or trailing spaces."
                ),
                cases=(
                    SeedCase("the sky is blue\n", "blue is sky the\n", False),
                    SeedCase("hello world\n", "world hello\n", False),
                    SeedCase("  code   every day  \n", "day every code\n", True),
                    SeedCase("single\n", "single\n", True),
                ),
            ),
            SeedQuestion(
                title="Valid Palindrome",
                description=(
                    "Read one line and determine whether it is a palindrome after "
                    "ignoring punctuation, spaces, and letter case. Print true or false."
                ),
                cases=(
                    SeedCase(
                        "A man, a plan, a canal: Panama\n",
                        "true\n",
                        False,
                    ),
                    SeedCase("race a car\n", "false\n", False),
                    SeedCase("No 'x' in Nixon\n", "true\n", True),
                    SeedCase("0P\n", "false\n", True),
                ),
            ),
        ),
    ),
    SeedTest(
        title="Core Algorithms Sprint",
        description="Practice searching, dynamic programming, and ordered data.",
        duration=60,
        questions=(
            SeedQuestion(
                title="Binary Search",
                description=(
                    "Given a sorted array, print the zero-based index of target or "
                    "-1 when absent. Input: n and target, then n sorted integers."
                ),
                cases=(
                    SeedCase("6 9\n-1 0 3 5 9 12\n", "4\n", False),
                    SeedCase("6 2\n-1 0 3 5 9 12\n", "-1\n", False),
                    SeedCase("1 7\n7\n", "0\n", True),
                    SeedCase("7 -5\n-9 -5 -1 0 4 8 12\n", "1\n", True),
                ),
            ),
            SeedQuestion(
                title="Maximum Subarray Sum",
                description=(
                    "Given n integers, print the largest sum of a non-empty "
                    "contiguous subarray. Input: n, followed by the array."
                ),
                cases=(
                    SeedCase(
                        "9\n-2 1 -3 4 -1 2 1 -5 4\n",
                        "6\n",
                        False,
                    ),
                    SeedCase("1\n5\n", "5\n", False),
                    SeedCase("4\n-8 -3 -6 -2\n", "-2\n", True),
                    SeedCase("6\n1 2 3 -10 4 5\n", "9\n", True),
                ),
            ),
            SeedQuestion(
                title="Merge Sorted Arrays",
                description=(
                    "Merge two sorted integer arrays. Input: n and m, then one "
                    "line for each array. Print the merged values separated by spaces."
                ),
                cases=(
                    SeedCase(
                        "3 3\n1 3 5\n2 4 6\n",
                        "1 2 3 4 5 6\n",
                        False,
                    ),
                    SeedCase("0 3\n\n1 2 3\n", "1 2 3\n", False),
                    SeedCase(
                        "4 2\n-5 -1 0 8\n-3 7\n",
                        "-5 -3 -1 0 7 8\n",
                        True,
                    ),
                    SeedCase(
                        "3 4\n1 1 2\n1 2 2 3\n",
                        "1 1 1 2 2 2 3\n",
                        True,
                    ),
                ),
            ),
        ),
    ),
    SeedTest(
        title="Interview Challenge Pack",
        description="Tackle classic interview problems with careful edge cases.",
        duration=75,
        questions=(
            SeedQuestion(
                title="Valid Parentheses",
                description=(
                    "Read a string containing only brackets (), {}, and []. "
                    "Print true when every bracket is correctly matched and nested."
                ),
                cases=(
                    SeedCase("()[]{}\n", "true\n", False),
                    SeedCase("(]\n", "false\n", False),
                    SeedCase("{[()]}\n", "true\n", True),
                    SeedCase("([)]\n", "false\n", True),
                ),
            ),
            SeedQuestion(
                title="Longest Unique Substring",
                description=(
                    "Read a string and print the length of its longest substring "
                    "that contains no repeated characters."
                ),
                cases=(
                    SeedCase("abcabcbb\n", "3\n", False),
                    SeedCase("bbbbb\n", "1\n", False),
                    SeedCase("pwwkew\n", "3\n", True),
                    SeedCase("dvdf\n", "3\n", True),
                ),
            ),
            SeedQuestion(
                title="Product Except Self",
                description=(
                    "Given n integers, print an array where each value is the "
                    "product of every input value except the one at that index. "
                    "Do not use division. Input: n, then the array."
                ),
                cases=(
                    SeedCase("4\n1 2 3 4\n", "24 12 8 6\n", False),
                    SeedCase("5\n-1 1 0 -3 3\n", "0 0 9 0 0\n", False),
                    SeedCase("3\n2 3 4\n", "12 8 6\n", True),
                    SeedCase("4\n0 0 2 3\n", "0 0 0 0\n", True),
                ),
            ),
        ),
    ),
)


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

        for test_seed in DEMO_TESTS:
            test = await db.scalar(
                select(Test).where(Test.title == test_seed.title)
            )
            if test is None:
                test = Test(
                    title=test_seed.title,
                    description=test_seed.description,
                    duration=test_seed.duration,
                    created_by=admin.id,
                )
                db.add(test)
                await db.flush()
                created["tests"] += 1
            else:
                test.description = test_seed.description
                test.duration = test_seed.duration
                test.created_by = admin.id

            for question_seed in test_seed.questions:
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
                        test_id=test.id,
                    )
                    db.add(question)
                    await db.flush()
                    created["questions"] += 1
                else:
                    question.description = question_seed.description

                existing_cases = (
                    await db.execute(
                        select(TestCase).where(
                            TestCase.question_id == question.id
                        )
                    )
                ).scalars().all()
                existing_keys = {
                    (
                        case.input_data,
                        case.output_data,
                        case.is_hidden,
                    )
                    for case in existing_cases
                }

                for case_seed in question_seed.cases:
                    key = (
                        case_seed.input_data,
                        case_seed.output_data,
                        case_seed.is_hidden,
                    )
                    if key in existing_keys:
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
