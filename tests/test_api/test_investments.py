from decimal import Decimal
import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_get_investment(client: AsyncClient):
    # 1. Cadastro e Login
    await client.post("/api/v1/auth/register", json={"email": "inv_user1@example.com", "password": "password123"})
    login_res = await client.post("/api/v1/auth/login", json={"email": "inv_user1@example.com", "password": "password123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Criar Ativo de Ação
    payload = {
        "ticker": "petr4",  # deve converter para uppercase
        "nome": "Petrobras PN",
        "classe": "ACOES",
        "quantidade": 100,
        "preco_medio": 30.00,
        "cotacao_atual": 36.00,
    }
    create_res = await client.post("/api/v1/investments/", json=payload, headers=headers)
    assert create_res.status_code == 201
    data = create_res.json()
    assert data["ticker"] == "PETR4"
    assert data["classe"] == "ACOES"
    assert Decimal(str(data["quantidade"])) == Decimal("100")
    assert Decimal(str(data["preco_medio"])) == Decimal("30.00")
    assert Decimal(str(data["cotacao_atual"])) == Decimal("36.00")
    assert Decimal(str(data["total_investido"])) == Decimal("3000.00")
    assert Decimal(str(data["patrimonio_atual"])) == Decimal("3600.00")
    assert Decimal(str(data["lucro_prejuizo_absoluto"])) == Decimal("600.00")
    assert Decimal(str(data["rentabilidade_percentual"])) == Decimal("20.00")

    inv_id = data["id"]

    # 3. Consultar por ID
    get_res = await client.get(f"/api/v1/investments/{inv_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == inv_id


@pytest.mark.asyncio
async def test_create_renda_emergencial_and_cripto_fractional(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={"email": "inv_user2@example.com", "password": "password123"})
    login_res = await client.post("/api/v1/auth/login", json={"email": "inv_user2@example.com", "password": "password123"})
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # 1. Renda Emergencial
    reserva_res = await client.post(
        "/api/v1/investments/",
        json={
            "ticker": "RESERVA-NUBANK",
            "nome": "Reserva de Emergência Caixinha",
            "classe": "RENDA_EMERGENCIAL",
            "quantidade": 1,
            "preco_medio": 10000.00,
            "cotacao_atual": 10250.00,
        },
        headers=headers,
    )
    assert reserva_res.status_code == 201
    assert reserva_res.json()["classe"] == "RENDA_EMERGENCIAL"

    # 2. Cripto com quantidade fracionária (ex: 0.00452300 BTC)
    cripto_res = await client.post(
        "/api/v1/investments/",
        json={
            "ticker": "BTC",
            "nome": "Bitcoin",
            "classe": "CRIPTO",
            "quantidade": 0.05,
            "preco_medio": 300000.00,
            "cotacao_atual": 360000.00,
        },
        headers=headers,
    )
    assert cripto_res.status_code == 201
    c_data = cripto_res.json()
    assert Decimal(str(c_data["total_investido"])) == Decimal("15000.00")
    assert Decimal(str(c_data["patrimonio_atual"])) == Decimal("18000.00")
    assert Decimal(str(c_data["lucro_prejuizo_absoluto"])) == Decimal("3000.00")
    assert Decimal(str(c_data["rentabilidade_percentual"])) == Decimal("20.00")


@pytest.mark.asyncio
async def test_reject_invalid_investment_class_enum(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={"email": "inv_user3@example.com", "password": "password123"})
    login_res = await client.post("/api/v1/auth/login", json={"email": "inv_user3@example.com", "password": "password123"})
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # Classe inválida deve ser rejeitada com 422
    res = await client.post(
        "/api/v1/investments/",
        json={
            "ticker": "XYZ",
            "nome": "Classe Invalida",
            "classe": "POUPANCA_INVALIDA",
            "quantidade": 10,
            "preco_medio": 10.0,
            "cotacao_atual": 10.0,
        },
        headers=headers,
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_filter_investments_by_class_and_crud(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={"email": "inv_user4@example.com", "password": "password123"})
    login_res = await client.post("/api/v1/auth/login", json={"email": "inv_user4@example.com", "password": "password123"})
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # Criar 1 Ação e 1 FII
    inv1 = (await client.post(
        "/api/v1/investments/",
        json={"ticker": "VALE3", "nome": "Vale ON", "classe": "ACOES", "quantidade": 50, "preco_medio": 60, "cotacao_atual": 65},
        headers=headers,
    )).json()

    await client.post(
        "/api/v1/investments/",
        json={"ticker": "HGLG11", "nome": "CSHG Logística", "classe": "FIIS", "quantidade": 10, "preco_medio": 160, "cotacao_atual": 165},
        headers=headers,
    )

    # 1. Listar todas
    all_res = await client.get("/api/v1/investments/", headers=headers)
    assert len(all_res.json()) == 2

    # 2. Filtrar por classe ACOES
    acoes_res = await client.get("/api/v1/investments/?classe=ACOES", headers=headers)
    assert len(acoes_res.json()) == 1
    assert acoes_res.json()[0]["ticker"] == "VALE3"

    # 3. Atualizar cotação do ativo
    update_res = await client.put(
        f"/api/v1/investments/{inv1['id']}",
        json={"cotacao_atual": 70.00},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert Decimal(str(update_res.json()["cotacao_atual"])) == Decimal("70.00")

    # 4. Deletar ativo
    del_res = await client.delete(f"/api/v1/investments/{inv1['id']}", headers=headers)
    assert del_res.status_code == 204

    # Confirma deleção
    get_del = await client.get(f"/api/v1/investments/{inv1['id']}", headers=headers)
    assert get_del.status_code == 404


@pytest.mark.asyncio
async def test_portfolio_summary_and_zero_division_guard(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={"email": "inv_user5@example.com", "password": "password123"})
    login_res = await client.post("/api/v1/auth/login", json={"email": "inv_user5@example.com", "password": "password123"})
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # 1. Summary de portfólio vazio -> Valores zerados e sem divisão por zero
    empty_summary = await client.get("/api/v1/investments/summary", headers=headers)
    assert empty_summary.status_code == 200
    empty_data = empty_summary.json()
    assert Decimal(str(empty_data["patrimonio_total"])) == Decimal("0.00")
    assert Decimal(str(empty_data["total_investido"])) == Decimal("0.00")
    assert Decimal(str(empty_data["lucro_prejuizo_absoluto"])) == Decimal("0.00")
    assert Decimal(str(empty_data["rentabilidade_percentual"])) == Decimal("0.00")
    assert empty_data["alocacao_por_classe"] == []

    # 2. Adicionar Ativo A: Ações (100 cotas a R$ 20.00 custo, R$ 25.00 cotação)
    # Total Investido: 2000.00, Patrimônio: 2500.00, Lucro: 500.00 (+25%)
    await client.post(
        "/api/v1/investments/",
        json={"ticker": "ITUB4", "nome": "Itaú PN", "classe": "ACOES", "quantidade": 100, "preco_medio": 20.0, "cotacao_atual": 25.0},
        headers=headers,
    )

    # 3. Adicionar Ativo B: Renda Emergencial (1 cota a R$ 2500.00 custo, R$ 2500.00 cotação)
    # Total Investido: 2500.00, Patrimônio: 2500.00, Lucro: 0.00 (0%)
    await client.post(
        "/api/v1/investments/",
        json={"ticker": "RESERVA", "nome": "CDB Reserva", "classe": "RENDA_EMERGENCIAL", "quantidade": 1, "preco_medio": 2500.0, "cotacao_atual": 2500.0},
        headers=headers,
    )

    # Totais consolidados:
    # Patrimônio Total = 2500 + 2500 = 5000.00
    # Total Investido = 2000 + 2500 = 4500.00
    # Lucro Absoluto = 500.00
    # Rentabilidade = (500 / 4500) * 100 = 11.11%
    # Alocação ACOES: 2500 / 5000 = 50.00%
    # Alocação RENDA_EMERGENCIAL: 2500 / 5000 = 50.00%
    summary_res = await client.get("/api/v1/investments/summary", headers=headers)
    assert summary_res.status_code == 200
    data = summary_res.json()

    assert Decimal(str(data["patrimonio_total"])) == Decimal("5000.00")
    assert Decimal(str(data["total_investido"])) == Decimal("4500.00")
    assert Decimal(str(data["lucro_prejuizo_absoluto"])) == Decimal("500.00")
    assert Decimal(str(data["rentabilidade_percentual"])) == Decimal("11.11")
    assert len(data["alocacao_por_classe"]) == 2

    classes_map = {item["classe"]: item for item in data["alocacao_por_classe"]}
    assert Decimal(str(classes_map["ACOES"]["percentual_carteira"])) == Decimal("50.00")
    assert Decimal(str(classes_map["RENDA_EMERGENCIAL"]["percentual_carteira"])) == Decimal("50.00")
