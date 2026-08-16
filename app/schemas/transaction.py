import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from app.models.transaction import TransactionType


class TransactionBase(BaseModel):
    valor: Decimal = Field(
        ...,
        gt=Decimal("0.00"),
        decimal_places=2,
        description="Valor da transação (deve ser positivo e maior que zero)",
    )
    tipo: TransactionType = Field(
        ...,
        description="Tipo da transação: RECEITA ou DESPESA",
    )
    data: date = Field(
        ...,
        description="Data em que a transação ocorreu (YYYY-MM-DD)",
    )
    descricao: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Descrição ou identificador da transação",
    )
    conta_id: uuid.UUID = Field(
        ...,
        description="ID da conta/carteira associada à transação",
    )


class TransactionCreate(TransactionBase):
    pass


class TransactionResponse(TransactionBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
