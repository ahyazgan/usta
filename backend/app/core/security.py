"""Parola hashleme (bcrypt 12) ve JWT / refresh token üretimi."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from ..config import get_settings

_settings = get_settings()


# --------------------------------------------------------------------------- #
# Parola
# --------------------------------------------------------------------------- #


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=_settings.bcrypt_rounds)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# --------------------------------------------------------------------------- #
# Access token (JWT)
# --------------------------------------------------------------------------- #


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=_settings.access_token_expire_minutes)).timestamp()),
    }
    return jwt.encode(payload, _settings.jwt_secret, algorithm=_settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Token'ı çöz; geçersizse jwt.PyJWTError fırlatır."""
    payload = jwt.decode(token, _settings.jwt_secret, algorithms=[_settings.jwt_algorithm])
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("token tipi access değil")
    return payload


# --------------------------------------------------------------------------- #
# Refresh token (rastgele; DB'de sha256 saklanır)
# --------------------------------------------------------------------------- #


def generate_refresh_token() -> tuple[str, str, datetime]:
    """(düz_token, sha256_hash, son_kullanma) döndürür."""
    raw = secrets.token_urlsafe(48)
    token_hash = hash_refresh_token(raw)
    expires_at = datetime.now(timezone.utc) + timedelta(days=_settings.refresh_token_expire_days)
    return raw, token_hash, expires_at


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
