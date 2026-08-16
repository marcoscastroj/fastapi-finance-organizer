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
