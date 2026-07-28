import uuid
from datetime import datetime
from pydantic import BaseModel,ConfigDict, EmailStr, Field

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=72, description="Senha deve ter no mínimo 8 caracteres e no maximo 32 caracteres")

class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True) 