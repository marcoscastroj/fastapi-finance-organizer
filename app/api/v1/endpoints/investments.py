import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.investment import InvestmentClass
from app.models.user import User
from app.schemas.investment import (
    InvestmentCreate,
    InvestmentResponse,
    InvestmentUpdate,
    PortfolioSummaryResponse,
)
from app.services import investment_service

router = APIRouter()


@router.post(
    "/",
    response_model=InvestmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar uma nova posição de investimento",
)
async def create_investment(
    investment_in: InvestmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await investment_service.create_investment(
        db, investment_in=investment_in, user_id=current_user.id
    )


@router.get(
    "/",
    response_model=List[InvestmentResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar posições de investimentos do usuário",
)
async def list_investments(
    classe: Optional[InvestmentClass] = Query(None, description="Filtrar por classe de ativo"),
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=100, description="Limite máximo de registros"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await investment_service.get_user_investments(
        db,
        user_id=current_user.id,
        classe=classe,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/summary",
    response_model=PortfolioSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Obter métricas consolidadas do portfólio de investimentos",
)
async def get_portfolio_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await investment_service.get_portfolio_summary(
        db, user_id=current_user.id
    )


@router.get(
    "/{investment_id}",
    response_model=InvestmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Obter detalhes de uma posição de investimento por ID",
)
async def get_investment(
    investment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    investment = await investment_service.get_investment_by_id(
        db, investment_id=investment_id, user_id=current_user.id
    )
    if not investment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investimento não encontrado.",
        )
    return investment


@router.put(
    "/{investment_id}",
    response_model=InvestmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Atualizar dados de um investimento",
)
async def update_investment(
    investment_id: uuid.UUID,
    investment_in: InvestmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    investment = await investment_service.get_investment_by_id(
        db, investment_id=investment_id, user_id=current_user.id
    )
    if not investment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investimento não encontrado.",
        )
    return await investment_service.update_investment(
        db, db_investment=investment, investment_in=investment_in
    )


@router.delete(
    "/{investment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir uma posição de investimento",
)
async def delete_investment(
    investment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    investment = await investment_service.get_investment_by_id(
        db, investment_id=investment_id, user_id=current_user.id
    )
    if not investment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investimento não encontrado.",
        )
    await investment_service.delete_investment(db, db_investment=investment)
    return None
