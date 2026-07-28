# Arquitetura do Projeto: FinCore API
**V1 (Manual) & V2 (Automação PDF)**

**Descrição:** API para sistema financeiro minimalista, focado em privacidade, sem armazenamento de dados sensíveis e com processamento de PDFs de fatura estritamente em memória.
**Stack Definida:** Python 3.12+, FastAPI, Uvicorn, PostgreSQL (Supabase), SQLAlchemy, Alembic (Migrações), JWT Auth.

---

## 1. Estrutura de Diretórios (Clean Architecture)
O repositório será estruturado em camadas para garantir baixo acoplamento e facilitar os testes e validações de qualidade:

*   `app/core/`: Configurações globais (Pydantic Settings), segurança (JWT, hashing de senhas) e dependências globais.
*   `app/db/`: Conexão com o banco de dados PostgreSQL/Supabase, sessão SQLAlchemy (`session.py`) e classe base (`base.py`).
*   `app/models/`: Entidades ORM do SQLAlchemy (mapeamento relacional das tabelas do banco de dados).
*   `app/schemas/`: Schemas Pydantic (validação de payloads das requisições HTTP e contratos de resposta DTO).
*   `app/services/`: Regras de negócio puras (casos de uso da aplicação, isolados do framework web).
*   `app/api/`: Controladores HTTP (Routers do FastAPI) organizados por versão (`app/api/v1/endpoints/`).
*   `app/infrastructure/`: Integrações externas e utilitários específicos (ex: leitor efêmero de PDF em memória para a V2).
*   `tests/`: Suíte de testes automatizados unitários e de integração (Pytest).

---

## 2. Definição de Endpoints (Contrato da API)

### Módulo de Autenticação (Auth)

*   **POST** `/api/v1/auth/register`
    *   **Objetivo:** Criar usuário anônimo apenas com credenciais essenciais.
    *   **Request (JSON):** `{ "email": "user@email.com", "password": "StrongPassword123" }`
    *   **Response (201):** `{ "id": "uuid", "email": "user@email.com", "created_at": "timestamp" }`

*   **POST** `/api/v1/auth/login`
    *   **Objetivo:** Autenticar e gerar token JWT stateless.
    *   **Request (JSON):** `{ "email": "user@email.com", "password": "StrongPassword123" }`
    *   **Response (200):** `{ "access_token": "eyJhbG...", "token_type": "bearer" }`

*   **DELETE** `/api/v1/auth/me`
    *   **Objetivo:** Hard delete imediato da conta e limpeza em cascata no banco.
    *   **Response (204 No Content):** Sem corpo.

### Módulo de Contas (Accounts)

*   **POST** `/api/v1/accounts`
    *   **Objetivo:** Criar uma nova carteira.
    *   **Request (JSON):** `{ "apelido": "C6 Bank" }`
    *   **Response (201):** `{ "id": "uuid", "apelido": "C6 Bank", "saldo_calculado": 0.00 }`

*   **GET** `/api/v1/accounts`
    *   **Objetivo:** Listar contas do usuário calculando o saldo no momento da requisição.
    *   **Response (200):** `[ { "id": "uuid", "apelido": "C6 Bank", "saldo_calculado": 1250.75 } ]`

### Módulo de Transações (Transactions) - V1

*   **POST** `/api/v1/transactions`
    *   **Objetivo:** Registrar nova transação (Receita ou Despesa).
    *   **Request (JSON):** `{ "valor": 50.00, "tipo": "DESPESA", "data": "2026-07-28", "descricao": "Combustível", "conta_id": "uuid" }`
    *   **Response (201):** `{ "id": "uuid", "valor": 50.00, "tipo": "DESPESA", ... }`

*   **GET** `/api/v1/transactions`
    *   **Objetivo:** Recuperar histórico filtrado (mês, ano, conta).
    *   **Query Params:** `?mes=07&ano=2026&conta_id=uuid` (Opcionais)
    *   **Response (200):** Array de objetos de transação.

### Módulo de Extração Efêmera (V2)

*   **POST** `/api/v1/transactions/extract`
    *   **Objetivo:** Receber PDF via form-data, ler em memória, devolver dados e acionar Garbage Collector.
    *   **Request:** `multipart/form-data (file: fatura.pdf)`
    *   **Response (200):** JSON com a lista mapeada via Regex para o Frontend confirmar antes de persistir:
        `[ { "data": "2026-07-20", "descricao": "Uber", "valor": 32.50 } ]`

---

## 3. Estratégia de Qualidade e CI/CD

O design dos contratos acima foi pensado para facilitar a cobertura de testes de negócio:

1.  **Automação de API (Contrato/Integração):** A padronização RESTful facilita suítes robustas, seja usando Pytest nativamente ou scripts em Rest Assured/Cypress acoplados à pipeline do GitLab.
2.  **Testes de Performance:** Endpoints cruciais, principalmente a rota `/extract` da V2, devem ser validados quanto ao consumo de RAM sob carga utilizando ferramentas como JMeter ou k6 antes do deploy no Render.
3.  **Pipeline:** Garantir stages de Linting (flake8/black), Testes, Build e Deploy automatizados.