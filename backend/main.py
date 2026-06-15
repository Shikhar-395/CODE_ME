from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from redis_client import redis
from .auth import get_current_user, set_session_cookies
from .database import engine, get_db
from .model import Base, Question, Test, TestCase, User, Submission, SubmissionStatus
from .schema import (
    QuestionCreate,
    QuestionResponse,
    TestCaseCreate,
    TestCaseResponse,
    TestCreate,
    TestResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    SubmissionResponce,
    SubmissionCreate
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == data.username))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    user = User(
        name=data.name,
        username=data.username,
        password=data.password,
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

    if not user or user.password != data.password:
        raise HTTPException(status_code=401, detail="Wrong credentials")

    set_session_cookies(user.id, response)
    return user


@app.post("/create-test", response_model=TestResponse, status_code=status.HTTP_201_CREATED)
async def create_test(
    data: TestCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
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
    user: User = Depends(get_current_user),
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
    user: User = Depends(get_current_user),
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

@app.post("/submission", response_model=SubmissionResponce)
async def code_submission(data:SubmissionCreate, question_id:int, db:AsyncSession= Depends(get_db), user_id:User= Depends(get_current_user)):
    question= await db.get(Question, question_id)
    if not question:
        raise HTTPException(
            status_code=404
        )

    submission= Submission(
        code= data.code,
        language= data.language,
        status= SubmissionStatus.PENDING,
        question_id= question_id
    )

    db.add(submission)
    await db.commit()
    await db.refresh(submission)

    await redis.lpush("submission_queue", submission.id)

    return {
        "submission_id": submission.id,
        "status": submission.status
    }