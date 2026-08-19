from decimal import Decimal
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, computed_field
from app.models.investment import InvestmentClass


class InvestmentBase(BaseModel):
    ticker: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Código ou símbolo do ativo (ex: PETR4, HGLG11, BTC, CDB-100)",
    )
    nome: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Nome ou descrição do ativo (ex: Petrobras PN, Reserva Emergência Nubank)",
    )
    classe: InvestmentClass = Field(
        ...,
        description="Classe do ativo: ACOES, FIIS, RENDA_FIXA, CRIPTO, ETF, RENDA_EMERGENCIAL",
    )
    quantidade: Decimal = Field(
        ...,
        gt=Decimal("0.00"),
        description="Quantidade custodiada do ativo (deve ser maior que zero)",
    )
    preco_medio: Decimal = Field(
        ...,
        ge=Decimal("0.00"),
        description="Preço médio de aquisição por unidade",
    )
    cotacao_atual: Decimal = Field(
        ...,
        ge=Decimal("0.00"),
        description="Cotação ou valor unitário atual de mercado",
    )


class InvestmentCreate(InvestmentBase):
    pass


class InvestmentUpdate(BaseModel):
    ticker: Optional[str] = Field(None, min_length=1, max_length=20)
    nome: Optional[str] = Field(None, min_length=1, max_length=255)
    classe: Optional[InvestmentClass] = None
    quantidade: Optional[Decimal] = Field(None, gt=Decimal("0.00"))
    preco_medio: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    cotacao_atual: Optional[Decimal] = Field(None, ge=Decimal("0.00"))


class InvestmentResponse(InvestmentBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def total_investido(self) -> Decimal:
        return round(self.quantidade * self.preco_medio, 2)

    @computed_field
    @property
    def patrimonio_atual(self) -> Decimal:
        return round(self.quantidade * self.cotacao_atual, 2)

    @computed_field
    @property
    def lucro_prejuizo_absoluto(self) -> Decimal:
        return round(self.patrimonio_atual - self.total_investido, 2)

    @computed_field
    @property
    def rentabilidade_percentual(self) -> Decimal:
        if self.total_investido > Decimal("0.00"):
            return round(
                (self.lucro_prejuizo_absoluto / self.total_investido) * Decimal("100"), 2
            )
        return Decimal("0.00")

    model_config = ConfigDict(from_attributes=True)


class ClassAllocation(BaseModel):
    classe: InvestmentClass = Field(..., description="Classe de ativo")
    patrimonio_total: Decimal = Field(..., description="Patrimônio total alocado na classe")
    total_investido: Decimal = Field(..., description="Total investido na classe")
    percentual_carteira: Decimal = Field(..., description="Percentual (%) em relação ao patrimônio total da carteira")

    model_config = ConfigDict(from_attributes=True)


class PortfolioSummaryResponse(BaseModel):
    patrimonio_total: Decimal = Field(..., description="Soma do valor atual de todos os ativos")
    total_investido: Decimal = Field(..., description="Soma do custo de aquisição de todos os ativos")
    lucro_prejuizo_absoluto: Decimal = Field(..., description="Diferença absoluta: Patrimônio Total - Total Investido")
    rentabilidade_percentual: Decimal = Field(..., description="Rentabilidade percentual global da carteira")
    alocacao_por_classe: List[ClassAllocation] = Field(
        default_factory=list,
        description="Distribuição detalhada do patrimônio por classe de ativo",
    )

    model_config = ConfigDict(from_attributes=True)
