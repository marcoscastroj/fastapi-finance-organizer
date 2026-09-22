from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
import pytest
import uuid
from app.models.investment import Investment, InvestmentClass
from app.schemas.investment import InvestmentCreate, InvestmentUpdate
from app.services.investment_service import (
    create_investment,
    get_user_investments,
    get_investment_by_id,
    update_investment,
    delete_investment,
    get_portfolio_summary,
)


@pytest.mark.asyncio
async def test_create_investment_unit():
    mock_db = AsyncMock()
    user_id = uuid.uuid4()

    inv_in = InvestmentCreate(
        ticker="petr4",
        nome="Petrobras PN",
        classe=InvestmentClass.ACOES,
        quantidade=Decimal("100"),
        preco_medio=Decimal("30.00"),
        cotacao_atual=Decimal("35.00"),
    )

    result = await create_investment(mock_db, investment_in=inv_in, user_id=user_id)

    assert result.ticker == "PETR4"
    assert result.user_id == user_id
    assert result.classe == InvestmentClass.ACOES
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()
    mock_db.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_portfolio_summary_unit():
    mock_db = AsyncMock()
    user_id = uuid.uuid4()

    inv1 = Investment(
        id=uuid.uuid4(),
        ticker="PETR4",
        nome="Petrobras PN",
        classe=InvestmentClass.ACOES,
        quantidade=Decimal("100"),
        preco_medio=Decimal("30.00"),
        cotacao_atual=Decimal("36.00"),
        user_id=user_id,
    )
    inv2 = Investment(
        id=uuid.uuid4(),
        ticker="RESERVA",
        nome="Reserva Nubank",
        classe=InvestmentClass.RENDA_EMERGENCIAL,
        quantidade=Decimal("1"),
        preco_medio=Decimal("1000.00"),
        cotacao_atual=Decimal("1000.00"),
        user_id=user_id,
    )

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [inv1, inv2]
    mock_db.execute.return_value = mock_result

    summary = await get_portfolio_summary(mock_db, user_id=user_id)

    # PETR4: Investido 3000, Patrimônio 3600
    # RESERVA: Investido 1000, Patrimônio 1000
    # Total Investido: 4000, Total Patrimônio: 4600, Lucro: 600, Rentabilidade: 15%
    assert summary.patrimonio_total == Decimal("4600.00")
    assert summary.total_investido == Decimal("4000.00")
    assert summary.lucro_prejuizo_absoluto == Decimal("600.00")
    assert summary.rentabilidade_percentual == Decimal("15.00")
    assert len(summary.alocacao_por_classe) == 2
