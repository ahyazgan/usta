"""Belirti-bazlı serbest teşhis servisi.

Girdi: kullanıcının yazdığı belirti + araç verisi → Claude METİN analizi.
AI arıza sistemini de belirler → AISession.ariza_sistem + fiyat tahmini (çark).
AISession'a kind=sound (metin tabanlı), kategori='belirti' loglanır.
"""

from __future__ import annotations

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from ...config import get_settings
from ...domain.ai_errors import AIUpstreamError
from ...domain.enums import AIKind
from ...domain.models import AISession, User, Vehicle
from ...domain.safety import enforce_symptom_safety
from ...domain.schemas import SymptomDiagnoseRequest, SymptomDiagnoseResponse
from .claude_client import ClaudeClient
from .cost import build_cost_estimate
from .prompts import build_symptom_prompt

SYMPTOM_KATEGORI = "belirti"


async def diagnose_symptom(
    *,
    db: AsyncSession,
    claude: ClaudeClient,
    user: User,
    vehicle: Vehicle,
    payload: SymptomDiagnoseRequest,
) -> SymptomDiagnoseResponse:
    settings = get_settings()
    model = settings.audio_model  # metin analizi — sonnet (Opus yasak)

    system = build_symptom_prompt(vehicle)
    user_text = f"Belirti: {payload.description}"

    result = await claude.complete_json(model=model, system=system, content=user_text)

    session = AISession(
        user_id=user.id,
        vehicle_id=vehicle.id,
        kind=AIKind.sound,  # metin tabanlı (görüntü değil)
        model=model,
        tokens_in=result.tokens_in,
        tokens_out=result.tokens_out,
        task=SYMPTOM_KATEGORI,
    )

    try:
        parsed = SymptomDiagnoseResponse(**result.data)
    except ValidationError as exc:
        # Şema bozuk olsa da token maliyetini kaybetme.
        db.add(session)
        await db.commit()
        raise AIUpstreamError("AI yanıtı beklenen şemada değil.") from exc

    final = enforce_symptom_safety(parsed, context=payload.description)
    session.tespit = final.tespit[:500]
    session.guven = final.guven.value
    session.tamirciye_git = final.tamirciye_git_onerisi
    session.kategori = SYMPTOM_KATEGORI
    session.ariza_sistem = final.ariza_sistem.value
    db.add(session)
    await db.commit()
    await db.refresh(session)
    # Fiyat şeffaflığı: belirlenen sisteme göre tamirci maliyet tahmini.
    cost = await build_cost_estimate(db, session.ariza_sistem, vehicle.vehicle_type)
    return final.model_copy(update={"session_id": session.id, "cost_estimate": cost})
