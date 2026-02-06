"""
FastAPI dependencies для аутентификации и авторизации.

Содержит:
- get_current_user: получение текущего пользователя из JWT токена
- require_role: проверка роли пользователя
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db import get_db
from app.models import User
from app.security import get_user_id_from_token

# HTTP Bearer схема для Authorization заголовка
security = HTTPBearer()


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency для получения текущего авторизованного пользователя.

    Извлекает JWT токен из Authorization заголовка,
    проверяет его валидность и возвращает объект User.

    Args:
        credentials: HTTP Bearer credentials (токен)
        db: Database session

    Returns:
        User: Объект текущего пользователя

    Raises:
        401: Токен невалидный, истёк или пользователь не найден

    Usage:
        @router.get("/protected")
        async def protected_route(user: User = Depends(get_current_user)):
            return {"user_id": user.id}
    """

    token = credentials.credentials

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
    """
    Алиас для get_current_user (для совместимости с FastAPI документацией).
    """
    return current_user


def require_role(*allowed_roles: str):
    """
    Dependency factory для проверки роли пользователя.

    Args:
        *allowed_roles: Список разрешённых ролей

    Returns:
        Dependency function

    Usage:
        @router.post("/admin/invites", dependencies=[Depends(require_role("admin"))])
        async def create_invite(...):
            ...

        # Или с получением user:
        @router.delete("/admin/users/{user_id}")
        async def delete_user(
            user_id: int,
            current_user: User = Depends(require_role("admin", "moderator"))
        ):
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


# === OPTIONAL AUTH (для endpoints где авторизация опциональна) ===

async def get_current_user_optional(
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
        db: AsyncSession = Depends(get_db)
) -> User | None:
    """
    Dependency для опциональной аутентификации.

    Возвращает User если токен валидный, иначе None.
    Не выбрасывает исключения.

    Usage:
        @router.get("/public-or-private")
        async def route(user: User | None = Depends(get_current_user_optional)):
            if user:
                return {"message": f"Hello, {user.username}"}
            else:
                return {"message": "Hello, anonymous"}
    """

    if credentials is None:
        return None

    token = credentials.credentials
    user_id = get_user_id_from_token(token)

    if user_id is None:
        return None

    user = await db.get(User, user_id)

    if user is None or not user.is_active:
        return None

    return user
