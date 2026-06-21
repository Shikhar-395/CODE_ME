from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from .model import (
    Difficulty,
    Language,
    SubmissionKind,
    SubmissionStatus,
    UserRole,
)


class UserCreate(BaseModel):
    name: str = Field(min_length=3, max_length=30)
    username: str = Field(min_length=4, max_length=20)
    password: str = Field(min_length=4, max_length=72)
    role: UserRole = UserRole.USER


class UserLogin(BaseModel):
    username: str = Field(min_length=4, max_length=20)
    password: str = Field(min_length=4, max_length=72)
    role: UserRole | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: UserRole


class AttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    test_id: int
    user_id: int
    score: int
    solved_count: int
    status: str
    started_at: datetime
    expires_at: datetime
    submitted_at: datetime | None
    server_time: datetime


class TestCreate(BaseModel):
    title: str = Field(min_length=5, max_length=50)
    description: str = Field(min_length=5, max_length=100)
    duration: int = Field(gt=0)


class TestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    duration: int
    created_by: int
    question_count: int = 0
    attempt: AttemptResponse | None = None
    access_state: str = "preview"


class QuestionCreate(BaseModel):
    test_id: int
    title: str = Field(min_length=4, max_length=50)
    description: str = Field(min_length=4, max_length=4000)
    difficulty: Difficulty = Difficulty.EASY


class QuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    test_id: int
    difficulty: Difficulty


class TestCaseCreate(BaseModel):
    question_id: int
    input_data: str = Field(min_length=1, max_length=500)
    output_data: str = Field(min_length=1, max_length=500)
    is_hidden: bool = True


class TestCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    input_data: str
    output_data: str
    is_hidden: bool
    question_id: int


class SubmissionCreate(BaseModel):
    question_id: int
    code: str = Field(min_length=1)
    language: Language


class SubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    language: Language
    status: SubmissionStatus
    kind: SubmissionKind
    user_id: int
    question_id: int
    attempt_id: int | None
    created_at: datetime


class SubmissionHistoryItem(BaseModel):
    id: int
    question_id: int
    question_title: str
    test_id: int
    contest_title: str
    language: Language
    status: SubmissionStatus
    mode: str
    created_at: datetime


class SubmissionHistoryResponse(BaseModel):
    items: list[SubmissionHistoryItem]
    page: int
    page_size: int
    total: int
    total_pages: int


class TestWithQuestionsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    duration: int
    created_by: int
    questions: list[QuestionResponse] = []
    question_count: int = 0
    attempt: AttemptResponse | None = None
    access_state: str = "preview"


class QuestionDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    test_id: int
    difficulty: Difficulty
    contest_title: str
    contest_duration: int
    attempt: AttemptResponse | None = None
    access_state: str
    test_cases: list[TestCaseResponse] = []


# Backwards-compatible aliases for the earlier misspelled class names.
User_Schema = UserCreate
User_Responce = UserResponse
TestResponce = TestResponse
Question_Create = QuestionCreate
Question_Responce = QuestionResponse
TestCaseResponce = TestCaseResponse
AttemptResponce = AttemptResponse
SubmissionResponce = SubmissionResponse
