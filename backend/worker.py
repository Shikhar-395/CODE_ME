import json
from redis_client import redis
from fastapi import Depends
from sqlalchemy import select
from vm import mini_machine
from .model import Base, Question, Test, TestCase, User, Submission, SubmissionStatus
from sqlalchemy.ext.asyncio import AsyncSession

async def judge(submission_id:int, db: AsyncSession):
    submission_id= submission_id
    submission= await db.execute(select(Submission).where(Submission.id == submission_id))
    result= submission.scalar_one_or_none()
    code= result.code
    language= result.language
    user_id= result.user_id
    quesiton_id= result.question_id
    test_case_result= await db.execute(select(TestCase).where(TestCase.question_id == quesiton_id))
    test_case= test_case_result.scalars().all()


    result= mini_machine(user_id,quesiton_id,test_case,code,language)
    return result

async def worker():
    while True:

        job= redis.brpop("submission_queue")
        submission_id= int(job[1])
        result= judge(submission_id)

        await redis.publish(
            "submission_updates",
            json.dump({
                "submission_id": submission_id,
                "status": result["status"]
            })
        )