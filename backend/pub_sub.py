import json
from ws_manager import manager
from redis_client import redis

async def listen_for_updates():

    pubsub= redis.pubsub()

    await pubsub.subscribe("subscription update")

    async for message in pubsub.listen():
        if message["type"] != "message" :
            continue

        payload= json.load(message["data"])
        submission_id= payload["submission_id"]

        await manager.send(
            submission_id,
            payload
        )
