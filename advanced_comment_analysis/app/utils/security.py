import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from jose import jwt, JWTError
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

MIN_SECRET_LENGTH = 32
# Any other value of ENVIRONMENT counts as production, so a typo cannot relax the checks.
NON_PRODUCTION = {"", "development", "dev", "local", "test"}


def is_production() -> bool:
    return os.getenv("ENVIRONMENT", "").strip().lower() not in NON_PRODUCTION


def load_jwt_secret() -> str:
    """Return the signing secret. Production stops here without a real one, which stops the app."""
    secret = os.getenv("JWT_SECRET_KEY", "").strip()
    if len(secret) >= MIN_SECRET_LENGTH:
        return secret
    if is_production():
        raise RuntimeError(
            f"JWT_SECRET_KEY must be at least {MIN_SECRET_LENGTH} characters in production. "
            "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
        )
    logger.warning(
        "JWT_SECRET_KEY is missing or shorter than %s characters, so this run signs with a random "
        "secret and logins end when it stops. Set JWT_SECRET_KEY in .env to keep them.",
        MIN_SECRET_LENGTH,
    )
    return secrets.token_urlsafe(48)


JWT_SECRET_KEY = load_jwt_secret()
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError as e:
        raise
