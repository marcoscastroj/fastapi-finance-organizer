import uuid
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class InvestmentClass(str, Enum):
    ACOES = "ACOES"
    FIIS = "FIIS"
    RENDA_FIXA = "RENDA_FIXA"
    CRIPTO = "CRIPTO"
    ETF = "ETF"
    RENDA_EMERGENCIAL = "RENDA_EMERGENCIAL"


class Investment(Base):
    __tablename__ = "investments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    classe: Mapped[InvestmentClass] = mapped_column(
        SQLEnum(
            InvestmentClass,
            name="investment_class",
            native_enum=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        index=True,
    )
    quantidade: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=8), nullable=False
    )
    preco_medio: Mapped[Decimal] = mapped_column(
        Numeric(precision=14, scale=4), nullable=False
    )
    cotacao_atual: Mapped[Decimal] = mapped_column(
        Numeric(precision=14, scale=4), nullable=False
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
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="investments")
