import asyncio
import os
from contextlib import asynccontextmanager, suppress

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
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
from .model import (
    Base,
    Question,
    Submission,
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
    QuestionResponse,
    SubmissionCreate,
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
        role=UserRole.USER,
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

@app.post("/submission", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def code_submission(
    data: SubmissionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    question= await db.get(Question, data.question_id)
    if not question:
        raise HTTPException(
            status_code=404
        )

    # Attach the authenticated user before flushing because submissions.user_id is required.
    submission= Submission(
        code= data.code,
        language= data.language,
        status= SubmissionStatus.PENDING,
        user_id=user.id,
        question_id= data.question_id
    )

    db.add(submission)
    await db.commit()
    await db.refresh(submission)

    # Queue only after commit so the worker can load the persisted submission row.
    await redis.lpush("submission_queue", submission.id)

    return submission


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
async def list_tests(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Test))
    tests = result.scalars().all()
    return tests


@app.get("/tests/{test_id}", response_model=TestWithQuestionsResponse)
async def get_test(test_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Test)
        .options(selectinload(Test.questions))
        .where(Test.id == test_id)
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    return test


@app.get("/questions/{question_id}", response_model=QuestionDetailResponse)
async def get_question(question_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Question)
        .options(selectinload(Question.test_cases))
        .where(Question.id == question_id)
    )
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return QuestionDetailResponse(
        id=question.id,
        title=question.title,
        description=question.description,
        test_id=question.test_id,
        test_cases=[
            TestCaseResponse.model_validate(test_case)
            for test_case in question.test_cases
            if not test_case.is_hidden
        ],
    )


@app.get("/submissions/{submission_id}", response_model=SubmissionResponse)
async def get_submission(submission_id: int, db: AsyncSession = Depends(get_db)):
    submission = await db.get(Submission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission
