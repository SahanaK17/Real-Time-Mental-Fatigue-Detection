"""
Security Utilities
==================
JWT token creation, validation, and password hashing.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union

import structlog
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

logger = structlog.get_logger(__name__)

# ── Password Hashing ─────────────────────────────────────
import bcrypt

# Workaround for passlib + bcrypt >= 4.0.0 compatibility bug
if not hasattr(bcrypt, "__about__"):
    class _About:
        __version__ = getattr(bcrypt, "__version__", "4.0.0")
    bcrypt.__about__ = _About()

# Workaround for passlib detect_wrap_bug raising ValueError in bcrypt >= 4.0.0
import passlib.handlers.bcrypt
passlib.handlers.bcrypt.detect_wrap_bug = lambda ident: False

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


# ── JWT Token Management ──────────────────────────────────
def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[dict] = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        subject: Token subject (usually user ID)
        expires_delta: Custom expiration. Defaults to settings value.
        extra_claims: Additional claims to embed (e.g., role, email)

    Returns:
        Encoded JWT string
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    payload = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),
        "type": "access",
    }

    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: Union[str, Any]) -> str:
    """
    Create a signed JWT refresh token with longer expiry.
    """
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),
        "type": "refresh",
    }

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token.

    Returns:
        Token payload dict, or None if invalid/expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError as e:
        logger.debug("JWT decode failed", error=str(e))
        return None


def verify_token(token: str) -> dict:
    """
    Decode and validate a JWT access token, raising JWTError on failure.
    Used by FastAPI dependency injection.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        raise


def decode_refresh_token(token: str) -> Optional[dict]:
    """Decode and validate a refresh token."""
    payload = decode_access_token(token)
    if payload and payload.get("type") != "refresh":
        return None
    return payload
