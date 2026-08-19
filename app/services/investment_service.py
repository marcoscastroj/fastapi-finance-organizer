from decimal import Decimal
import uuid
from typing import Optional, Sequence, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.investment import Investment, InvestmentClass
from app.schemas.investment import (
    ClassAllocation,
    InvestmentCreate,
    InvestmentUpdate,
    PortfolioSummaryResponse,
)


async def create_investment(
    db: AsyncSession, investment_in: InvestmentCreate, user_id: uuid.UUID
) -> Investment:
    db_investment = Investment(
        ticker=investment_in.ticker.upper(),
        nome=investment_in.nome,
        classe=investment_in.classe,
        quantidade=investment_in.quantidade,
        preco_medio=investment_in.preco_medio,
        cotacao_atual=investment_in.cotacao_atual,
        user_id=user_id,
    )
    db.add(db_investment)
    await db.commit()
    await db.refresh(db_investment)
    return db_investment


async def get_user_investments(
    db: AsyncSession,
    user_id: uuid.UUID,
    classe: Optional[InvestmentClass] = None,
    skip: int = 0,
    limit: int = 100,
) -> Sequence[Investment]:
    query = select(Investment).where(Investment.user_id == user_id)

    if classe:
        query = query.where(Investment.classe == classe)

    query = query.order_by(Investment.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


async def get_investment_by_id(
    db: AsyncSession, investment_id: uuid.UUID, user_id: uuid.UUID
) -> Optional[Investment]:
    result = await db.execute(
        select(Investment).where(
            Investment.id == investment_id,
            Investment.user_id == user_id,
        )
    )
    return result.scalars().first()


async def update_investment(
    db: AsyncSession, db_investment: Investment, investment_in: InvestmentUpdate
) -> Investment:
    if investment_in.ticker is not None:
        db_investment.ticker = investment_in.ticker.upper()
    if investment_in.nome is not None:
        db_investment.nome = investment_in.nome
    if investment_in.classe is not None:
        db_investment.classe = investment_in.classe
    if investment_in.quantidade is not None:
        db_investment.quantidade = investment_in.quantidade
    if investment_in.preco_medio is not None:
        db_investment.preco_medio = investment_in.preco_medio
    if investment_in.cotacao_atual is not None:
        db_investment.cotacao_atual = investment_in.cotacao_atual

    db.add(db_investment)
    await db.commit()
    await db.refresh(db_investment)
    return db_investment


async def delete_investment(
    db: AsyncSession, db_investment: Investment
) -> None:
    await db.delete(db_investment)
    await db.commit()


async def get_portfolio_summary(
    db: AsyncSession, user_id: uuid.UUID
) -> PortfolioSummaryResponse:
    investments = await get_user_investments(db, user_id=user_id, limit=1000)

    if not investments:
        return PortfolioSummaryResponse(
            patrimonio_total=Decimal("0.00"),
            total_investido=Decimal("0.00"),
            lucro_prejuizo_absoluto=Decimal("0.00"),
            rentabilidade_percentual=Decimal("0.00"),
            alocacao_por_classe=[],
        )

    class_totals: Dict[InvestmentClass, Dict[str, Decimal]] = {}
    patrimonio_total = Decimal("0.00")
    total_investido = Decimal("0.00")

    for inv in investments:
        custo_ativo = round(inv.quantidade * inv.preco_medio, 2)
        patrimonio_ativo = round(inv.quantidade * inv.cotacao_atual, 2)

        patrimonio_total += patrimonio_ativo
        total_investido += custo_ativo

        if inv.classe not in class_totals:
            class_totals[inv.classe] = {
                "patrimonio": Decimal("0.00"),
                "investido": Decimal("0.00"),
            }
        class_totals[inv.classe]["patrimonio"] += patrimonio_ativo
        class_totals[inv.classe]["investido"] += custo_ativo

    lucro_prejuizo = round(patrimonio_total - total_investido, 2)

    rentabilidade_geral = (
        round((lucro_prejuizo / total_investido) * Decimal("100"), 2)
        if total_investido > Decimal("0.00")
        else Decimal("0.00")
    )

    alocacoes: list[ClassAllocation] = []
    for classe, totals in class_totals.items():
        patrimonio_classe = totals["patrimonio"]
        investido_classe = totals["investido"]
        pct = (
            round((patrimonio_classe / patrimonio_total) * Decimal("100"), 2)
            if patrimonio_total > Decimal("0.00")
            else Decimal("0.00")
        )
        alocacoes.append(
            ClassAllocation(
                classe=classe,
                patrimonio_total=patrimonio_classe,
                total_investido=investido_classe,
                percentual_carteira=pct,
            )
        )

    alocacoes.sort(key=lambda x: x.patrimonio_total, reverse=True)

    return PortfolioSummaryResponse(
        patrimonio_total=patrimonio_total,
        total_investido=total_investido,
        lucro_prejuizo_absoluto=lucro_prejuizo,
        rentabilidade_percentual=rentabilidade_geral,
        alocacao_por_classe=alocacoes,
    )
