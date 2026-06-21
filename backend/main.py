import asyncio
import math
import os
from contextlib import asynccontextmanager, suppress

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from .auth import (
    COOKIE_NAME,
    COOKIE_SAMESITE,
    COOKIE_SECURE,
    get_current_user,
    hash_password,
    require_admin,
    set_session_cookies,
    verify_password,
)
from .database import engine, get_db
from .contest_service import (
    attempt_status,
    calculate_attempt_score,
    get_user_attempt,
    require_question_access,
    resolve_submission_attempt,
    start_attempt,
    sync_attempt,
    utc_now,
)
from .model import (
    Attempt,
    Base,
    Question,
    Submission,
    SubmissionKind,
    SubmissionStatus,
    Test,
    TestCase,
    User,
    UserRole,
)
from .pub_sub import listen_for_updates
from .redis_client import redis
from .seed import seed_demo_data
from .schema import (
    QuestionCreate,
    AttemptResponse,
    QuestionResponse,
    SubmissionCreate,
    SubmissionHistoryItem,
    SubmissionHistoryResponse,
    SubmissionResponse,
    TestCaseCreate,
    TestCaseResponse,
    TestCreate,
    TestResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    TestWithQuestionsResponse,
    QuestionDetailResponse,
)

from .websocket import router as websocket_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    if os.getenv("AUTO_SEED_DEMO_DATA", "false").lower() == "true":
        await seed_demo_data()

    # Keep Redis pub/sub connected while the API is up so websocket clients get judge updates.
    updates_task = asyncio.create_task(listen_for_updates())
    try:
        yield
    finally:
        updates_task.cancel()
        with suppress(asyncio.CancelledError):
            await updates_task
        await redis.aclose()


app = FastAPI(lifespan=lifespan)

cors_origins = [
    origin.strip().rstrip("/")
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(websocket_router)


def attempt_response(attempt: Attempt) -> AttemptResponse:
    return AttemptResponse(
        id=attempt.id,
        test_id=attempt.test_id,
        user_id=attempt.user_id,
        score=attempt.score,
        solved_count=attempt.score,
        status=attempt_status(attempt),
        started_at=attempt.started_at,
        expires_at=attempt.expires_at,
        submitted_at=attempt.submitted_at,
        server_time=utc_now(),
    )


def question_response(question: Question) -> QuestionResponse:
    return QuestionResponse.model_validate(question)


async def test_response(
    db: AsyncSession,
    test: Test,
    user: User | None,
    *,
    include_questions: bool,
):
    questions = list(test.questions)
    attempt = None
    access_state = "preview"

    if user is not None and user.role == UserRole.USER:
        attempt = await get_user_attempt(
            db,
            user_id=user.id,
            test_id=test.id,
        )
        state = attempt_status(attempt)
        access_state = "locked" if state == "not_started" else (
            "timed" if state == "active" else "practice"
        )
    elif user is not None and user.role == UserRole.ADMIN:
        access_state = "admin"

    visible_questions = questions
    if (
        include_questions
        and user is not None
        and user.role == UserRole.USER
        and access_state == "locked"
    ):
        visible_questions = []

    values = {
        "id": test.id,
        "title": test.title,
        "description": test.description,
        "duration": test.duration,
        "created_by": test.created_by,
        "question_count": len(questions),
        "attempt": attempt_response(attempt) if attempt else None,
        "access_state": access_state,
    }
    if include_questions:
        return TestWithQuestionsResponse(
            **values,
            questions=[question_response(question) for question in visible_questions],
        )
    return TestResponse(**values)


@app.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == data.username))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    user = User(
        name=data.name,
        username=data.username,
        password=hash_password(data.password),
        role=data.role,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


@app.post("/signin", response_model=UserResponse)
async def user_signin(data: UserLogin, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == data.username))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="Wrong credentials")

    password_valid, upgraded_hash = verify_password(
        data.password,
        user.password,
    )
    if not password_valid:
        raise HTTPException(status_code=401, detail="Wrong credentials")

    if data.role is not None and user.role != data.role:
        actual_role = "an administrator" if user.role == UserRole.ADMIN else "a user"
        raise HTTPException(
            status_code=403,
            detail=f"This account is registered as {actual_role}. Choose the correct login type.",
        )

    if upgraded_hash:
        user.password = upgraded_hash
        await db.commit()

    set_session_cookies(user.id, response)
    return user


@app.post("/create-test", response_model=TestResponse, status_code=status.HTTP_201_CREATED)
async def create_test(
    data: TestCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    test = Test(
        title=data.title,
        description=data.description,
        duration=data.duration,
        created_by=user.id,
    )

    db.add(test)
    await db.commit()
    await db.refresh(test)

    return test


@app.post("/create-question", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def add_question(
    data: QuestionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    result = await db.execute(select(Test).where(Test.id == data.test_id))
    test = result.scalar_one_or_none()

    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    # Only the test creator can attach new questions to that test.
    if test.created_by != user.id:
        raise HTTPException(status_code=403, detail="You can add questions only to your own tests")

    question = Question(
        title=data.title,
        description=data.description,
        difficulty=data.difficulty,
        test_id=test.id,
    )

    db.add(question)
    await db.commit()
    await db.refresh(question)

    return question


@app.post("/add-testcase", response_model=TestCaseResponse, status_code=status.HTTP_201_CREATED)
async def create_test_case(
    data: TestCaseCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    result = await db.execute(
        select(Question, Test)
        .join(Test, Question.test_id == Test.id)
        .where(Question.id == data.question_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Question not found")

    question, test = row
    # The join loads the parent test so ownership can be checked before adding cases.
    if test.created_by != user.id:
        raise HTTPException(status_code=403, detail="You can add test cases only to your own questions")

    test_case = TestCase(
        input_data=data.input_data,
        output_data=data.output_data,
        is_hidden=data.is_hidden,
        question_id=question.id,
    )

    db.add(test_case)
    await db.commit()
    await db.refresh(test_case)

    return test_case

async def create_execution(
    data: SubmissionCreate,
    kind: SubmissionKind,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Administrators can view problems but cannot submit solutions",
        )

    question = await db.get(Question, data.question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    attempt = await resolve_submission_attempt(
        db,
        question=question,
        user=user,
    )

    test_case_count = await db.scalar(
        select(func.count(TestCase.id)).where(
            TestCase.question_id == question.id,
            *(
                (TestCase.is_hidden.is_(False),)
                if kind == SubmissionKind.RUN
                else ()
            ),
        )
    )
    if not test_case_count:
        detail = (
            "This problem has no public cases to run."
            if kind == SubmissionKind.RUN
            else "This problem has no test cases to judge."
        )
        raise HTTPException(status_code=422, detail=detail)

    submission = Submission(
        code=data.code,
        language=data.language,
        status=SubmissionStatus.PENDING,
        kind=kind,
        user_id=user.id,
        question_id=data.question_id,
        attempt_id=attempt.id if attempt else None,
    )

    db.add(submission)
    await db.commit()
    await db.refresh(submission)

    # Queue only after commit so the worker can load the persisted submission row.
    await redis.lpush("submission_queue", submission.id)

    return submission


@app.post("/submission", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def code_submission(
    data: SubmissionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await create_execution(data, SubmissionKind.SUBMIT, db, user)


@app.post("/executions/run", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def run_code(
    data: SubmissionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await create_execution(data, SubmissionKind.RUN, db, user)


@app.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return user


@app.post("/logout")
async def logout(response: Response):
    response.delete_cookie(
        key=COOKIE_NAME,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
    )
    return {"detail": "Logged out"}


@app.get("/tests", response_model=list[TestResponse])
async def list_tests(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Test)
        .options(selectinload(Test.questions))
        .order_by(Test.id)
    )
    tests = result.scalars().all()
    return [
        await test_response(db, test, user, include_questions=False)
        for test in tests
    ]


@app.get("/admin/tests", response_model=list[TestWithQuestionsResponse])
async def list_admin_tests(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Administrator access required",
        )

    result = await db.execute(
        select(Test)
        .options(selectinload(Test.questions))
        .where(Test.created_by == user.id)
        .order_by(Test.id.desc())
    )
    return [
        await test_response(db, test, user, include_questions=True)
        for test in result.scalars().all()
    ]


@app.get("/tests/{test_id}", response_model=TestWithQuestionsResponse)
async def get_test(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Test)
        .options(selectinload(Test.questions))
        .where(Test.id == test_id)
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    return await test_response(db, test, user, include_questions=True)


@app.post(
    "/tests/{test_id}/attempts/start",
    response_model=AttemptResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_test_attempt(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Administrators cannot start contest attempts.",
        )
    test = await db.get(Test, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Contest not found")
    attempt = await start_attempt(db, test=test, user=user)
    return attempt_response(attempt)


@app.get("/tests/{test_id}/attempt", response_model=AttemptResponse | None)
async def get_test_attempt(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role == UserRole.ADMIN:
        return None
    test = await db.get(Test, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Contest not found")
    attempt = await get_user_attempt(
        db,
        user_id=user.id,
        test_id=test_id,
    )
    return attempt_response(attempt) if attempt else None


@app.post("/attempts/{attempt_id}/finish", response_model=AttemptResponse)
async def finish_test_attempt(
    attempt_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    attempt = await db.get(Attempt, attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if attempt.user_id != user.id:
        raise HTTPException(status_code=403, detail="This attempt belongs to another user.")

    attempt = await sync_attempt(db, attempt)
    if attempt.submitted_at is None:
        attempt.submitted_at = utc_now()
        attempt.score = await calculate_attempt_score(db, attempt.id)
        await db.commit()
        await db.refresh(attempt)
    return attempt_response(attempt)


@app.get("/questions/{question_id}", response_model=QuestionDetailResponse)
async def get_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Question)
        .options(selectinload(Question.test_cases))
        .where(Question.id == question_id)
    )
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    attempt = await require_question_access(
        db,
        question=question,
        user=user,
    )
    test = await db.get(Test, question.test_id)
    state = attempt_status(attempt)
    access_state = "admin" if user.role == UserRole.ADMIN else (
        "timed" if state == "active" else "practice"
    )
    return QuestionDetailResponse(
        id=question.id,
        title=question.title,
        description=question.description,
        test_id=question.test_id,
        difficulty=question.difficulty,
        contest_title=test.title,
        contest_duration=test.duration,
        attempt=attempt_response(attempt) if attempt else None,
        access_state=access_state,
        test_cases=[
            TestCaseResponse.model_validate(test_case)
            for test_case in question.test_cases
            if not test_case.is_hidden
        ],
    )


@app.get("/submissions/{submission_id}", response_model=SubmissionResponse)
async def get_submission(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    submission = await db.get(Submission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    if submission.user_id != user.id:
        raise HTTPException(status_code=403, detail="This submission belongs to another user.")
    return submission


@app.get("/submissions", response_model=SubmissionHistoryResponse)
async def list_submissions(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if page < 1:
        raise HTTPException(status_code=422, detail="page must be at least 1")
    if page_size < 1 or page_size > 100:
        raise HTTPException(status_code=422, detail="page_size must be between 1 and 100")

    filters = (
        Submission.user_id == user.id,
        Submission.kind == SubmissionKind.SUBMIT,
    )
    total = int(
        await db.scalar(select(func.count(Submission.id)).where(*filters))
        or 0
    )
    result = await db.execute(
        select(Submission, Question, Test)
        .join(Question, Submission.question_id == Question.id)
        .join(Test, Question.test_id == Test.id)
        .where(*filters)
        .order_by(Submission.created_at.desc(), Submission.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = [
        SubmissionHistoryItem(
            id=submission.id,
            question_id=question.id,
            question_title=question.title,
            test_id=test.id,
            contest_title=test.title,
            language=submission.language,
            status=submission.status,
            mode="timed" if submission.attempt_id else "practice",
            created_at=submission.created_at,
        )
        for submission, question, test in result.all()
    ]
    return SubmissionHistoryResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=max(1, math.ceil(total / page_size)),
    )
