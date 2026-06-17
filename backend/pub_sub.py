import asyncio
import json

from redis.exceptions import RedisError

from .redis_client import redis
from .ws_manager import manager

async def listen_for_updates():
    pubsub = None

    while True:
        try:
            pubsub= redis.pubsub()

            # Match the channel used by worker.py when judge results are published.
            await pubsub.subscribe("submission_updates")

            async for message in pubsub.listen():
                if message["type"] != "message" :
                    continue

                payload= json.loads(message["data"])
                submission_id= payload["submission_id"]

                await manager.send(
                    submission_id,
                    payload
                )
        except asyncio.CancelledError:
            raise
        except RedisError:
            # Retry until Redis is ready; this keeps API startup from depending on Redis timing.
            await asyncio.sleep(1)
        finally:
            if pubsub is not None:
                await pubsub.aclose()
