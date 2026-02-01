from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.redis import redis_client
from app.models import Message
from app.schemas.messages import MessageCreate

NONCE_TTL_SECONDS = 300
PENDING = "PENDING"


def _nonce_key(author: str, nonce: str) -> str:
    return f"nonce:{author}:{nonce}"

# Discord-like дедупликация сообщений через nonce, см доки.
async def create_message_with_nonce(
        db: AsyncSession,
        room_id: int,
        payload: MessageCreate,
) -> Message:

    # Без nonce — без изменений
    if payload.nonce is None:
        msg = Message(
            room_id=room_id,
            author=payload.author,
            body=payload.body,
            nonce=None,
        )
        db.add(msg)
        await db.commit()
        await db.refresh(msg)
        return msg

    # С nonce — проверяем дедупликацию
    key = _nonce_key(payload.author, payload.nonce)

    # Пытаемся атомарно захватить этот nonce
    acquired = await redis_client.set(key, PENDING, nx=True, ex=NONCE_TTL_SECONDS)

    if not acquired:
        val = await redis_client.get(key)

        if val and val != PENDING:
            # Сообщение уже создано (в Redis msg_id)
            try:
                msg_id = int(val)
                existing = await db.get(Message, msg_id)

                if existing:
                    if payload.enforce_nonce:
                        # СТРОГИЙ режим: дубликат = ошибка
                        raise HTTPException(status_code=409, detail="nonce conflict")
                    else:
                        return existing
            except ValueError:
                pass

        if payload.enforce_nonce:
            raise HTTPException(status_code=409, detail="nonce conflict")

        # Мягкий режим: не смогли найти — создадим новое (риск дубликата минимален)

    # === Создаём новое сообщение ===
    try:
        msg = Message(
            room_id=room_id,
            author=payload.author,
            body=payload.body,
            nonce=payload.nonce,
        )
        db.add(msg)
        await db.commit()
        await db.refresh(msg)
    except Exception:
        # Откатываем блокировку при ошибке БД
        await redis_client.delete(key)
        raise

    # Публикуем msg_id в Redis (для будущих дубликатов)
    # XX проверяет что ключ существует (защита от истечения TTL)
    ok = await redis_client.set(key, str(msg.id), xx=True, ex=NONCE_TTL_SECONDS)
    if not ok:
        # TTL истёк — удаляем ключ для чистоты
        await redis_client.delete(key)

    return msg