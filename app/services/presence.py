"""
Presence tracking - отслеживание онлайн пользователей в комнатах.

Использует Redis sets для хранения списка активных пользователей.
"""
from redis.asyncio import Redis


async def user_joined_room(redis: Redis | None, room_id: int, user_id: int) -> None:
    """
    Пользователь присоединился к комнате (открыл её).
    
    Добавляет user_id в Redis set `room:{room_id}:online`
    """
    if not redis:
        return
    
    try:
        await redis.sadd(f"room:{room_id}:online", str(user_id))
        # TTL 30 секунд — если пользователь не обновит, считается оффлайн
        await redis.expire(f"room:{room_id}:online", 30)
    except Exception as e:
        print(f"[Presence] Error joining room: {e}")


async def user_left_room(redis: Redis | None, room_id: int, user_id: int) -> None:
    """
    Пользователь покинул комнату (закрыл вкладку или сменил комнату).
    
    Удаляет user_id из Redis set `room:{room_id}:online`
    """
    if not redis:
        return
    
    try:
        await redis.srem(f"room:{room_id}:online", str(user_id))
    except Exception as e:
        print(f"[Presence] Error leaving room: {e}")


async def get_online_users(redis: Redis | None, room_id: int) -> list[int]:
    """
    Получить список ID онлайн пользователей в комнате.
    
    Returns:
        List[int]: Список user_id
    """
    if not redis:
        return []
    
    try:
        members = await redis.smembers(f"room:{room_id}:online")
        return [int(m) for m in members]
    except Exception as e:
        print(f"[Presence] Error getting online users: {e}")
        return []


async def heartbeat_room(redis: Redis | None, room_id: int, user_id: int) -> None:
    """
    Heartbeat — обновление присутствия пользователя.
    
    Вызывается периодически (каждые 10-15 сек) чтобы продлить TTL.
    """
    if not redis:
        return
    
    try:
        # Проверяем что пользователь в set
        is_member = await redis.sismember(f"room:{room_id}:online", str(user_id))
        if is_member:
            # Продляем TTL
            await redis.expire(f"room:{room_id}:online", 30)
    except Exception as e:
        print(f"[Presence] Error heartbeat: {e}")
