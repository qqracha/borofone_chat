from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Base class for all models SQLAlchemy, inheritance from this
class Base(DeclarativeBase):
    pass

# Room model class, id | title
class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False) # 100 requirement, after alembic migration

# Message model class, id | nonce | room_id | author | body | create_at
class Message(Base):
    """
    id - [int]
    nonce - [str | None]; limit 25, Client identifier for deduplication (optional), in the future crypto.randomUUID()
    room_id - [int]
    Author - [string]; limit 64,
    Body - [string]
    Created_at - [datetime]
    """
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Discord-like: optional nonce, max 25 chars
    nonce: Mapped[str | None] = mapped_column(Text, nullable=True)

    room_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    author: Mapped[str] = mapped_column(String(32), nullable=False) # 32 requirements, after alembic migration
    body: Mapped[str] = mapped_column(Text, nullable=False) # no limit right now, but better add validation by Pydantic

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
