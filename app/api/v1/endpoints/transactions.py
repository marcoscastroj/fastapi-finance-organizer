import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.transaction import (
    TransactionCreate,
    TransactionProjectionsResponse,
    TransactionResponse,
    TransactionStatus,
)
from app.services import transaction_service

router = APIRouter()


@router.post(
    "/",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar uma nova transação (Receita ou Despesa)",
)
async def create_transaction(
    transaction_in: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transaction = await transaction_service.create_transaction(
        db, transaction_in=transaction_in, user_id=current_user.id
    )
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conta não encontrada.",
        )
    return transaction


@router.get(
    "/",
    response_model=List[TransactionResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar transações do usuário com filtros opcionais",
)
async def list_transactions(
    mes: Optional[int] = Query(None, ge=1, le=12, description="Filtrar por mês (1 a 12)"),
    ano: Optional[int] = Query(None, ge=1900, le=2100, description="Filtrar por ano (ex: 2026)"),
    conta_id: Optional[uuid.UUID] = Query(None, description="Filtrar por ID da conta"),
    status: Optional[TransactionStatus] = Query(None, description="Filtrar por status: EFETIVADA (data <= hoje) ou AGENDADA (data > hoje)"),
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=100, description="Limite máximo de registros"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await transaction_service.get_user_transactions(
        db,
        user_id=current_user.id,
        mes=mes,
        ano=ano,
        conta_id=conta_id,
        status=status,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/projections",
    response_model=TransactionProjectionsResponse,
    status_code=status.HTTP_200_OK,
    summary="Obter totalizadores e projeções financeiras do mês",
)
async def get_projections(
    mes: int = Query(..., ge=1, le=12, description="Mês da projeção (1 a 12)"),
    ano: int = Query(..., ge=1900, le=2100, description="Ano da projeção (ex: 2026)"),
    conta_id: Optional[uuid.UUID] = Query(None, description="Filtrar por ID da conta"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await transaction_service.get_monthly_projections(
        db,
        user_id=current_user.id,
        mes=mes,
        ano=ano,
        conta_id=conta_id,
    )


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
    status_code=status.HTTP_200_OK,
    summary="Obter detalhes de uma transação por ID",
)
async def get_transaction(
    transaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transaction = await transaction_service.get_transaction_by_id(
        db, transaction_id=transaction_id, user_id=current_user.id
    )
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transação não encontrada.",
        )
    return transaction


@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deletar uma transação por ID",
)
async def delete_transaction(
    transaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transaction = await transaction_service.get_transaction_by_id(
        db, transaction_id=transaction_id, user_id=current_user.id
    )
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transação não encontrada.",
        )
    await transaction_service.delete_transaction(db, db_transaction=transaction)
    return None
