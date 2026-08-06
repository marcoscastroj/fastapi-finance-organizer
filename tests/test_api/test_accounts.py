import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_account(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={"email": "user@example.com", "password": "password123"})
    login_res = await client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "password123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.post("/api/v1/accounts/", json={"apelido": "Nubank"}, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["apelido"] == "Nubank"
    assert "id" in data
    assert "user_id" in data

@pytest.mark.asyncio
async def test_crud_accounts_isolation(client: AsyncClient):
    # Criar Usuário A
    await client.post("/api/v1/auth/register", json={"email": "userA@example.com", "password": "password123"})
    login_A = await client.post("/api/v1/auth/login", json={"email": "userA@example.com", "password": "password123"})
    headers_A = {"Authorization": f"Bearer {login_A.json()['access_token']}"}

    # Criar Usuário B
    await client.post("/api/v1/auth/register", json={"email": "userB@example.com", "password": "password123"})
    login_B = await client.post("/api/v1/auth/login", json={"email": "userB@example.com", "password": "password123"})
    headers_B = {"Authorization": f"Bearer {login_B.json()['access_token']}"}

    # Usuário A cria a conta "Carteira Física"
    create_res = await client.post("/api/v1/accounts/", json={"apelido": "Carteira Física"}, headers=headers_A)
    account_id = create_res.json()["id"]

    # 1. Usuário A lista sua conta
    list_res_A = await client.get("/api/v1/accounts/", headers=headers_A)
    assert len(list_res_A.json()) == 1

    # 2. Usuário B NÃO vê a conta de A
    list_res_B = await client.get("/api/v1/accounts/", headers=headers_B)
    assert len(list_res_B.json()) == 0

    # 3. Usuário B tenta acessar via ID -> 404
    get_b_res = await client.get(f"/api/v1/accounts/{account_id}", headers=headers_B)
    assert get_b_res.status_code == 404

    # 4. Usuário A atualiza a conta
    update_res = await client.put(f"/api/v1/accounts/{account_id}", json={"apelido": "Itaú"}, headers=headers_A)
    assert update_res.status_code == 200
    assert update_res.json()["apelido"] == "Itaú"

    # 5. Usuário A deleta a conta
    del_res = await client.delete(f"/api/v1/accounts/{account_id}", headers=headers_A)
    assert del_res.status_code == 204

    # 6. Confirmar deleção
    get_deleted = await client.get(f"/api/v1/accounts/{account_id}", headers=headers_A)
    assert get_deleted.status_code == 404