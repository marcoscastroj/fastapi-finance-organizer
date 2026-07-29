from unittest.mock import AsyncMock, MagicMock
import pytest
import uuid
from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.user_service import authenticate_user, create_user, get_user_by_email, delete_user

@pytest.mark.asyncio
async def test_get_user_by_email_found():
    """Garante que get_user_by_email retorna o usuário quando encontrado no banco."""
    mock_db = AsyncMock()
    mock_user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password="hashed_pwd_123"
    )

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_user
    mock_db.execute.return_value = mock_result

    user = await get_user_by_email(mock_db, email="test@example.com")

    assert user is not None
    assert user.email == "test@example.com"
    mock_db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_get_user_by_email_not_found():
    """Garante que get_user_by_email retorna None quando o e-mail não existe."""
    mock_db = AsyncMock()

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result

    user = await get_user_by_email(mock_db, email="inexistente@example.com")

    assert user is None
    mock_db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_create_user_service():
    """Garante que create_user realiza a criptografia da senha e grava no banco via AsyncSession."""
    mock_db = AsyncMock()
    user_in = UserCreate(email="novo@example.com", password="senhaSegura123")

    new_user = await create_user(mock_db, user_in=user_in)

    assert new_user.email == "novo@example.com"
    assert new_user.hashed_password != "senhaSegura123"  # Deve ter sido feito o hash

    # Verifica se os métodos de persistência do SQLAlchemy foram chamados
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()
    mock_db.refresh.assert_awaited_once()

@pytest.mark.asyncio
async def test_authenticate_user_success():
    """Garante que a autenticação retorna o usuário caso a senha esteja correta."""
    mock_db = AsyncMock()
    raw_password = "senhaCorreta123"
    hashed_pwd = get_password_hash(raw_password)

    mock_user = User(
        id=uuid.uuid4(),
        email="auth@example.com",
        hashed_password=hashed_pwd
    )

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_user
    mock_db.execute.return_value = mock_result

    authenticated_user = await authenticate_user(
        mock_db, email="auth@example.com", password=raw_password
    )

    assert authenticated_user is not None
    assert authenticated_user.email == "auth@example.com"

@pytest.mark.asyncio
async def test_authenticate_user_wrong_password():
    """Garante que a autenticação retorna None se a senha estiver incorreta."""
    mock_db = AsyncMock()
    raw_password = "senhaCorreta123"
    wrong_password = "senhaErrada123"
    hashed_pwd = get_password_hash(raw_password)

    mock_user = User(
        id=uuid.uuid4(),
        email="auth@example.com",
        hashed_password=hashed_pwd
    )

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_user
    mock_db.execute.return_value = mock_result

    authenticated_user = await authenticate_user(
        mock_db, email="auth@example.com", password=wrong_password
    )

    assert authenticated_user is None

@pytest.mark.asyncio
async def test_authenticate_user_not_found():
    """Garante que a autenticação retorna None se o usuário não for encontrado."""
    mock_db = AsyncMock()

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result

    authenticated_user = await authenticate_user(
        mock_db, email="nao_existe@example.com", password="qualquer_senha"
    )

    assert authenticated_user is None

@pytest.mark.asyncio
async def test_delete_user_service():
    mock_db = AsyncMock()
    mock_user = User(
        id = uuid.uuid4(),
        email = "delete@example.com",
        hashed_password="hashed_pwd_123"
    )

    await delete_user(mock_db, user=mock_user)

    mock_db.delete.assert_called_once_with(mock_user)
    mock_db.commit.assert_awaited_once()