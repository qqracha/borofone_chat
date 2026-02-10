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
    body: str
    nonce: str | int | None = None
    enforce_nonce: bool = False

    @field_validator("body")
    @classmethod
    def validate_body(cls, v: str) -> str:
        """
        Limit: 1-4096 characters.
        """
        v = v.strip()

        if not v:
            raise ValueError("body cannot be empty")
        if len(v) > 4096:
            raise ValueError("body must be 4096 characters or less")

        return v

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

    user: MessageUserResponse # user object

    class Config:
        from_attributes = True

# for future, currently not in use
# Attachment
class AttachmentsResponse(BaseModel):
    id: int
    url: str
    filename: str
    size: int
    content_type: str

class MessageWithAttachmentsResponse(MessageResponse):
    attachments: list[AttachmentsResponse] = []
    reply_to: MessageResponse | None = None
    mentions: list[MessageUserResponse] = []