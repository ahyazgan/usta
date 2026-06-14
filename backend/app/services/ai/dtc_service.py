"""Arıza kodu (OBD-II / DTC) açıklama servisi.

Girdi: kullanıcının yazdığı kod (örn. P0300) + araç verisi → Claude METİN analizi.
Görüntü/ses yok. AISession'a kind=sound (metin tabanlı), kategori='ariza_kodu'
olarak loglanır (token/maliyet denetimi + Teşhis Geçmişi).
"""

from __future__ import annotations

import re

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from ...config import get_settings
from ...domain.ai_errors import AIUpstreamError
from ...domain.enums import AIKind
from ...domain.models import AISession, User, Vehicle
from ...domain.safety import enforce_dtc_safety
from ...domain.schemas import DtcDiagnoseRequest, DtcDiagnoseResponse
from .claude_client import ClaudeClient
from .prompts import build_dtc_prompt

DTC_KATEGORI = "ariza_kodu"
DTC_SISTEM = "diger"


def _normalize_code(code: str) -> str:
    """Kullanıcı girdisini sadeleştir: boşlukları at, büyük harfe çevir."""
    return re.sub(r"\s+", "", code).upper()


async def diagnose_dtc(
    *,
    db: AsyncSession,
    claude: ClaudeClient,
    user: User,
    vehicle: Vehicle,
    payload: DtcDiagnoseRequest,
) -> DtcDiagnoseResponse:
    settings = get_settings()
    model = settings.audio_model  # metin analizi — sonnet (Opus yasak)

    system = build_dtc_prompt(vehicle)
    code = _normalize_code(payload.code)
    user_text = f"Arıza kodu: {code}"
    if payload.user_note:
        user_text += f"\nKullanıcı notu: {payload.user_note}"

    result = await claude.complete_json(model=model, system=system, content=user_text)

    session = AISession(
        user_id=user.id,
        vehicle_id=vehicle.id,
        kind=AIKind.sound,  # metin tabanlı (görüntü değil)
        model=model,
        tokens_in=result.tokens_in,
        tokens_out=result.tokens_out,
        task=DTC_KATEGORI,
    )

    try:
        parsed = DtcDiagnoseResponse(**result.data)
    except ValidationError as exc:
        # Şema bozuk olsa da token maliyetini kaybetme.
        db.add(session)
        await db.commit()
        raise AIUpstreamError("AI yanıtı beklenen şemada değil.") from exc

    final = enforce_dtc_safety(parsed, context=payload.user_note or "")
    session.tespit = final.tespit[:500]
    session.guven = final.guven.value
    session.tamirciye_git = final.tamirciye_git_onerisi
    session.kategori = DTC_KATEGORI
    session.ariza_sistem = DTC_SISTEM
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return final.model_copy(update={"session_id": session.id})
