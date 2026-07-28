from datetime import timedelta
import jwt
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password

def test_hash_password():
    """Garante que a senha é criptografada e diferente do texto plano."""
    password = "minhaSenhaSuperSegura123"
    hashed = get_password_hash(password)

    assert hashed != password
    assert isinstance(hashed, str)

def test_verify_password_correct():
    """Garante que a verificação de senha retorna True para a senha correta."""
    password = "minhaSenhaSuperSegura123"
    hashed = get_password_hash(password)

    assert verify_password(password, hashed) is True

def test_verify_password_incorrect():
    """Garante que a verificação de senha retorna False para senha incorreta."""
    password = "minhaSenhaSuperSegura123"
    wrong_password = "senhaIncorreta"
    hashed = get_password_hash(password)

    assert verify_password(wrong_password, hashed) is False

def test_create_access_token():
    """Garante que o token JWT é gerado contendo o assunto (sub) e payload correto."""
    subject = "user_uuid_12345"
    token = create_access_token(subject=subject)

    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    assert payload.get("sub") == subject
    assert "exp" in payload