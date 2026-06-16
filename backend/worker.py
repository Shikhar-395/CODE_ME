import json
from redis_client import redis

async def fake_judge(submission_id:int):
    return {
        "status": "accepted"
    }

async def worker():
    while True:

        job= redis.brpop("submission_queue")
        submission_id= int(job[1])
        result= fake_judge(submission_id)

        await redis.publish(
            "submission_updates",
            json.dump({
                "submission_id": submission_id,
                "status": result["status"]
            })
        )