import uuid
from typing import Sequence, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.account import Account
from app.schemas.account import AccountCreate, AccountUpdate

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
    return db_account

async def get_user_accounts(
        db: AsyncSession, user_id: uuid.UUID, skip: int=0, limit: int= 100
) -> Sequence[Account]:
    result = await db.execute(
        select(Account)
        .where(Account.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .order_by(Account.created_at.desc())
    )
    return result.scalars().all()

async def get_account_by_id(
        db: AsyncSession, account_id: uuid.UUID, user_id: uuid.UUID
) -> Optional[Account]:
    result = await db.execute(
        select(Account)
        .where(
            Account.id == account_id, 
            Account.user_id == user_id,
            )
    )
    return result.scalars().first()

async def update_account(
        db: AsyncSession, db_account: Account, account_in: AccountUpdate
) -> Account:
    if account_in.apelido is not None:
        db_account.apelido = account_in.apelido

    db.add(db_account)
    await db.commit()
    await db.refresh(db_account)
    return db_account

async def delete_account(db: AsyncSession, db_account: Account) -> None:
    await db.delete(db_account)
    await db.commit()