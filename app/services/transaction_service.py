from datetime import date
from decimal import Decimal
import uuid
from typing import Optional, Sequence
from sqlalchemy import case, extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.account import Account
from app.models.transaction import Transaction, TransactionType
from app.schemas.transaction import (
    TransactionCreate,
    TransactionProjectionsResponse,
    TransactionStatus,
)


async def create_transaction(
    db: AsyncSession, transaction_in: TransactionCreate, user_id: uuid.UUID
) -> Optional[Transaction]:
    account_check = await db.execute(
        select(Account).where(
            Account.id == transaction_in.conta_id,
            Account.user_id == user_id,
        )
    )
    account = account_check.scalars().first()
    if not account:
        return None

    db_transaction = Transaction(
        valor=transaction_in.valor,
        tipo=transaction_in.tipo,
        data=transaction_in.data,
        descricao=transaction_in.descricao,
        recorrencia=transaction_in.recorrencia,
        conta_id=transaction_in.conta_id,
        user_id=user_id,
    )
    db.add(db_transaction)
    await db.commit()
    await db.refresh(db_transaction)
    return db_transaction


async def get_user_transactions(
    db: AsyncSession,
    user_id: uuid.UUID,
    mes: Optional[int] = None,
    ano: Optional[int] = None,
    conta_id: Optional[uuid.UUID] = None,
    status: Optional[TransactionStatus] = None,
    skip: int = 0,
    limit: int = 100,
) -> Sequence[Transaction]:
    query = select(Transaction).where(Transaction.user_id == user_id)

    if conta_id:
        query = query.where(Transaction.conta_id == conta_id)

    if ano:
        query = query.where(extract("year", Transaction.data) == ano)

    if mes:
        query = query.where(extract("month", Transaction.data) == mes)

    if status == TransactionStatus.EFETIVADA:
        query = query.where(Transaction.data <= date.today())
    elif status == TransactionStatus.AGENDADA:
        query = query.where(Transaction.data > date.today())

    query = query.order_by(Transaction.data.desc(), Transaction.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


async def get_transaction_by_id(
    db: AsyncSession, transaction_id: uuid.UUID, user_id: uuid.UUID
) -> Optional[Transaction]:
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id,
        )
    )
    return result.scalars().first()


async def get_monthly_projections(
    db: AsyncSession,
    user_id: uuid.UUID,
    mes: int,
    ano: int,
    conta_id: Optional[uuid.UUID] = None,
) -> TransactionProjectionsResponse:
    receitas_expr = func.coalesce(
        func.sum(
            case(
                (Transaction.tipo == TransactionType.RECEITA, Transaction.valor),
                else_=0,
            )
        ),
        0,
    ).label("receitas_previstas")

    despesas_expr = func.coalesce(
        func.sum(
            case(
                (Transaction.tipo == TransactionType.DESPESA, Transaction.valor),
                else_=0,
            )
        ),
        0,
    ).label("despesas_previstas")

    query = select(receitas_expr, despesas_expr).where(
        Transaction.user_id == user_id,
        extract("year", Transaction.data) == ano,
        extract("month", Transaction.data) == mes,
    )

    if conta_id:
        query = query.where(Transaction.conta_id == conta_id)

    result = await db.execute(query)
    row = result.first()

    receitas = Decimal(str(row[0])) if row else Decimal("0.00")
    despesas = Decimal(str(row[1])) if row else Decimal("0.00")
    saldo = receitas - despesas

    return TransactionProjectionsResponse(
        mes=mes,
        ano=ano,
        conta_id=conta_id,
        receitas_previstas=receitas,
        despesas_previstas=despesas,
        saldo_projetado=saldo,
    )


async def delete_transaction(
    db: AsyncSession, db_transaction: Transaction
) -> None:
    await db.delete(db_transaction)
    await db.commit()

