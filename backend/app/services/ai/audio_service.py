"""Ses teşhis servisi.

ÖNEMLİ: Whisper/transkripsiyon KULLANILMAZ — motor sesi transkribe edilemez.
Kullanıcının tarifi + kayıt koşulu + araç verisi ile Claude METİN analizi yapılır.
"""

from __future__ import annotations

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from ...config import get_settings
from ...domain.ai_errors import AIUpstreamError
from ...domain.enums import AIKind
from ...domain.models import AISession, User, Vehicle
from ...domain.safety import enforce_sound_safety
from ...domain.schemas import SoundDiagnoseRequest, SoundDiagnoseResponse
from .claude_client import ClaudeClient
from .prompts import build_audio_prompt


async def diagnose_sound(
    *,
    db: AsyncSession,
    claude: ClaudeClient,
    user: User,
    vehicle: Vehicle,
    payload: SoundDiagnoseRequest,
) -> SoundDiagnoseResponse:
    settings = get_settings()
    model = settings.audio_model

    system = build_audio_prompt(vehicle)
    user_text = (
        f"Kayıt koşulu: {payload.condition.value}\n"
        f"Kullanıcı tarifi: {payload.user_description}"
    )

    result = await claude.complete_json(model=model, system=system, content=user_text)

    db.add(
        AISession(
            user_id=user.id,
            vehicle_id=vehicle.id,
            kind=AIKind.sound,
            model=model,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
        )
    )
    await db.commit()

    try:
        parsed = SoundDiagnoseResponse(**result.data)
    except ValidationError as exc:
        raise AIUpstreamError("AI yanıtı beklenen şemada değil.") from exc
    return enforce_sound_safety(parsed, context=payload.user_description)
