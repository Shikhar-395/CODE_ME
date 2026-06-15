from pydantic import BaseModel, Field, ConfigDict
from model import UserRole, Language, SubmissionStatus

class User_Schema(BaseModel):
    name:str= Field(min_length=3, max_length=10)
    username:str= Field(min_length=4, max_length=20)
    password:str= Field(min_length=4, max_length=20)
    role:UserRole= UserRole.USER

class User_Responce(BaseModel):
    model_config= ConfigDict(from_attributes=True)

    id:int
    username:str
    role:str

class TestCreate(BaseModel):
    title:str= Field(min_length=5, max_length=50)
    discription:str= Field(min_length=5, max_length=100)
    duration:int

class TestResponce(BaseModel):
    model_config= ConfigDict(from_attributes=True)

    id:int
    tittle:str
    description:str
    duration:int
    created_by:int

class Question_Create(BaseModel):
    title:str= Field(min_length=4, max_length=50)
    discription:str= Field(min_length=4, max_length=100)

class Question_Responce(BaseModel):
    model_config= ConfigDict(from_attributes=True)

    id:int
    title:str
    description:str
    test_id:int

class TestCaseCreate(BaseModel):
    input_data:str= Field(min_length=1, max_length=50)
    output_data:str= Field(min_length=1, max_length=50)
    is_hidden:bool= True

class TestCaseResponce(BaseModel):
    model_config= ConfigDict(from_attributes=True)

    id:int
    input_data:str
    output_data:str
    is_hidden:bool
    question_id:int

class AttemptResponce(BaseModel):
    model_config=ConfigDict(from_attributes=True)

    id:int
    test_id:int
    user_id:int
    score:int

class SubmissionCreate(BaseModel):
    code:str
    language:str

class SubmissionResponce(BaseModel):
    model_config=ConfigDict(from_attributes=True)

    id:int
    code:str
    language:str
    status:SubmissionStatus
    user_id:int
    question_id:int