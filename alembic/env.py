import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.models import Base
from app.settings import settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Миграции в 'offline' режиме.

    Генерирует SQL скрипты без подключения к БД.
    Используется редко (для ручного применения SQL).
    """
    url = settings.database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Выполнение миграций через существующее соединение.
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Миграции через async engine.

    Это основной режим для SQLAlchemy.
    """
    # Берём конфигурацию из alembic.ini
    configuration = config.get_section(config.config_ini_section, {})

    # Подставляем database_url из settings.py
    configuration["sqlalchemy.url"] = settings.database_url

    # Создаём async engine
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # без пула для миграций
    )

    # Выполняем миграции
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    # Закрываем engine
    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Миграции в 'online' режиме (реальное подключение к БД).

    Это основной режим — вызывается при `alembic upgrade`.
    """
    asyncio.run(run_async_migrations())


# Выбор режима: offline или online
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
