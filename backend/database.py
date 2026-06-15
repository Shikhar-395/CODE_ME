import os

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

DATABASE_URL= os.getenv("DATABASE_URL","hii")

engine= create_async_engine(DATABASE_URL)

SessionLocal= async_sessionmaker(
    autoflush= False,
    expire_on_commit=False,
    bind=engine
)

class Base(declarative_base):
    pass