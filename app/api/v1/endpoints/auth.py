from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.core.limiter import limiter
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token
from app.db.session import get_db
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import (
    authenticate_user,
    create_user,
    get_user_by_email,
    delete_user
)
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar um novo usuário anônimo",
)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Um usuário com este email já existe.",
        )
    new_user = await create_user(db, user_in=user_in)
    return new_user

@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Autenticar e gerar token JWT",
)
@limiter.limit("5/minute")
async def login(request: Request, user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(
        db, email=user_in.email, password=user_in.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=str(user.id))
    return Token(access_token=access_token, token_type="bearer")

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Obter dados do usuário logado"
)
async def read_user_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.delete(
    "/me",
    status_code = status.HTTP_204_NO_CONTENT,
    summary = "Hard delete imediato da conta e limpeza em cascata no banco"
)
async def delete_user_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await delete_user(db, user=current_user)
    return None