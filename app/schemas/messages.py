"""
Pydantic schemes for working with chat messages.
"""
from pydantic import BaseModel, field_validator, model_validator

# User nested in message
class MessageUserResponse(BaseModel):
    id: int
    username: str
    display_name: str
    avatar_url: str | None

    class Config:
        from_attributes = True

# Message create
class MessageCreate(BaseModel):
    body: str = ""  # Default empty, can be just attachments
    nonce: str | int | None = None
    enforce_nonce: bool = False
    attachments: list[dict] | None = None  # Список вложений [{"filename": "...", "file_path": "...", "file_size": ..., "mime_type": "..."}]

    @field_validator("body")
    @classmethod
    def validate_body(cls, v: str) -> str:
        """
        Limit: 0-4096 characters. Empty allowed if attachments present.
        """
        if v is None:
            return ""
        v = v.strip()
        if len(v) > 4096:
            raise ValueError("body must be 4096 characters or less")
        return v

    @model_validator(mode="after")
    def validate_body_or_attachments(self):
        """
        Either body or attachments must be present.
        """
        has_body = self.body and self.body.strip()
        has_attachments = self.attachments and len(self.attachments) > 0
        if not has_body and not has_attachments:
            raise ValueError("either body or attachments are required")
        return self

    @field_validator("nonce")
    @classmethod
    def validate_nonce(cls, v: str | int | None) -> str | None:
        """
        Nonce validation, optional 25 characters.
        """
        if v is None:
            return None

        v_str = str(v).strip()

        if len(v_str) > 25:
            raise ValueError("nonce must be 1-25 characters")

        return v_str if v_str else None

    @model_validator(mode="after")
    def validate_enforce_nonce(self):
        """
        If enforce_nonce is True, nonce is required.
        """
        if self.enforce_nonce and not self.nonce:
            raise ValueError("enforce_nonce requires nonce to be set")
        return self


# for future, currently not in use
# Attachment
class AttachmentResponse(BaseModel):
    """Вложение к сообщению."""
    id: int
    message_id: int
    filename: str
    file_path: str
    file_size: int
    mime_type: str | None
    created_at: str

    class Config:
        from_attributes = True

# Message response
class MessageResponse(BaseModel):
    """
    Response schema with user object when creating/receiving a message.
    The user object is populated via a JOIN with the users table.
    - GET /rooms/{id}/messages
    - WebSocket messages
    """
    id: int
    room_id: int
    nonce: str | None
    body: str
    created_at: str  # ISO 8601
    edited_at: str | None
    attachments: list[AttachmentResponse] = []

    user: MessageUserResponse # user object

    class Config:
        from_attributes = True

class MessageWithAttachmentsResponse(MessageResponse):
    attachments: list[AttachmentResponse] = []
    reply_to: MessageResponse | None = None
    mentions: list[MessageUserResponse] = []
