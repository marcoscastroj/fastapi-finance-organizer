from fastapi import FastAPI

app = FastAPI(
    title="Finance Organizer API",
    description="API para organização financeira",
    version="0.1.0",
)

@app.get("/", tags=["Health Check"])
def read_root():
    return {
        "status": "online",
        "message": "Bem-vindo a API Finance Organizer!",
    }