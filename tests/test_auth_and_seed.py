import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.auth import hash_password, require_admin, verify_password
from backend.main import (
    code_submission,
    create_user,
    get_question,
    list_admin_tests,
    user_signin,
)
from backend.model import Base, Language, Question, Test, TestCase, User, UserRole
from backend.schema import SubmissionCreate, UserCreate, UserLogin
from backend.seed import seed_demo_data


class PasswordTests(unittest.TestCase):
    def test_argon2_hash_round_trip(self):
        hashed = hash_password("correct horse")

        valid, replacement = verify_password("correct horse", hashed)

        self.assertTrue(valid)
        self.assertIsNone(replacement)
        self.assertNotEqual(hashed, "correct horse")

    def test_plaintext_password_is_upgraded(self):
        valid, replacement = verify_password("4444", "4444")

        self.assertTrue(valid)
        self.assertIsNotNone(replacement)
        self.assertTrue(replacement.startswith("$argon2"))


class DatabaseBehaviorTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "test.db"
        self.engine = create_async_engine(
            f"sqlite+aiosqlite:///{database_path}"
        )
        self.sessions = async_sessionmaker(
            self.engine,
            expire_on_commit=False,
        )
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def asyncTearDown(self):
        await self.engine.dispose()
        self.temp_dir.cleanup()

    async def test_signup_creates_selected_admin_role(self):
        payload = UserCreate.model_validate(
            {
                "name": "Demo User",
                "username": "demo@example.com",
                "password": "safe-password",
                "role": "admin",
            }
        )

        async with self.sessions() as db:
            user = await create_user(payload, db)
            stored = await db.get(User, user.id)

        self.assertEqual(stored.role, UserRole.ADMIN)
        self.assertTrue(stored.password.startswith("$argon2"))

    async def test_signup_defaults_to_regular_user(self):
        payload = UserCreate(
            name="Regular User",
            username="regular@example.com",
            password="safe-password",
        )

        async with self.sessions() as db:
            user = await create_user(payload, db)
            stored = await db.get(User, user.id)

        self.assertEqual(stored.role, UserRole.USER)

    async def test_legacy_login_upgrades_plaintext_password(self):
        async with self.sessions() as db:
            user = User(
                name="Legacy",
                username="legacy@example.com",
                password="4444",
                role=UserRole.USER,
            )
            db.add(user)
            await db.commit()

            await user_signin(
                UserLogin(username="legacy@example.com", password="4444"),
                Response(),
                db,
            )
            await db.refresh(user)

        self.assertTrue(user.password.startswith("$argon2"))

    async def test_admin_login_returns_admin_role(self):
        async with self.sessions() as db:
            admin = User(
                name="Admin",
                username="admin@example.com",
                password=hash_password("password"),
                role=UserRole.ADMIN,
            )
            db.add(admin)
            await db.commit()

            signed_in = await user_signin(
                UserLogin(
                    username="admin@example.com",
                    password="password",
                    role=UserRole.ADMIN,
                ),
                Response(),
                db,
            )

        self.assertEqual(signed_in.role, UserRole.ADMIN)

    async def test_login_rejects_wrong_role_selection(self):
        async with self.sessions() as db:
            user = User(
                name="Regular",
                username="regular@example.com",
                password=hash_password("password"),
                role=UserRole.USER,
            )
            db.add(user)
            await db.commit()

            with self.assertRaises(HTTPException) as raised:
                await user_signin(
                    UserLogin(
                        username="regular@example.com",
                        password="password",
                        role=UserRole.ADMIN,
                    ),
                    Response(),
                    db,
                )

        self.assertEqual(raised.exception.status_code, 403)
        self.assertIn("registered as a user", raised.exception.detail)

    async def test_non_admin_is_rejected(self):
        user = User(
            name="Regular",
            username="regular@example.com",
            password=hash_password("password"),
            role=UserRole.USER,
        )

        with self.assertRaises(HTTPException) as raised:
            await require_admin(user)

        self.assertEqual(raised.exception.status_code, 403)

    async def test_admin_tests_are_scoped_to_the_creator(self):
        async with self.sessions() as db:
            first_admin = User(
                name="First Admin",
                username="first-admin@example.com",
                password=hash_password("password"),
                role=UserRole.ADMIN,
            )
            second_admin = User(
                name="Second Admin",
                username="second-admin@example.com",
                password=hash_password("password"),
                role=UserRole.ADMIN,
            )
            db.add_all([first_admin, second_admin])
            await db.flush()

            first_test = Test(
                title="First Admin Contest",
                description="Owned by the first administrator.",
                duration=30,
                created_by=first_admin.id,
            )
            second_test = Test(
                title="Second Admin Contest",
                description="Owned by the second administrator.",
                duration=45,
                created_by=second_admin.id,
            )
            db.add_all([first_test, second_test])
            await db.flush()
            db.add_all(
                [
                    Question(
                        title="First problem",
                        description="Only the first admin should receive this.",
                        test_id=first_test.id,
                    ),
                    Question(
                        title="Second problem",
                        description="Only the second admin should receive this.",
                        test_id=second_test.id,
                    ),
                ]
            )
            await db.commit()

            first_results = await list_admin_tests(db, first_admin)
            second_results = await list_admin_tests(db, second_admin)

        self.assertEqual([test.title for test in first_results], ["First Admin Contest"])
        self.assertEqual(
            [question.title for question in first_results[0].questions],
            ["First problem"],
        )
        self.assertEqual([test.title for test in second_results], ["Second Admin Contest"])
        self.assertEqual(
            [question.title for question in second_results[0].questions],
            ["Second problem"],
        )

    async def test_regular_user_cannot_list_admin_tests(self):
        regular_user = User(
            name="Regular",
            username="regular@example.com",
            password=hash_password("password"),
            role=UserRole.USER,
        )

        async with self.sessions() as db:
            with self.assertRaises(HTTPException) as raised:
                await list_admin_tests(db, regular_user)

        self.assertEqual(raised.exception.status_code, 403)

    async def test_admin_cannot_submit_but_regular_user_can(self):
        async with self.sessions() as db:
            admin = User(
                name="Admin",
                username="admin@example.com",
                password=hash_password("password"),
                role=UserRole.ADMIN,
            )
            regular_user = User(
                name="Regular",
                username="regular@example.com",
                password=hash_password("password"),
                role=UserRole.USER,
            )
            db.add_all([admin, regular_user])
            await db.flush()
            test = Test(
                title="Submission Test",
                description="Submission permission coverage.",
                duration=30,
                created_by=admin.id,
            )
            db.add(test)
            await db.flush()
            question = Question(
                title="Submit safely",
                description="Regular users can submit this problem.",
                test_id=test.id,
            )
            db.add(question)
            await db.commit()

            payload = SubmissionCreate(
                question_id=question.id,
                code="print('ok')",
                language=Language.PYTHON,
            )

            with self.assertRaises(HTTPException) as raised:
                await code_submission(payload, db, admin)

            with patch("backend.main.redis.lpush", new=AsyncMock()) as enqueue:
                submission = await code_submission(payload, db, regular_user)

        self.assertEqual(raised.exception.status_code, 403)
        self.assertEqual(submission.user_id, regular_user.id)
        enqueue.assert_awaited_once_with("submission_queue", submission.id)

    async def test_public_question_hides_hidden_cases(self):
        async with self.sessions() as db:
            admin = User(
                name="Admin",
                username="admin@example.com",
                password=hash_password("password"),
                role=UserRole.ADMIN,
            )
            db.add(admin)
            await db.flush()
            test = Test(
                title="Visibility Test",
                description="Visibility test",
                duration=30,
                created_by=admin.id,
            )
            db.add(test)
            await db.flush()
            question = Question(
                title="Hidden cases",
                description="Only examples should be public.",
                test_id=test.id,
            )
            db.add(question)
            await db.flush()
            db.add_all(
                [
                    TestCase(
                        input_data="visible",
                        output_data="visible",
                        is_hidden=False,
                        question_id=question.id,
                    ),
                    TestCase(
                        input_data="secret",
                        output_data="secret",
                        is_hidden=True,
                        question_id=question.id,
                    ),
                ]
            )
            await db.commit()

            response = await get_question(question.id, db)

        self.assertEqual(len(response.test_cases), 1)
        self.assertEqual(response.test_cases[0].input_data, "visible")

    async def test_seed_is_idempotent(self):
        environment = {
            "SEED_ADMIN_NAME": "Singh",
            "SEED_ADMIN_USERNAME": "singh@gmail.com",
            "SEED_ADMIN_PASSWORD": "4444",
        }
        with patch.dict("os.environ", environment, clear=False):
            first = await seed_demo_data(self.sessions)
            second = await seed_demo_data(self.sessions)

        async with self.sessions() as db:
            user_count = await db.scalar(select(func.count(User.id)))
            test_count = await db.scalar(select(func.count(Test.id)))
            question_count = await db.scalar(select(func.count(Question.id)))
            case_count = await db.scalar(select(func.count(TestCase.id)))
            admin = await db.scalar(
                select(User).where(User.username == "singh@gmail.com")
            )

        self.assertEqual(first, {
            "users": 1,
            "tests": 3,
            "questions": 9,
            "test_cases": 36,
        })
        self.assertEqual(second, {
            "users": 0,
            "tests": 0,
            "questions": 0,
            "test_cases": 0,
        })
        self.assertEqual((user_count, test_count, question_count, case_count), (1, 3, 9, 36))
        self.assertEqual(admin.role, UserRole.ADMIN)
        self.assertTrue(verify_password("4444", admin.password)[0])


if __name__ == "__main__":
    unittest.main()
