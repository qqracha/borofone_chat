"""
Настройки приложения.

Все настройки загружаются из переменных окружения (.env файл).
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Настройки приложения с автозагрузкой из .env

    Переменные окружения:
    - DATABASE_URL: URL подключения к PostgreSQL
    - REDIS_URL: URL подключения к Redis
    - JWT_SECRET_KEY: Секретный ключ для подписи JWT токенов
    """

    # Database
    database_url: str = "postgresql+asyncpg://app:password@localhost:5432/app"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT Authentication
    jwt_secret_key: str = "CHANGE_ME_IN_PRODUCTION_USE_LONG_RANDOM_STRING"

    # Для production используй: openssl rand -hex 32

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton instance
settings = Settings()