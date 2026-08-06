# fastapi-finance-organizer
Finance organizer API in python using fastapi
 ### 🚀 Como Executar o Projeto Atualmente

  Para rodar o ambiente de desenvolvimento e os testes no seu terminal:

  1. Subir o Banco de Dados (PostgreSQL):
    docker compose up -d

  2. Rodar as Migrações do Banco de Dados (Alembic):
    alembic upgrade head

  3. Iniciar a Aplicação FastAPI (Uvicorn):
    uvicorn app.main:app --reload
    Acesse a documentação interativa em: http://127.0.0.1:8000/docs
  4. Rodar a Suíte de Testes (Pytest):
    pytest