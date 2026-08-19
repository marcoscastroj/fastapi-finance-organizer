from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
import pytest
import uuid
from app.models.account import Account
from app.models.transaction import Transaction, TransactionType, RecurrenceType
from app.schemas.transaction import TransactionCreate
from app.services.transaction_service import (
    create_transaction,
    get_user_transactions,
    get_transaction_by_id,
    get_monthly_projections,
    delete_transaction,
)


@pytest.mark.asyncio
async def test_create_transaction_success():
    mock_db = AsyncMock()
    user_id = uuid.uuid4()
    conta_id = uuid.uuid4()

    mock_account = Account(id=conta_id, user_id=user_id, apelido="Carteira")
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_account
    mock_db.execute.return_value = mock_result
    mock_db.add = MagicMock()

    tx_in = TransactionCreate(
        valor=Decimal("150.00"),
        tipo=TransactionType.RECEITA,
        data=date(2026, 8, 15),
        descricao="Freelance",
        conta_id=conta_id,
        recorrencia=RecurrenceType.MENSAL,
    )

    created_tx = await create_transaction(mock_db, transaction_in=tx_in, user_id=user_id)

    assert created_tx is not None
    assert created_tx.valor == Decimal("150.00")
    assert created_tx.tipo == TransactionType.RECEITA
    assert created_tx.recorrencia == RecurrenceType.MENSAL
    assert created_tx.user_id == user_id
    assert created_tx.conta_id == conta_id
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()
    mock_db.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_transaction_account_not_found():
    mock_db = AsyncMock()
    user_id = uuid.uuid4()
    conta_id = uuid.uuid4()

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result

    tx_in = TransactionCreate(
        valor=Decimal("50.00"),
        tipo=TransactionType.DESPESA,
        data=date(2026, 8, 15),
        descricao="Lanche",
        conta_id=conta_id,
    )

    created_tx = await create_transaction(mock_db, transaction_in=tx_in, user_id=user_id)
    assert created_tx is None
    mock_db.add.assert_not_called()


@pytest.mark.asyncio
async def test_get_transaction_by_id():
    mock_db = AsyncMock()
    user_id = uuid.uuid4()
    tx_id = uuid.uuid4()

    mock_tx = Transaction(
        id=tx_id,
        valor=Decimal("99.90"),
        tipo=TransactionType.DESPESA,
        data=date(2026, 8, 15),
        descricao="Internet",
        conta_id=uuid.uuid4(),
        user_id=user_id,
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_tx
    mock_db.execute.return_value = mock_result

    found_tx = await get_transaction_by_id(mock_db, transaction_id=tx_id, user_id=user_id)
    assert found_tx is not None
    assert found_tx.id == tx_id


@pytest.mark.asyncio
async def test_delete_transaction():
    mock_db = AsyncMock()
    mock_tx = Transaction(
        id=uuid.uuid4(),
        valor=Decimal("50.00"),
        tipo=TransactionType.DESPESA,
        data=date(2026, 8, 15),
        descricao="Cinema",
        conta_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
    )

    await delete_transaction(mock_db, db_transaction=mock_tx)
    mock_db.delete.assert_called_once_with(mock_tx)
    mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_monthly_projections():
    mock_db = AsyncMock()
    user_id = uuid.uuid4()
    conta_id = uuid.uuid4()

    mock_result = MagicMock()
    mock_result.first.return_value = (Decimal("3500.00"), Decimal("1200.00"))
    mock_db.execute.return_value = mock_result

    projections = await get_monthly_projections(
        mock_db,
        user_id=user_id,
        mes=8,
        ano=2026,
        conta_id=conta_id,
    )

    assert projections.mes == 8
    assert projections.ano == 2026
    assert projections.conta_id == conta_id
    assert projections.receitas_previstas == Decimal("3500.00")
    assert projections.despesas_previstas == Decimal("1200.00")
    assert projections.saldo_projetado == Decimal("2300.00")

