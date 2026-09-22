import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from sqlalchemy import Date, DateTime, Enum as SQLEnum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class TransactionType(str, Enum):
    RECEITA = "RECEITA"
    DESPESA = "DESPESA"


class RecurrenceType(str, Enum):
    UNICA = "UNICA"
    SEMANAL = "SEMANAL"
    MENSAL = "MENSAL"
    ANUAL = "ANUAL"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    valor: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2), nullable=False
    )
    tipo: Mapped[TransactionType] = mapped_column(
        SQLEnum(
            TransactionType,
            name="transaction_type",
            native_enum=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    data: Mapped[date] = mapped_column(Date, nullable=False)
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    recorrencia: Mapped[RecurrenceType] = mapped_column(
        SQLEnum(
            RecurrenceType,
            name="recurrence_type",
            native_enum=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=RecurrenceType.UNICA,
    )

    conta_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    account: Mapped["Account"] = relationship("Account", back_populates="transactions")
    user: Mapped["User"] = relationship("User", back_populates="transactions")
