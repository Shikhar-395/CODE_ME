import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException, WebSocketDisconnect
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.main import (
    code_submission,
    finish_test_attempt,
    get_question,
    get_submission,
    get_test,
    list_submissions,
    run_code,
    start_test_attempt,
)
from backend.auth import COOKIE_NAME, create_token
from backend.model import (
    Base,
    Attempt,
    Language,
    Question,
    SubmissionKind,
    Submission,
    SubmissionStatus,
    Test,
    TestCase,
    User,
    UserRole,
)
from backend.schema import SubmissionCreate
from backend.seed_catalog import CATALOG, validate_catalog
from backend.worker import judge
from backend.websocket import websocket_endpoint


class FakeWebSocket:
    def __init__(self, token: str):
        self.cookies = {COOKIE_NAME: token}
        self.accepted = False
        self.closed_code = None
        self.messages = []

    async def accept(self):
        self.accepted = True

    async def close(self, code: int, reason: str):
        self.closed_code = code

    async def send_json(self, payload):
        self.messages.append(payload)

    async def receive_text(self):
        raise WebSocketDisconnect()


class SessionContext:
    def __init__(self, db):
        self.db = db

    async def __aenter__(self):
        return self.db

    async def __aexit__(self, exc_type, exc, traceback):
        return False


class CatalogTests(unittest.TestCase):
    def test_catalog_shape_and_case_coverage(self):
        validate_catalog()
        questions = [
            question
            for contest in CATALOG
            for question in contest.questions
        ]

        self.assertEqual(len(CATALOG), 10)
        self.assertEqual(len(questions), 100)
        self.assertEqual(sum(len(question.cases) for question in questions), 500)
        self.assertTrue(
            all(
                sum(not case.is_hidden for case in question.cases) == 2
                and sum(case.is_hidden for case in question.cases) == 3
                for question in questions
            )
        )


class ContestFlowTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "contest.db"
        self.engine = create_async_engine(
            f"sqlite+aiosqlite:///{database_path}"
        )
        self.sessions = async_sessionmaker(
            self.engine,
            expire_on_commit=False,
        )
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with self.sessions() as db:
            self.admin = User(
                name="Admin",
                username="admin@example.com",
                password="password",
                role=UserRole.ADMIN,
            )
            self.user = User(
                name="User",
                username="user@example.com",
                password="password",
                role=UserRole.USER,
            )
            self.other_user = User(
                name="Other",
                username="other@example.com",
                password="password",
                role=UserRole.USER,
            )
            db.add_all([self.admin, self.user, self.other_user])
            await db.flush()
            self.test = Test(
                title="Timed Contest",
                description="A contest used by the flow tests.",
                duration=30,
                created_by=self.admin.id,
            )
            db.add(self.test)
            await db.flush()
            self.question = Question(
                title="Add values",
                description="Read two integers and print their sum.",
                test_id=self.test.id,
            )
            db.add(self.question)
            await db.flush()
            db.add_all(
                [
                    TestCase(
                        input_data="2 3\n",
                        output_data="5\n",
                        is_hidden=False,
                        question_id=self.question.id,
                    ),
                    TestCase(
                        input_data="4 7\n",
                        output_data="11\n",
                        is_hidden=True,
                        question_id=self.question.id,
                    ),
                ]
            )
            await db.commit()

    async def asyncTearDown(self):
        await self.engine.dispose()
        self.temp_dir.cleanup()

    async def test_problems_are_locked_until_start_then_resume(self):
        async with self.sessions() as db:
            locked = await get_test(self.test.id, db, self.user)
            self.assertEqual(locked.access_state, "locked")
            self.assertEqual(locked.questions, [])
            self.assertEqual(locked.question_count, 1)

            with self.assertRaises(HTTPException) as raised:
                await get_question(self.question.id, db, self.user)
            self.assertEqual(raised.exception.status_code, 403)

            first = await start_test_attempt(self.test.id, db, self.user)
            second = await start_test_attempt(self.test.id, db, self.user)
            unlocked = await get_test(self.test.id, db, self.user)

        self.assertEqual(first.id, second.id)
        self.assertEqual(first.status, "active")
        self.assertEqual(unlocked.access_state, "timed")
        self.assertEqual(len(unlocked.questions), 1)

    async def test_expired_attempt_unlocks_practice_and_rejects_timed_link(self):
        async with self.sessions() as db:
            response = await start_test_attempt(self.test.id, db, self.user)
            attempt = await db.get(Attempt, response.id)
            attempt.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
            await db.commit()

            contest = await get_test(self.test.id, db, self.user)
            practice_question = await get_question(self.question.id, db, self.user)
            with patch("backend.main.redis.lpush", new=AsyncMock()):
                submission = await code_submission(
                    SubmissionCreate(
                        question_id=self.question.id,
                        code="print(5)",
                        language=Language.PYTHON,
                    ),
                    db,
                    self.user,
                )

        self.assertEqual(contest.access_state, "practice")
        self.assertEqual(contest.attempt.status, "expired")
        self.assertEqual(practice_question.access_state, "practice")
        self.assertIsNone(submission.attempt_id)

    async def test_finish_is_idempotent_and_preserves_single_score(self):
        async with self.sessions() as db:
            response = await start_test_attempt(self.test.id, db, self.user)
            first = await finish_test_attempt(response.id, db, self.user)
            second = await finish_test_attempt(response.id, db, self.user)

        self.assertEqual(first.status, "completed")
        self.assertEqual(first.submitted_at, second.submitted_at)

    async def test_run_uses_public_cases_submit_uses_all_cases_and_history_hides_runs(self):
        payload = SubmissionCreate(
            question_id=self.question.id,
            code="print(5)",
            language=Language.PYTHON,
        )
        async with self.sessions() as db:
            await start_test_attempt(self.test.id, db, self.user)
            with patch("backend.main.redis.lpush", new=AsyncMock()):
                run_submission = await run_code(payload, db, self.user)
                full_submission = await code_submission(payload, db, self.user)

            seen_case_counts: list[int] = []

            async def accepted(_submission, test_cases):
                seen_case_counts.append(len(test_cases))
                return {"status": SubmissionStatus.ACCEPTED}

            with (
                patch("backend.worker.mini_machine", new=accepted),
                patch("backend.worker.redis.publish", new=AsyncMock()),
            ):
                await judge(run_submission.id, db)
                await judge(full_submission.id, db)

            history = await list_submissions(1, 20, db, self.user)

        self.assertEqual(run_submission.kind, SubmissionKind.RUN)
        self.assertEqual(full_submission.kind, SubmissionKind.SUBMIT)
        self.assertEqual(seen_case_counts, [1, 2])
        self.assertEqual(history.total, 1)
        self.assertEqual(history.items[0].id, full_submission.id)

    async def test_submission_reads_are_scoped_to_owner(self):
        async with self.sessions() as db:
            await start_test_attempt(self.test.id, db, self.user)
            with patch("backend.main.redis.lpush", new=AsyncMock()):
                submission = await code_submission(
                    SubmissionCreate(
                        question_id=self.question.id,
                        code="print(5)",
                        language=Language.PYTHON,
                    ),
                    db,
                    self.user,
                )

            owned = await get_submission(submission.id, db, self.user)
            with self.assertRaises(HTTPException) as raised:
                await get_submission(submission.id, db, self.other_user)

        self.assertEqual(owned.id, submission.id)
        self.assertEqual(raised.exception.status_code, 403)

    async def test_websocket_requires_submission_ownership_and_sends_current_status(self):
        async with self.sessions() as db:
            submission = Submission(
                code="print(5)",
                language=Language.PYTHON,
                status=SubmissionStatus.RUNNING,
                kind=SubmissionKind.SUBMIT,
                user_id=self.user.id,
                question_id=self.question.id,
            )
            db.add(submission)
            await db.commit()

            owner_socket = FakeWebSocket(create_token(self.user.id))
            other_socket = FakeWebSocket(create_token(self.other_user.id))
            with patch(
                "backend.websocket.SessionLocal",
                side_effect=lambda: SessionContext(db),
            ):
                await websocket_endpoint(owner_socket, submission.id)
                await websocket_endpoint(other_socket, submission.id)

        self.assertTrue(owner_socket.accepted)
        self.assertEqual(
            owner_socket.messages,
            [{"submission_id": submission.id, "status": "running"}],
        )
        self.assertEqual(other_socket.closed_code, 4403)
