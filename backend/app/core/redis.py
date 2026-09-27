import json
import redis.asyncio as aioredis
from app.core.config import settings

redis_client = None

async def get_redis_client():
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    return redis_client
