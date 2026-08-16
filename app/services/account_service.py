from decimal import Decimal
import uuid
from typing import Sequence, Optional
from sqlalchemy import case, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.account import Account
from app.models.transaction import Transaction, TransactionType
from app.schemas.account import AccountCreate, AccountUpdate


def _calculate_balance_expr():
    return func.coalesce(
        func.sum(
            case(
                (Transaction.tipo == TransactionType.RECEITA, Transaction.valor),
                else_=-Transaction.valor,
            )
        ),
        0,
    ).label("saldo_calculado")


async def create_account(
    db: AsyncSession, account_in: AccountCreate, user_id: uuid.UUID
) -> Account:
    db_account = Account(
        apelido=account_in.apelido,
        user_id=user_id,
    )
    db.add(db_account)
    await db.commit()
    await db.refresh(db_account)
    setattr(db_account, "saldo_calculado", Decimal("0.00"))
    return db_account


async def get_user_accounts(
    db: AsyncSession, user_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> Sequence[Account]:
    stmt = (
        select(Account, _calculate_balance_expr())
        .outerjoin(Transaction, Transaction.conta_id == Account.id)
        .where(Account.user_id == user_id)
        .group_by(Account.id)
        .order_by(Account.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()
    accounts = []
    for account, saldo in rows:
        setattr(account, "saldo_calculado", Decimal(str(saldo)))
        accounts.append(account)
    return accounts


async def get_account_by_id(
    db: AsyncSession, account_id: uuid.UUID, user_id: uuid.UUID
) -> Optional[Account]:
    stmt = (
        select(Account, _calculate_balance_expr())
        .outerjoin(Transaction, Transaction.conta_id == Account.id)
        .where(Account.id == account_id, Account.user_id == user_id)
        .group_by(Account.id)
    )
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        return None
    account, saldo = row
    setattr(account, "saldo_calculado", Decimal(str(saldo)))
    return account


async def update_account(
    db: AsyncSession, db_account: Account, account_in: AccountUpdate
) -> Account:
    if account_in.apelido is not None:
        db_account.apelido = account_in.apelido

    db.add(db_account)
    await db.commit()
    await db.refresh(db_account)
    
    updated = await get_account_by_id(db, account_id=db_account.id, user_id=db_account.user_id)
    return updated or db_account


async def delete_account(db: AsyncSession, db_account: Account) -> None:
    await db.delete(db_account)
    await db.commit()