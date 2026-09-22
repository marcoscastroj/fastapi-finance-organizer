from fastapi import APIRouter
from app.api.v1.endpoints import auth, accounts, transactions, investments

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["Accounts"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
api_router.include_router(investments.router, prefix="/investments", tags=["Investments"])