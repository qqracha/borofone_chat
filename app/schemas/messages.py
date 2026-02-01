from pydantic import BaseModel, field_validator, model_validator

# Schema for creating a message (input validation)
class MessageCreate(BaseModel):
    nonce: str | int | None = None
    enforce_nonce: bool = False

    author: str
    body: str

    @field_validator("nonce")
    @classmethod
    def normalize_nonce(cls, v):
        """
        Нормализация nonce: конвертируем в строку и проверяем длину.

        Discord ограничивает nonce до 25 символов.
        None допустим (сообщение без дедупликации).
        """
        if v is None:
            return None
        v = str(v)
        if not (1 <= len(v) <= 25):
            raise ValueError("nonce must be 1..25 chars")
        return v

    @model_validator(mode="after")
    def validate_enforce_nonce(self):
        """
        Проверка консистентности: enforce_nonce требует наличия nonce.

        Если клиент требует строгую дедупликацию (enforce_nonce=true),
        но не передал nonce — это ошибка.
        """
        if self.enforce_nonce and self.nonce is None:
            raise ValueError("enforce_nonce=true requires nonce")
        return self
