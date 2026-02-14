"""
WebSocket endpoint с аутентификацией через cookies.

Изменения:
- Токен читается из cookie вместо query параметра
- Fallback на query параметр для совместимости
"""
from fastapi import APIRouter, Cookie, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.infra.db import get_db
from app.infra.redis import get_redis
from app.models import User
from app.schemas.messages import MessageCreate
from app.security import get_user_id_from_token
from app.services.messages import create_message_with_nonce

router = APIRouter(tags=["WebSocket"])


async def get_user_from_websocket(
    websocket: WebSocket,
    db: AsyncSession,
    token_cookie: str | None = None,
    token_query: str | None = None
) -> User | None:
    """
    Получение пользователя из WebSocket соединения.

    Приоритет:
    1. Cookie (access_token)
    2. Query параметр (token) - fallback

    Args:
        websocket: WebSocket connection
        db: Database session
        token_cookie: Токен из cookie
        token_query: Токен из query параметра

    Returns:
        User или None если токен невалидный
    """
    token = token_cookie or token_query

    if not token:
        return None

    user_id = get_user_id_from_token(token)
    if not user_id:
        return None

    user = await db.get(User, user_id)
    if not user or not user.is_active:
        return None

    return user


@router.websocket("/ws/rooms/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    db: AsyncSession = Depends(get_db),
    token: str = Query(None),  # Fallback для старых клиентов
):
    """
    WebSocket endpoint для real-time чата.

    ВАЖНО: Redis получаем внутри, т.к. WebSocket dependencies работают иначе.
    """

    await websocket.accept()

    # Получаем токен из cookie
    token_cookie = websocket.cookies.get("access_token")

    # Аутентификация
    user = await get_user_from_websocket(
        websocket,
        db,
        token_cookie=token_cookie,
        token_query=token
    )

    if not user:
        await websocket.send_json({
            "type": "error",
            "code": "unauthorized",
            "detail": "Authentication required"
        })
        await websocket.close()
        return

    username = user.username

    try:
        from app.infra.redis import redis_client
        redis = redis_client

        # Проверяем что Redis работает
        if redis:
            await redis.ping()
    except Exception as e:
        print(f"⚠️ Redis unavailable in WebSocket: {e}")
        redis = None

    # Subscribe to Redis channel
    channel_name = f"room:{room_id}"

    if redis:
        try:
            pubsub = redis.pubsub()
            await pubsub.subscribe(channel_name)
        except Exception as e:
            print(f"⚠️ Could not subscribe to Redis channel: {e}")
            pubsub = None

    print(f"[WebSocket] User {username} connected to room {room_id}")

    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "room_id": room_id,
            "user": {
                "id": user.id,
                "username": user.username,
                "display_name": user.display_name
            }
        })

        # Handle messages
        import asyncio

        async def receive_messages():
            """Receive messages from client."""
            try:
                while True:
                    data = await websocket.receive_json()

                    if data.get("type") == "message":
                        # Validate and save message
                        try:
                            payload = MessageCreate(
                                body=data.get("body", ""),
                                nonce=data.get("nonce")
                            )

                            msg = await create_message_with_nonce(
                                db=db,
                                room_id=room_id,
                                user_id=user.id,
                                payload=payload,
                                redis=redis
                            )

                            # Publish to Redis (если доступен)
                            if redis:
                                try:
                                    await redis.publish(
                                        channel_name,
                                        {
                                            "type": "message",
                                            "id": msg.id,
                                            "room_id": msg.room_id,
                                            "nonce": msg.nonce,
                                            "body": msg.body,
                                            "created_at": msg.created_at.isoformat(),
                                            "edited_at": None,
                                            "user": {
                                                "id": user.id,
                                                "username": user.username,
                                                "display_name": user.display_name,
                                                "avatar_url": user.avatar_url
                                            }
                                        }
                                    )
                                except Exception as e:
                                    print(f"⚠️ Could not publish to Redis: {e}")
                                    # Fallback: отправляем напрямую через WebSocket
                                    await websocket.send_json({
                                        "type": "message",
                                        "id": msg.id,
                                        "room_id": msg.room_id,
                                        "nonce": msg.nonce,
                                        "body": msg.body,
                                        "created_at": msg.created_at.isoformat(),
                                        "edited_at": None,
                                        "user": {
                                            "id": user.id,
                                            "username": user.username,
                                            "display_name": user.display_name,
                                            "avatar_url": user.avatar_url
                                        }
                                    })

                        except ValueError as e:
                            await websocket.send_json({
                                "type": "error",
                                "code": "validation_error",
                                "detail": str(e)
                            })
                        except Exception as e:
                            print(f"[WebSocket] Error creating message: {e}")
                            await websocket.send_json({
                                "type": "error",
                                "code": "internal_error",
                                "detail": "Failed to send message"
                            })
            except WebSocketDisconnect:
                pass

        async def send_messages():
            """Send messages from Redis to client."""
            if not pubsub:
                # Если нет Redis - просто ждём
                try:
                    while True:
                        await asyncio.sleep(1)
                except WebSocketDisconnect:
                    pass
                return

            try:
                while True:
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                    if message and message['type'] == 'message':
                        await websocket.send_text(message['data'])
                    await asyncio.sleep(0.01)
            except WebSocketDisconnect:
                pass

        # Run both tasks concurrently
        await asyncio.gather(
            receive_messages(),
            send_messages()
        )

    except WebSocketDisconnect:
        print(f"[WebSocket] User {username} disconnected from room {room_id}")
    except Exception as e:
        print(f"[WebSocket] Unexpected error: {e}")
    finally:
        if pubsub:
            await pubsub.unsubscribe(channel_name)
            await pubsub.close()
