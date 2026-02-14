"""
Message service with nonce deduplication using Redis.

Changes:
- Redis client через dependency вместо global import
- Fallback если Redis недоступен
- Proper error handling
"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import TYPE_CHECKING
from redis.asyncio import Redis
from sqlalchemy import select

from app.infra.redis import redis_client
from app.models import Message
from app.schemas.messages import MessageCreate

if TYPE_CHECKING:
    from redis.asyncio import Redis

NONCE_TTL_SECONDS = 300
PENDING = "PENDING"


def _nonce_key(user_id: int, nonce: str) -> str:
    """Generate Redis key for nonce."""
    return f"nonce:{user_id}:{nonce}"

# Discord-like deduplication message by nonce, docs for more info.
async def create_message_with_nonce(
        db: AsyncSession,
        room_id: int,
        user_id: int,
        payload: MessageCreate,
        redis: Redis | None = None,
) -> Message:

    # No nonce - no change
    if payload.nonce is None:
        msg = Message(
            room_id=room_id,
            user_id=user_id,
            body=payload.body,
            nonce=None,
        )
        db.add(msg)
        await db.commit()
        await db.refresh(msg)
        return msg

    # With nonce — check deduplication
    key = _nonce_key(user_id, payload.nonce)

    # === CASE 2: Redis unavailable - fallback to DB-only deduplication ===
    if redis is None:
        # Проверка дубликата в БД
        stmt = select(Message).where(
            Message.user_id == user_id,
            Message.nonce == payload.nonce
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            if payload.enforce_nonce:
                raise HTTPException(status_code=409, detail="nonce conflict")
            return existing

        # Создание нового сообщения
        msg = Message(
            room_id=room_id,
            user_id=user_id,
            body=payload.body,
            nonce=payload.nonce,
        )
        db.add(msg)
        await db.commit()
        await db.refresh(msg)
        return msg

    try:
        # Trying to atomically capture nonce
        acquired = await redis_client.set(key, PENDING, nx=True, ex=NONCE_TTL_SECONDS)

        if not acquired:
            val = await redis_client.get(key)

            if val and val != PENDING:
                # Message already created (msg_id in Redis)
                try:
                    msg_id = int(val)
                    existing = await db.get(Message, msg_id)

                    if existing:
                        if payload.enforce_nonce:
                            # Strict mode: Duplicate = Error 409
                            raise HTTPException(status_code=409, detail="nonce conflict")
                        else:
                            return existing
                except (ValueError, TypeError):
                    pass

            if payload.enforce_nonce:
                raise HTTPException(status_code=409, detail="nonce conflict")

            # Soft mode: couldn't find it, we'll create a new one (the risk of a duplicate is minimal)

        # Create a new message
        try:
            msg = Message(
                room_id=room_id,
                user_id=user_id,
                body=payload.body,
                nonce=payload.nonce,
            )
            db.add(msg)
            await db.commit()
            await db.refresh(msg)
        except Exception:
            await redis_client.delete(key)
            raise

        # Publish msg_id to Redis (for future duplicates)
        # XX checks that the key exists (protects against TTL expiration)
        ok = await redis_client.set(key, str(msg.id), xx=True, ex=NONCE_TTL_SECONDS)
        if not ok:
            # TTL expired - delete key for cleanup
            await redis_client.delete(key)

        return msg

    except Exception as e:
        # Если Redis упал - fallback на DB-only логику
        if "Redis" in str(type(e).__name__):
            print(f"⚠️ Redis unavailable, falling back to DB-only: {e}")
            # Recursive call без Redis
            return await create_message_with_nonce(db, room_id, user_id, payload, redis=None)
        raise
