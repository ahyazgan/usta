"""Kimlik doğrulama iş mantığı: kayıt, giriş, token yenileme."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from ..domain.models import RefreshToken, User
from ..domain.schemas import TokenResponse


async def register(db: AsyncSession, email: str, password: str) -> User:
    existing = await db.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Bu e-posta zaten kayıtlı."
        )
    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _issue_tokens(db: AsyncSession, user: User) -> TokenResponse:
    raw_refresh, token_hash, expires_at = generate_refresh_token()
    db.add(RefreshToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at))
    await db.commit()
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=raw_refresh,
    )


async def login(db: AsyncSession, email: str, password: str) -> TokenResponse:
    user = await db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="E-posta veya parola hatalı."
        )
    return await _issue_tokens(db, user)


async def refresh(db: AsyncSession, raw_refresh: str) -> TokenResponse:
    token_hash = hash_refresh_token(raw_refresh)
    record = await db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    now = datetime.now(timezone.utc)
    expires_at = record.expires_at if record else None
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if record is None or record.revoked or expires_at is None or expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Yenileme token'ı geçersiz."
        )

    # Rotasyon: eski token'ı iptal et, yenisini ver.
    record.revoked = True
    user = await db.get(User, record.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Kullanıcı yok.")
    return await _issue_tokens(db, user)
