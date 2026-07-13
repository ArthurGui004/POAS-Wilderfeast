import bcrypt
import jwt
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta, timezone
from app.config import settings


def hash_password(password: str) -> str:
    # O bcrypt exige bytes, então codificamos a senha
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    # Decodificamos para string para salvar facilmente no banco de dados
    return hashed_password.decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    # Ambas as strings precisam virar bytes para a comparação
    password_bytes = plain.encode('utf-8')
    hash_bytes = hashed.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hash_bytes)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    # A sintaxe do encode no PyJWT é idêntica à do python-jose
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        # A sintaxe do decode também é idêntica
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except InvalidTokenError:
        # Capturamos o erro específico do PyJWT agora
        return None
