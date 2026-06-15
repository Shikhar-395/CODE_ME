from pydantic import BaseModel, Field, ConfigDict

from .model import UserRole, Language, SubmissionStatus


class UserCreate(BaseModel):
    name: str = Field(min_length=3, max_length=30)
    username: str = Field(min_length=4, max_length=20)
    password: str = Field(min_length=4, max_length=72)
    role: UserRole = UserRole.USER


class UserLogin(BaseModel):
    username: str = Field(min_length=4, max_length=20)
    password: str = Field(min_length=4, max_length=72)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: UserRole


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


class QuestionCreate(BaseModel):
    test_id: int
    title: str = Field(min_length=4, max_length=50)
    description: str = Field(min_length=4, max_length=100)


class QuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    test_id: int


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


class AttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    test_id: int
    user_id: int
    score: int


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
    user_id: int
    question_id: int


# Backwards-compatible aliases for the earlier misspelled class names.
User_Schema = UserCreate
User_Responce = UserResponse
TestResponce = TestResponse
Question_Create = QuestionCreate
Question_Responce = QuestionResponse
TestCaseResponce = TestCaseResponse
AttemptResponce = AttemptResponse
SubmissionResponce = SubmissionResponse
