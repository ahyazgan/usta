"""Canlı sesli rehber rotaları (Gemini Live). JWT + rate limit + sahiplik.

Mobil istemci buradan ephemeral token alır, sonra DOĞRUDAN Gemini'ye bağlanır
(medya akışı backend'den geçmez). Bitince süreyi /end ile bildirir.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..core.deps import get_current_user
from ..core.rate_limit import enforce_rate_limit
from ..database import get_db
from ..domain.models import User
from ..domain.schemas import LiveSessionEndIn, LiveSessionOut, LiveSessionRequest
from ..services import vehicle_service
from ..services.ai import live_session_service

router = APIRouter(prefix="/v1/live", tags=["live"], dependencies=[Depends(enforce_rate_limit)])


@router.post("/session", response_model=LiveSessionOut)
async def start_live_session(
    payload: LiveSessionRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> LiveSessionOut:
    """Canlı oturum başlat: ephemeral token + oturum bilgisi döndürür.

    Anahtar yoksa 503, aylık ücretsiz limit dolduysa 402 (premium hariç).
    system_instruction yanıtta YOKTUR (server-side kalır).
    """
    vehicle = await vehicle_service.get_owned(db, user.id, payload.vehicle_id)
    return await live_session_service.start_session(
        db,
        user=user,
        vehicle=vehicle,
        task=payload.task,
        lang=payload.lang,
        settings=get_settings(),
    )


@router.post("/session/{live_usage_id}/end", status_code=status.HTTP_204_NO_CONTENT)
async def end_live_session(
    live_usage_id: int,
    payload: LiveSessionEndIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    """Oturum süresini bildir (dakika sayacı + maliyet freni)."""
    await live_session_service.end_session(
        db,
        user=user,
        live_usage_id=live_usage_id,
        seconds=payload.seconds,
        settings=get_settings(),
    )
