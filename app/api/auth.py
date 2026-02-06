"""
Authentication endpoints.

Содержит:
- POST /auth/register - регистрация по инвайт-коду
- POST /auth/login - вход по email/password
- POST /auth/refresh - обновление access токена
- GET /auth/me - получение информации о текущем пользователе
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db import get_db
from app.models import Invite, User
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.dependencies import get_current_user  # Создадим это позже

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Регистрация нового пользователя по инвайт-коду.

    Шаги:
    1. Проверка инвайт-кода (существует, не истёк, не исчерпан)
    2. Проверка уникальности email и username
    3. Создание пользователя с хешированным паролем
    4. Увеличение счётчика использований инвайта
    5. Возврат JWT токенов

    Args:
        data: RegisterRequest с email, password, username, display_name, invite_code

    Returns:
        TokenResponse: access_token и refresh_token

    Raises:
        400: Инвайт-код невалидный или исчерпан
        409: Email или username уже существуют
    """

    # === 1. Проверка инвайт-кода ===
    stmt = select(Invite).where(Invite.code == data.invite_code)
    result = await db.execute(stmt)
    invite = result.scalar_one_or_none()

    if not invite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid invite code"
        )

    # Проверка: не отозван ли
    if invite.revoked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invite code has been revoked"
        )

    # Проверка: не истёк ли
    if invite.expires_at and invite.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invite code has expired"
        )

    # Проверка: не исчерпан ли лимит использований
    if invite.max_uses and invite.current_uses >= invite.max_uses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invite code has reached maximum uses"
        )

    # === 2. Проверка уникальности email ===
    stmt = select(User).where(User.email == data.email)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # === 3. Проверка уникальности username ===
    stmt = select(User).where(User.username == data.username)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken"
        )

    # === 4. Создание пользователя ===
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        username=data.username,
        display_name=data.display_name,
        role="member"  # По умолчанию обычный пользователь
    )

    db.add(user)
    await db.flush()  # Чтобы получить user.id

    # === 5. Увеличение счётчика инвайта ===
    invite.current_uses += 1

    await db.commit()
    await db.refresh(user)

    # === 6. Генерация токенов ===
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Вход по email и паролю.

    Args:
        data: LoginRequest с email и password

    Returns:
        TokenResponse: access_token и refresh_token

    Raises:
        401: Неверный email или пароль
        403: Аккаунт заблокирован
    """

    # Поиск пользователя по email
    stmt = select(User).where(User.email == data.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    # Проверка существования и пароля
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Проверка активности аккаунта
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    # Генерация токенов
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Обновление access токена через refresh токен.

    Args:
        data: RefreshRequest с refresh_token

    Returns:
        TokenResponse: новый access_token и тот же refresh_token

    Raises:
        401: Refresh токен невалидный или истёк
    """

    try:
        # Декодирование и проверка токена
        payload = decode_token(data.refresh_token)

        # Проверка типа токена
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        # Проверка существования пользователя
        user = await db.get(User, int(user_id))
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or disabled"
            )

        # Генерация нового access токена
        access_token = create_access_token({"sub": user_id})

        return TokenResponse(
            access_token=access_token,
            refresh_token=data.refresh_token  # Возвращаем тот же refresh токен
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """
    Получение информации о текущем авторизованном пользователе.

    Requires: Authorization header с Bearer токеном

    Returns:
        UserResponse: информация о пользователе
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        display_name=current_user.display_name,
        avatar_url=current_user.avatar_url,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat()
    )
