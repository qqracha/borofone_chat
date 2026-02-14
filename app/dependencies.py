"""
FastAPI dependencies для аутентификации через cookies.

Изменения:
- Токены читаются из httpOnly cookies вместо Authorization header
- Fallback на Authorization header для совместимости с API клиентами
"""
from fastapi import Cookie, Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db import get_db
from app.models import User
from app.security import get_user_id_from_token


async def get_current_user(
        request: Request,
        db: AsyncSession = Depends(get_db),
        access_token: str = Cookie(None, alias="access_token"),
) -> User:
    """
    Dependency для получения текущего авторизованного пользователя.

    Приоритет получения токена:
    1. Cookie (access_token) - основной способ
    2. Authorization header - fallback для API клиентов

    Args:
        request: FastAPI Request
        db: Database session
        access_token: Токен из cookie

    Returns:
        User: Объект текущего пользователя

    Raises:
        401: Токен невалидный, истёк или пользователь не найден
    """

    token = access_token

    # Fallback: проверяем Authorization header
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Извлечение user_id из токена
    user_id = get_user_id_from_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Поиск пользователя в БД
    user = await db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Проверка активности
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    return user


async def get_current_active_user(
        current_user: User = Depends(get_current_user)
) -> User:
    """Алиас для get_current_user."""
    return current_user


def require_role(*allowed_roles: str):
    """
    Dependency factory для проверки роли пользователя.

    Usage:
        @router.post("/admin/invites")
        async def create_invite(user: User = Depends(require_role("admin"))):
            ...
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        """Проверка роли текущего пользователя."""

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(allowed_roles)}"
            )

        return current_user

    return role_checker


# Shortcuts для часто используемых ролей
require_admin = require_role("admin")
require_moderator = require_role("admin", "moderator")


async def get_current_user_optional(
        request: Request,
        db: AsyncSession = Depends(get_db),
        access_token: str = Cookie(None, alias="access_token")
) -> User | None:
    """
    Dependency для опциональной аутентификации.

    Возвращает User если токен валидный, иначе None.
    Не выбрасывает исключения.
    """
    token = access_token

    # Fallback: Authorization header
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")

    if not token:
        return None

    user_id = get_user_id_from_token(token)

    if user_id is None:
        return None

    user = await db.get(User, user_id)

    if user is None or not user.is_active:
        return None

    return user
