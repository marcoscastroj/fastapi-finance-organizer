import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class AccountBase(BaseModel):
    apelido: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Apelido/Nome identificador da conta (ex: Nubank, Carteira Física)",
    )

class AccountCreate(AccountBase):
    pass

class AccountUpdate(BaseModel):
    apelido: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Novo Apelido de Conta",
    )

class AccountResponse(AccountBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)