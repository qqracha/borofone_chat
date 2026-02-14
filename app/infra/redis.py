"""
Redis configuration with async client and FastAPI dependency.

Includes:
- Async Redis client
- Connection pooling
- Dependency for FastAPI
- Graceful fallback если Redis недоступен
"""
from typing import AsyncGenerator

from redis.asyncio import Redis, ConnectionPool
from redis.exceptions import RedisError

from app.settings import settings

# ==========================================
# CONNECTION POOL
# ==========================================

pool = ConnectionPool.from_url(
    settings.redis_url,
    decode_responses=True,  # Автоматически декодировать bytes → str
    max_connections=10,
    socket_connect_timeout=5,
    socket_timeout=5,
)

# ==========================================
# GLOBAL CLIENT (для использования вне FastAPI)
# ==========================================

redis_client: Redis | None = None

try:
    redis_client = Redis(connection_pool=pool)
except Exception as e:
    print(f"⚠️ Warning: Could not create Redis client: {e}")
    redis_client = None

# ==========================================
# DEPENDENCY
# ==========================================

async def get_redis() -> AsyncGenerator[Redis | None, None]:
    """
    FastAPI dependency для получения Redis client.

    Возвращает None если Redis недоступен (graceful degradation).

    Usage:
        @router.post("/messages")
        async def create_message(redis: Redis = Depends(get_redis)):
            if redis:
                await redis.set("key", "value")
    """
    if redis_client is None:
        yield None
        return

    try:
        # Проверяем соединение
        await redis_client.ping()
        yield redis_client
    except RedisError as e:
        print(f"⚠️ Redis unavailable: {e}")
        yield None


async def get_redis_required() -> AsyncGenerator[Redis, None]:
    """
    FastAPI dependency для Redis (требует доступности).

    Выбрасывает HTTPException если Redis недоступен.

    Usage:
        @router.post("/messages")
        async def create_message(redis: Redis = Depends(get_redis_required)):
            await redis.set("key", "value")  # Redis гарантированно доступен
    """
    from fastapi import HTTPException, status

    if redis_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis service unavailable"
        )

    try:
        await redis_client.ping()
        yield redis_client
    except RedisError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis connection failed: {str(e)}"
        )


# ==========================================
# HELPER FUNCTIONS
# ==========================================

async def check_redis_health() -> bool:
    """
    Проверка здоровья Redis.

    Returns:
        bool: True если Redis доступен
    """
    if redis_client is None:
        return False

    try:
        await redis_client.ping()
        return True
    except RedisError:
        return False


async def close_redis():
    """Закрытие Redis соединений."""
    if redis_client:
        await redis_client.close()

    if pool:
        await pool.disconnect()


async def clear_redis():
    """Очистка всех ключей в Redis (только для тестов!)."""
    if redis_client:
        await redis_client.flushdb()
