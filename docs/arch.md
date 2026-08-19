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
    *   **Objetivo:** Listar contas do usuário calculando o saldo real no momento da requisição (considera apenas transações com data <= data atual).
    *   **Response (200):** `[ { "id": "uuid", "apelido": "C6 Bank", "saldo_calculado": 1250.75 } ]`

### Módulo de Transações (Transactions) - V1 & Lançamentos Futuros / Recorrência

*   **POST** `/api/v1/transactions`
    *   **Objetivo:** Registrar nova transação (Receita ou Despesa, presente ou futura, com recorrência).
    *   **Request (JSON):** `{ "valor": 50.00, "tipo": "DESPESA", "data": "2026-07-28", "descricao": "Combustível", "conta_id": "uuid", "recorrencia": "UNICA" }`
    *   **Recorrências Suportadas:** `UNICA`, `SEMANAL`, `MENSAL`, `ANUAL` (Default: `UNICA`).
    *   **Response (201):** `{ "id": "uuid", "valor": 50.00, "tipo": "DESPESA", "data": "2026-07-28", "descricao": "Combustível", "conta_id": "uuid", "recorrencia": "UNICA", "status": "EFETIVADA" }`

*   **GET** `/api/v1/transactions`
    *   **Objetivo:** Recuperar histórico filtrado (mês, ano, conta, status).
    *   **Query Params:** `?mes=07&ano=2026&conta_id=uuid&status=EFETIVADA` (Opcionais).
    *   **Status Suportados:** `EFETIVADA` (data <= hoje) ou `AGENDADA` (data > hoje).
    *   **Response (200):** Array de objetos de transação com status dinâmico.

*   **GET** `/api/v1/transactions/projections`
    *   **Objetivo:** Obter totalizadores projetados do mês (Receitas Previstas, Despesas Previstas e Saldo Projetado).
    *   **Query Params:** `?mes=08&ano=2026&conta_id=uuid` (`mes` e `ano` obrigatórios, `conta_id` opcional).
    *   **Response (200):**
        ```json
        {
          "mes": 8,
          "ano": 2026,
          "conta_id": "uuid | null",
          "receitas_previstas": 5000.00,
          "despesas_previstas": 2150.50,
          "saldo_projetado": 2849.50
        }
        ```

*   **Regra de Negócio de Saldos e Projeções:**
    *   **Saldo Atual da Carteira (GET `/api/v1/accounts`):** Soma apenas transações efetivadas (`data <= hoje`), garantindo que lançamentos futuros não alterem o saldo real em caixa.
    *   **Saldo Projetado (GET `/api/v1/transactions/projections`):** Soma todas as transações previstas no mês/ano (`receitas_previstas - despesas_previstas`), permitindo visão futura de fluxo de caixa.

### Módulo de Investimentos (Investments & Portfolio)

*   **POST** `/api/v1/investments`
    *   **Objetivo:** Cadastrar nova posição de investimento.
    *   **Classes Suportadas:** `ACOES`, `FIIS`, `RENDA_FIXA`, `CRIPTO`, `ETF`, `RENDA_EMERGENCIAL`.
    *   **Request (JSON):**
        ```json
        {
          "ticker": "PETR4",
          "nome": "Petrobras PN",
          "classe": "ACOES",
          "quantidade": 100,
          "preco_medio": 35.50,
          "cotacao_atual": 38.20
        }
        ```
    *   **Response (201):** Objeto do investimento criado com IDs, timestamps e métricas individuais (`total_investido`, `patrimonio_atual`, `lucro_prejuizo_absoluto`, `rentabilidade_percentual`).

*   **GET** `/api/v1/investments`
    *   **Objetivo:** Listar posições de investimentos do usuário com filtro opcional por classe.
    *   **Query Params:** `?classe=ACOES&skip=0&limit=100` (Opcionais).
    *   **Response (200):** Array de objetos de investimentos.

*   **GET** `/api/v1/investments/{investment_id}`
    *   **Objetivo:** Obter detalhes de um investimento por ID.
    *   **Response (200):** Objeto do investimento.

*   **PUT** `/api/v1/investments/{investment_id}`
    *   **Objetivo:** Atualizar dados de um investimento (quantidade, cotação atual, preço médio, nome, classe).
    *   **Response (200):** Objeto atualizado.

*   **DELETE** `/api/v1/investments/{investment_id}`
    *   **Objetivo:** Excluir posição de investimento.
    *   **Response (204 No Content):** Sem corpo.

*   **GET** `/api/v1/investments/summary`
    *   **Objetivo:** Obter totalizadores consolidados da carteira de investimentos (Patrimônio Total, Total Investido, Lucro Absoluto, Rentabilidade (%) e Distribuição por Classe).
    *   **Response (200):**
        ```json
        {
          "patrimonio_total": 45000.00,
          "total_investido": 40000.00,
          "lucro_prejuizo_absoluto": 5000.00,
          "rentabilidade_percentual": 12.50,
          "alocacao_por_classe": [
            {
              "classe": "ACOES",
              "patrimonio_total": 20000.00,
              "total_investido": 18000.00,
              "percentual_carteira": 44.44
            },
            {
              "classe": "RENDA_EMERGENCIAL",
              "patrimonio_total": 15000.00,
              "total_investido": 15000.00,
              "percentual_carteira": 33.33
            }
          ]
        }
        ```

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