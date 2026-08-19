import uuid
from decimal import Decimal
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_receita_and_despesa(client: AsyncClient):
    # Cadastro e Login
    await client.post("/api/v1/auth/register", json={"email": "user_trans@example.com", "password": "password123"})
    login_res = await client.post("/api/v1/auth/login", json={"email": "user_trans@example.com", "password": "password123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Criar Conta
    acc_res = await client.post("/api/v1/accounts/", json={"apelido": "Banco Inter"}, headers=headers)
    assert acc_res.status_code == 201
    account_id = acc_res.json()["id"]

    # 1. Registrar RECEITA
    receita_payload = {
        "valor": 2500.00,
        "tipo": "RECEITA",
        "data": "2026-08-15",
        "descricao": "Salário Mensal",
        "conta_id": account_id,
    }
    rec_res = await client.post("/api/v1/transactions/", json=receita_payload, headers=headers)
    assert rec_res.status_code == 201
    rec_data = rec_res.json()
    assert Decimal(str(rec_data["valor"])) == Decimal("2500.00")
    assert rec_data["tipo"] == "RECEITA"
    assert rec_data["descricao"] == "Salário Mensal"
    assert rec_data["data"] == "2026-08-15"
    assert rec_data["conta_id"] == account_id
    assert "id" in rec_data

    # 2. Registrar DESPESA
    despesa_payload = {
        "valor": 350.75,
        "tipo": "DESPESA",
        "data": "2026-08-16",
        "descricao": "Supermercado",
        "conta_id": account_id,
    }
    desp_res = await client.post("/api/v1/transactions/", json=despesa_payload, headers=headers)
    assert desp_res.status_code == 201
    desp_data = desp_res.json()
    assert Decimal(str(desp_data["valor"])) == Decimal("350.75")
    assert desp_data["tipo"] == "DESPESA"


@pytest.mark.asyncio
async def test_reject_negative_and_zero_values(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={"email": "user_val@example.com", "password": "password123"})
    login_res = await client.post("/api/v1/auth/login", json={"email": "user_val@example.com", "password": "password123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    acc_res = await client.post("/api/v1/accounts/", json={"apelido": "Carteira"}, headers=headers)
    account_id = acc_res.json()["id"]

    # Valor negativo deve ser rejeitado (422)
    neg_res = await client.post(
        "/api/v1/transactions/",
        json={
            "valor": -50.00,
            "tipo": "DESPESA",
            "data": "2026-08-15",
            "descricao": "Valor negativo inválido",
            "conta_id": account_id,
        },
        headers=headers,
    )
    assert neg_res.status_code == 422

    # Valor zero deve ser rejeitado (422)
    zero_res = await client.post(
        "/api/v1/transactions/",
        json={
            "valor": 0.00,
            "tipo": "DESPESA",
            "data": "2026-08-15",
            "descricao": "Valor zero inválido",
            "conta_id": account_id,
        },
        headers=headers,
    )
    assert zero_res.status_code == 422


@pytest.mark.asyncio
async def test_reject_transaction_on_nonexistent_or_other_user_account(client: AsyncClient):
    # Usuário A
    await client.post("/api/v1/auth/register", json={"email": "userA_sec@example.com", "password": "password123"})
    login_A = await client.post("/api/v1/auth/login", json={"email": "userA_sec@example.com", "password": "password123"})
    headers_A = {"Authorization": f"Bearer {login_A.json()['access_token']}"}

    # Usuário B
    await client.post("/api/v1/auth/register", json={"email": "userB_sec@example.com", "password": "password123"})
    login_B = await client.post("/api/v1/auth/login", json={"email": "userB_sec@example.com", "password": "password123"})
    headers_B = {"Authorization": f"Bearer {login_B.json()['access_token']}"}

    # Usuário B cria conta
    acc_res_B = await client.post("/api/v1/accounts/", json={"apelido": "Conta do B"}, headers=headers_B)
    acc_id_B = acc_res_B.json()["id"]

    # 1. Usuário A tenta criar transação na conta de B -> 404
    cross_res = await client.post(
        "/api/v1/transactions/",
        json={
            "valor": 100.00,
            "tipo": "RECEITA",
            "data": "2026-08-15",
            "descricao": "Tentativa indevida",
            "conta_id": acc_id_B,
        },
        headers=headers_A,
    )
    assert cross_res.status_code == 404

    # 2. Usuário A tenta criar transação em conta inexistente (UUID aleatório) -> 404
    non_existent_uuid = str(uuid.uuid4())
    fake_res = await client.post(
        "/api/v1/transactions/",
        json={
            "valor": 100.00,
            "tipo": "RECEITA",
            "data": "2026-08-15",
            "descricao": "Conta não existe",
            "conta_id": non_existent_uuid,
        },
        headers=headers_A,
    )
    assert fake_res.status_code == 404


@pytest.mark.asyncio
async def test_dynamic_balance_calculation(client: AsyncClient):
    # Usuário
    await client.post("/api/v1/auth/register", json={"email": "user_saldo@example.com", "password": "password123"})
    login_res = await client.post("/api/v1/auth/login", json={"email": "user_saldo@example.com", "password": "password123"})
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # Criar conta: saldo inicial deve ser 0.00
    acc_res = await client.post("/api/v1/accounts/", json={"apelido": "C6 Bank"}, headers=headers)
    account_id = acc_res.json()["id"]
    assert Decimal(str(acc_res.json()["saldo_calculado"])) == Decimal("0.00")

    # Adicionar RECEITA: +1000.00
    await client.post(
        "/api/v1/transactions/",
        json={"valor": 1000.00, "tipo": "RECEITA", "data": "2026-08-10", "descricao": "Depósito", "conta_id": account_id},
        headers=headers,
    )

    # Consultar conta via GET /accounts/{id} e via listagem
    acc_get = await client.get(f"/api/v1/accounts/{account_id}", headers=headers)
    assert Decimal(str(acc_get.json()["saldo_calculado"])) == Decimal("1000.00")

    # Adicionar DESPESA: -350.50 -> Saldo esperado: 649.50
    desp1 = await client.post(
        "/api/v1/transactions/",
        json={"valor": 350.50, "tipo": "DESPESA", "data": "2026-08-11", "descricao": "Conta de Luz", "conta_id": account_id},
        headers=headers,
    )
    desp1_id = desp1.json()["id"]

    acc_get2 = await client.get(f"/api/v1/accounts/{account_id}", headers=headers)
    assert Decimal(str(acc_get2.json()["saldo_calculado"])) == Decimal("649.50")

    # Adicionar outra DESPESA: -49.50 -> Saldo esperado: 600.00
    await client.post(
        "/api/v1/transactions/",
        json={"valor": 49.50, "tipo": "DESPESA", "data": "2026-08-12", "descricao": "Almoço", "conta_id": account_id},
        headers=headers,
    )

    list_acc = await client.get("/api/v1/accounts/", headers=headers)
    assert Decimal(str(list_acc.json()[0]["saldo_calculado"])) == Decimal("600.00")

    # Deletar uma despesa de 350.50 -> Saldo deve recalcular dinamicamente para 950.50
    del_res = await client.delete(f"/api/v1/transactions/{desp1_id}", headers=headers)
    assert del_res.status_code == 204

    acc_after_del = await client.get(f"/api/v1/accounts/{account_id}", headers=headers)
    assert Decimal(str(acc_after_del.json()["saldo_calculado"])) == Decimal("950.50")


@pytest.mark.asyncio
async def test_filter_transactions(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={"email": "user_filter@example.com", "password": "password123"})
    login_res = await client.post("/api/v1/auth/login", json={"email": "user_filter@example.com", "password": "password123"})
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # Criar duas contas
    acc1 = (await client.post("/api/v1/accounts/", json={"apelido": "Conta 1"}, headers=headers)).json()
    acc2 = (await client.post("/api/v1/accounts/", json={"apelido": "Conta 2"}, headers=headers)).json()

    # Transação 1: Julho 2026 na Conta 1
    await client.post(
        "/api/v1/transactions/",
        json={"valor": 100.00, "tipo": "RECEITA", "data": "2026-07-20", "descricao": "Julho Conta 1", "conta_id": acc1["id"]},
        headers=headers,
    )

    # Transação 2: Agosto 2026 na Conta 1
    await client.post(
        "/api/v1/transactions/",
        json={"valor": 200.00, "tipo": "DESPESA", "data": "2026-08-10", "descricao": "Agosto Conta 1", "conta_id": acc1["id"]},
        headers=headers,
    )

    # Transação 3: Agosto 2026 na Conta 2
    await client.post(
        "/api/v1/transactions/",
        json={"valor": 300.00, "tipo": "DESPESA", "data": "2026-08-15", "descricao": "Agosto Conta 2", "conta_id": acc2["id"]},
        headers=headers,
    )

    # 1. Filtro por mês = 7
    res_mes_7 = await client.get("/api/v1/transactions/?mes=7", headers=headers)
    assert len(res_mes_7.json()) == 1
    assert res_mes_7.json()[0]["descricao"] == "Julho Conta 1"

    # 2. Filtro por mês = 8
    res_mes_8 = await client.get("/api/v1/transactions/?mes=8", headers=headers)
    assert len(res_mes_8.json()) == 2

    # 3. Filtro por conta = acc2["id"]
    res_acc2 = await client.get(f"/api/v1/transactions/?conta_id={acc2['id']}", headers=headers)
    assert len(res_acc2.json()) == 1
    assert res_acc2.json()[0]["descricao"] == "Agosto Conta 2"

    # 4. Filtro combinado: mês = 8, ano = 2026 e conta = acc1["id"]
    res_comb = await client.get(f"/api/v1/transactions/?mes=8&ano=2026&conta_id={acc1['id']}", headers=headers)
    assert len(res_comb.json()) == 1
    assert res_comb.json()[0]["descricao"] == "Agosto Conta 1"


@pytest.mark.asyncio
async def test_recurrence_and_future_transactions(client: AsyncClient):
    from datetime import date, timedelta
    today = date.today()
    future_date = (today + timedelta(days=15)).isoformat()
    past_date = (today - timedelta(days=5)).isoformat()

    # Cadastro e Login
    await client.post("/api/v1/auth/register", json={"email": "user_rec@example.com", "password": "password123"})
    login_res = await client.post("/api/v1/auth/login", json={"email": "user_rec@example.com", "password": "password123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    acc_res = await client.post("/api/v1/accounts/", json={"apelido": "NuConta"}, headers=headers)
    account_id = acc_res.json()["id"]

    # 1. Transação no futuro com recorrência MENSAL -> Status AGENDADA
    fut_res = await client.post(
        "/api/v1/transactions/",
        json={
            "valor": 1200.00,
            "tipo": "DESPESA",
            "data": future_date,
            "descricao": "Aluguel Futuro",
            "conta_id": account_id,
            "recorrencia": "MENSAL",
        },
        headers=headers,
    )
    assert fut_res.status_code == 201
    fut_data = fut_res.json()
    assert fut_data["recorrencia"] == "MENSAL"
    assert fut_data["status"] == "AGENDADA"

    # 2. Transação no passado sem especificar recorrência -> Default UNICA, Status EFETIVADA
    past_res = await client.post(
        "/api/v1/transactions/",
        json={
            "valor": 80.00,
            "tipo": "DESPESA",
            "data": past_date,
            "descricao": "Jantar Passado",
            "conta_id": account_id,
        },
        headers=headers,
    )
    assert past_res.status_code == 201
    past_data = past_res.json()
    assert past_data["recorrencia"] == "UNICA"
    assert past_data["status"] == "EFETIVADA"


@pytest.mark.asyncio
async def test_future_transactions_do_not_impact_current_account_balance(client: AsyncClient):
    from datetime import date, timedelta
    today = date.today()
    today_str = today.isoformat()
    future_str = (today + timedelta(days=20)).isoformat()

    # Cadastro e Login
    await client.post("/api/v1/auth/register", json={"email": "user_bal_crit@example.com", "password": "password123"})
    login_res = await client.post("/api/v1/auth/login", json={"email": "user_bal_crit@example.com", "password": "password123"})
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # Criar Conta
    acc_res = await client.post("/api/v1/accounts/", json={"apelido": "Carteira Principal"}, headers=headers)
    account_id = acc_res.json()["id"]

    # 1. Receita EFETIVADA hoje: +1500.00 -> Saldo: 1500.00
    await client.post(
        "/api/v1/transactions/",
        json={"valor": 1500.00, "tipo": "RECEITA", "data": today_str, "descricao": "Salário", "conta_id": account_id},
        headers=headers,
    )
    acc_check = await client.get(f"/api/v1/accounts/{account_id}", headers=headers)
    assert Decimal(str(acc_check.json()["saldo_calculado"])) == Decimal("1500.00")

    # 2. Despesa AGENDADA no futuro: -600.00 -> Saldo ATUAL NÃO DEVE MUDAR (deve continuar 1500.00)
    await client.post(
        "/api/v1/transactions/",
        json={"valor": 600.00, "tipo": "DESPESA", "data": future_str, "descricao": "Boleto Futuro", "conta_id": account_id},
        headers=headers,
    )
    acc_check2 = await client.get(f"/api/v1/accounts/{account_id}", headers=headers)
    assert Decimal(str(acc_check2.json()["saldo_calculado"])) == Decimal("1500.00")

    # 3. Receita AGENDADA no futuro: +3000.00 -> Saldo ATUAL NÃO DEVE MUDAR (deve continuar 1500.00)
    await client.post(
        "/api/v1/transactions/",
        json={"valor": 3000.00, "tipo": "RECEITA", "data": future_str, "descricao": "Bônus Futuro", "conta_id": account_id},
        headers=headers,
    )
    acc_check3 = await client.get(f"/api/v1/accounts/{account_id}", headers=headers)
    assert Decimal(str(acc_check3.json()["saldo_calculado"])) == Decimal("1500.00")

    # Listagem de contas também deve manter 1500.00
    acc_list = await client.get("/api/v1/accounts/", headers=headers)
    assert Decimal(str(acc_list.json()[0]["saldo_calculado"])) == Decimal("1500.00")


@pytest.mark.asyncio
async def test_filter_transactions_by_status(client: AsyncClient):
    from datetime import date, timedelta
    today = date.today()
    past_date = (today - timedelta(days=3)).isoformat()
    future_date = (today + timedelta(days=10)).isoformat()

    await client.post("/api/v1/auth/register", json={"email": "user_status_filt@example.com", "password": "password123"})
    login_res = await client.post("/api/v1/auth/login", json={"email": "user_status_filt@example.com", "password": "password123"})
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    acc_res = await client.post("/api/v1/accounts/", json={"apelido": "Conta Filtro Status"}, headers=headers)
    account_id = acc_res.json()["id"]

    # Transação passada
    await client.post(
        "/api/v1/transactions/",
        json={"valor": 100.00, "tipo": "DESPESA", "data": past_date, "descricao": "Compra Passada", "conta_id": account_id},
        headers=headers,
    )
    # Transação futura
    await client.post(
        "/api/v1/transactions/",
        json={"valor": 200.00, "tipo": "DESPESA", "data": future_date, "descricao": "Compra Futura", "conta_id": account_id},
        headers=headers,
    )

    # 1. Filtro status=EFETIVADA
    res_efet = await client.get("/api/v1/transactions/?status=EFETIVADA", headers=headers)
    assert res_efet.status_code == 200
    assert len(res_efet.json()) == 1
    assert res_efet.json()[0]["descricao"] == "Compra Passada"
    assert res_efet.json()[0]["status"] == "EFETIVADA"

    # 2. Filtro status=AGENDADA
    res_agen = await client.get("/api/v1/transactions/?status=AGENDADA", headers=headers)
    assert res_agen.status_code == 200
    assert len(res_agen.json()) == 1
    assert res_agen.json()[0]["descricao"] == "Compra Futura"
    assert res_agen.json()[0]["status"] == "AGENDADA"


@pytest.mark.asyncio
async def test_monthly_projections_endpoint(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={"email": "user_proj@example.com", "password": "password123"})
    login_res = await client.post("/api/v1/auth/login", json={"email": "user_proj@example.com", "password": "password123"})
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # Criar Contas
    acc1 = (await client.post("/api/v1/accounts/", json={"apelido": "Conta Proj 1"}, headers=headers)).json()
    acc2 = (await client.post("/api/v1/accounts/", json={"apelido": "Conta Proj 2"}, headers=headers)).json()

    # Mês de teste: Novembro de 2026 (mes=11, ano=2026)
    # Receita 1 em Conta 1: 5000.00
    await client.post(
        "/api/v1/transactions/",
        json={"valor": 5000.00, "tipo": "RECEITA", "data": "2026-11-05", "descricao": "Salário Novembro", "conta_id": acc1["id"]},
        headers=headers,
    )
    # Receita 2 em Conta 2: 1200.00
    await client.post(
        "/api/v1/transactions/",
        json={"valor": 1200.00, "tipo": "RECEITA", "data": "2026-11-10", "descricao": "Freelance Novembro", "conta_id": acc2["id"]},
        headers=headers,
    )
    # Despesa 1 em Conta 1: 2000.00
    await client.post(
        "/api/v1/transactions/",
        json={"valor": 2000.00, "tipo": "DESPESA", "data": "2026-11-12", "descricao": "Aluguel Novembro", "conta_id": acc1["id"]},
        headers=headers,
    )
    # Despesa 2 em Conta 2: 450.50
    await client.post(
        "/api/v1/transactions/",
        json={"valor": 450.50, "tipo": "DESPESA", "data": "2026-11-20", "descricao": "Contas Novembro", "conta_id": acc2["id"]},
        headers=headers,
    )

    # 1. Projeção Geral do Usuário para Novembro 2026 (todas as contas)
    proj_res = await client.get("/api/v1/transactions/projections?mes=11&ano=2026", headers=headers)
    assert proj_res.status_code == 200
    data = proj_res.json()
    assert data["mes"] == 11
    assert data["ano"] == 2026
    assert data["conta_id"] is None
    # Receitas: 5000 + 1200 = 6200.00
    assert Decimal(str(data["receitas_previstas"])) == Decimal("6200.00")
    # Despesas: 2000 + 450.50 = 2450.50
    assert Decimal(str(data["despesas_previstas"])) == Decimal("2450.50")
    # Saldo Projetado: 6200 - 2450.50 = 3749.50
    assert Decimal(str(data["saldo_projetado"])) == Decimal("3749.50")

    # 2. Projeção Filtrada apenas para Conta 1
    proj_acc1 = await client.get(f"/api/v1/transactions/projections?mes=11&ano=2026&conta_id={acc1['id']}", headers=headers)
    assert proj_acc1.status_code == 200
    data_acc1 = proj_acc1.json()
    assert data_acc1["conta_id"] == acc1["id"]
    assert Decimal(str(data_acc1["receitas_previstas"])) == Decimal("5000.00")
    assert Decimal(str(data_acc1["despesas_previstas"])) == Decimal("2000.00")
    assert Decimal(str(data_acc1["saldo_projetado"])) == Decimal("3000.00")

    # 3. Projeção para mês sem transações (ex: Dezembro 2026) -> Valores zerados
    proj_empty = await client.get("/api/v1/transactions/projections?mes=12&ano=2026", headers=headers)
    assert proj_empty.status_code == 200
    data_empty = proj_empty.json()
    assert Decimal(str(data_empty["receitas_previstas"])) == Decimal("0.00")
    assert Decimal(str(data_empty["despesas_previstas"])) == Decimal("0.00")
    assert Decimal(str(data_empty["saldo_projetado"])) == Decimal("0.00")

