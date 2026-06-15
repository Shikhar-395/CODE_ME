from pydantic import BaseModel, Field, ConfigDict

class User_Schema(BaseModel):
    name:str= Field(min_length=3, max_length=10)
    username:str= Field(min_length=4, max_length=20)
    password:str= Field(min_length=4, max_length=20)
    role:str= Field(min_length=1, max_length=10)

class User_Responce(BaseModel):
    model_config= ConfigDict(from_attributes=True)

    id:int
    username:str
    password:str
    role:str

class 
    