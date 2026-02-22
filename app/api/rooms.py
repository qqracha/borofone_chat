from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user
from app.infra.db import get_db
from app.models import Room, User
from app.schemas.rooms import RoomCreate, RoomResponse

router = APIRouter(prefix="/rooms", tags=["Rooms"])


def _room_to_response(room: Room) -> RoomResponse:
    return RoomResponse(
        id=room.id,
        title=room.title,
        description=room.description,
        created_at=room.created_at.isoformat(),
    )


@router.get("", response_model=list[RoomResponse])
async def list_rooms(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Room).order_by(Room.created_at.asc()))
    return [_room_to_response(r) for r in result.scalars().all()]


@router.post("", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    payload: RoomCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create rooms",
        )

    room = Room(
        title=payload.title,
        description=payload.description,
        created_by=current_user.id,
    )
    db.add(room)
    await db.commit()

    # Явный SELECT после commit — гарантирует все server-default поля (created_at и др.)
    room = (await db.execute(select(Room).where(Room.id == room.id))).scalar_one()

    return _room_to_response(room)


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    room = await db.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    return _room_to_response(room)


@router.get("/{room_id}/online", response_model=list[dict])
async def get_online_users_in_room(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Получить список онлайн пользователей в комнате.
    
    Returns:
        List[dict]: Список пользователей с полями id, username, display_name, avatar_url
    """
    from app.infra.redis import redis_client
    from app.services.presence import get_online_users
    from sqlalchemy import select
    
    # Получаем ID онлайн пользователей из Redis
    online_ids = await get_online_users(redis_client, room_id)
    
    if not online_ids:
        return []
    
    # Загружаем данные пользователей из БД
    stmt = select(User).where(User.id.in_(online_ids))
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    return [
        {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url,
        }
        for user in users
    ]


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    room = await db.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can delete rooms")

    await db.delete(room)
    await db.commit()
