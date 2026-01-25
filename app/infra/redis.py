import redis.asyncio as redis

from app.settings import settings

redis_client = redis.from_url(settings.redis_url, decode_responses=True)


async def ping_redis() -> bool:
    try:
        return bool(await redis_client.ping())
    except Exception:
        return False
