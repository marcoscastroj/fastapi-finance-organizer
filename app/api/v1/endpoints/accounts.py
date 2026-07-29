import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.account import AccountCreate, AccountResponse, AccountUpdate
from app.services import account_service

router = APIRouter()

@router.post(
    "/",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar uma nova conta/carteira",
)
async def create_account(
    account_in: AccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await account_service.create_account(
        db, account_in=account_in, user_id=current_user.id
    )

@router.get(
    "/",
    response_model=List[AccountResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar todas as contas do usuario logado",
)
async def list_accounts(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await account_service.get_user_accounts(
        db, user_id=current_user.id, skip=skip, limit=limit
    )

@router.get(
    "/{account_id}",
    response_model=AccountResponse,
    status_code=status.HTTP_200_OK,
    summary="Obter detalhes de uma conta por ID",
)
async def get_account(
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = await account_service.get_account_by_id(
        db, account_id=account_id, user_id=current_user.id
    )
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conta não encontrada.",
        )
    return account

@router.put(
    "/{account_id}",
    response_model=AccountResponse,
    status_code=status.HTTP_200_OK,
)
async def update_account(
        account_id: uuid.UUID,
        account_in: AccountUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    account = await account_service.get_account_by_id(
        db, account_id=account_id, user_id=current_user.id
    )
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conta não encontrada",
        )

    return await account_service.update_account(
        db, db_account=account, account_in=account_in
    )

@router.delete(
    "/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deletar uma conta",
)
async def delete_account(
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = await account_service.get_account_by_id(
        db, account_id=account_id, user_id=current_user.id
    )
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conta não encontrada.",
        )
    await account_service.delete_account(db, db_account=account)
    return None