from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title="Finance Organizer API",
    description="API para organização financeira",
    version="0.1.0",
)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.get("/", tags=["Health Check"])
def read_root():
    return {
        "status": "online",
        "message": "Bem-vindo a API Finance Organizer!",
        "environment" : settings.ENVIRONMENT,
    }