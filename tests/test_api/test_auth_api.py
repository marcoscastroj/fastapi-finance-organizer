import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient):
    """Garante que a rota POST /api/v1/auth/register cadastra um usuário com sucesso."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "novo.usuario@exemplo.com",
            "password": "senhaSegura123!"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "novo.usuario@exemplo.com"
    assert "id" in data
    assert data["is_active"] is True
    # Garante que a senha NUNCA é retornada no JSON
    assert "password" not in data
    assert "hashed_password" not in data

@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Garante que tentar cadastrar o mesmo e-mail duas vezes retorna 400 Bad Request."""
    user_payload = {
        "email": "duplicado@exemplo.com",
        "password": "senhaSegura123!"
    }

    # Primeiro cadastro (sucesso)
    res1 = await client.post("/api/v1/auth/register", json=user_payload)
    assert res1.status_code == 201

    # Segundo cadastro com o mesmo e-mail (deve falhar)
    res2 = await client.post("/api/v1/auth/register", json=user_payload)
    assert res2.status_code == 400
    assert res2.json()["detail"] == "Um usuário com este email já existe."

@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient):
    """Garante que enviar um e-mail com formato inválido dispara erro de validação (422)."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "email_invalido_sem_arroba",
            "password": "senhaSegura123!"
        }
    )

    assert response.status_code == 422

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Garante que o login com credenciais válidas retorna status 200 e um token JWT."""
    user_payload = {
        "email": "login.sucesso@exemplo.com",
        "password": "senhaSegura123!"
    }

    # Cadastra o usuário primeiro
    await client.post("/api/v1/auth/register", json=user_payload)

    # Realiza o login
    response = await client.post("/api/v1/auth/login", json=user_payload)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_incorrect_password(client: AsyncClient):
    """Garante que o login com senha errada retorna 401 Unauthorized."""
    # Cadastra com uma senha
    await client.post(
        "/api/v1/auth/register",
        json={"email": "usuario.senha@exemplo.com", "password": "senhaCorreta123"}
    )

    # Tenta logar com outra senha
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "usuario.senha@exemplo.com", "password": "senhaIncorreta123"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "E-mail ou senha incorretos."

@pytest.mark.asyncio
async def test_read_user_me_success(client: AsyncClient):
    """Garante que a rota protegida GET /api/v1/auth/me funciona ao enviar o token JWT."""
    user_payload = {
        "email": "perfil.me@exemplo.com",
        "password": "senhaSegura123!"
    }

    # 1. Cadastra
    await client.post("/api/v1/auth/register", json=user_payload)

    # 2. Loga para obter o token
    login_res = await client.post("/api/v1/auth/login", json=user_payload)
    token = login_res.json()["access_token"]

    # 3. Faz a chamada na rota protegida passando o token no cabeçalho Authorization
    headers = {"Authorization": f"Bearer {token}"}
    me_response = await client.get("/api/v1/auth/me", headers=headers)

    assert me_response.status_code == 200
    data = me_response.json()
    assert data["email"] == "perfil.me@exemplo.com"
    assert "id" in data

@pytest.mark.asyncio
async def test_read_user_me_unauthorized_no_token(client: AsyncClient):
    """Garante que chamar a rota /me sem o token retorna 401 Unauthorized."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_read_user_me_invalid_token(client: AsyncClient):
    """Garante que chamar a rota /me com um token forjado ou inválido retorna 401."""
    headers = {"Authorization": "Bearer token_falso_e_invalido_123"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_delete_user_me_success(client: AsyncClient):
    """Garante que DELETE /api/v1/auth/me remove a conta e invalida logins/acessos futuros."""
    user_payload = {
        "email": "deletar.conta@exemplo.com",
        "password": "senhaSegura123!"
    }

    # 1. Cadastra o usuário
    await client.post("/api/v1/auth/register", json=user_payload)

    # 2. Realiza o login para obter o token JWT
    login_res = await client.post("/api/v1/auth/login", json=user_payload)
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Solicita a exclusão da conta (deve retornar 204)
    delete_res = await client.delete("/api/v1/auth/me", headers=headers)
    assert delete_res.status_code == 204

    # 4. Tenta acessar /me novamente com o mesmo token (deve falhar com 401)
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 401

    # 5. Tenta logar novamente (deve falhar com 401 pois o usuário foi removido)
    login_fail_res = await client.post("/api/v1/auth/login", json=user_payload)
    assert login_fail_res.status_code == 401
    
@pytest.mark.asyncio
async def test_delete_user_me_unauthorized(client: AsyncClient):
    """Garante que tentar deletar a conta sem token de autenticação retorna 401 Unauthorized."""
    response = await client.delete("/api/v1/auth/me")
    assert response.status_code == 401