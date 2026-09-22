import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, computed_field
from app.models.transaction import RecurrenceType, TransactionType


class TransactionStatus(str, Enum):
    EFETIVADA = "EFETIVADA"
    AGENDADA = "AGENDADA"


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
        description="Data em que a transação ocorreu ou está agendada (YYYY-MM-DD)",
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
    recorrencia: RecurrenceType = Field(
        default=RecurrenceType.UNICA,
        description="Padrão de recorrência da transação: UNICA, SEMANAL, MENSAL, ANUAL",
    )


class TransactionCreate(TransactionBase):
    pass


class TransactionResponse(TransactionBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    @computed_field
    @property
    def status(self) -> TransactionStatus:
        return (
            TransactionStatus.EFETIVADA
            if self.data <= date.today()
            else TransactionStatus.AGENDADA
        )

    model_config = ConfigDict(from_attributes=True)


class TransactionProjectionsResponse(BaseModel):
    mes: int = Field(..., ge=1, le=12, description="Mês de referência da projeção (1 a 12)")
    ano: int = Field(..., ge=1900, le=2100, description="Ano de referência da projeção")
    conta_id: Optional[uuid.UUID] = Field(None, description="ID da conta filtrada, se aplicável")
    receitas_previstas: Decimal = Field(
        default=Decimal("0.00"),
        description="Total de receitas previstas no mês (efetivadas + agendadas)",
    )
    despesas_previstas: Decimal = Field(
        default=Decimal("0.00"),
        description="Total de despesas previstas no mês (efetivadas + agendadas)",
    )
    saldo_projetado: Decimal = Field(
        default=Decimal("0.00"),
        description="Saldo líquido projetado para o mês (receitas - despesas)",
    )

    model_config = ConfigDict(from_attributes=True)

