"""Görüntü teşhis servisi.

Akış: prompt oluştur -> Claude (sonnet) çağır -> şemaya doğrula ->
güvenlik kurallarını zorla -> token logla -> yanıt döndür.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ...config import get_settings
from ...domain.enums import AIKind
from ...domain.models import AISession, User, Vehicle
from ...domain.safety import enforce_image_safety
from ...domain.schemas import ImageDiagnoseRequest, ImageDiagnoseResponse
from .claude_client import ClaudeClient
from .prompts import build_vision_prompt


async def diagnose_image(
    *,
    db: AsyncSession,
    claude: ClaudeClient,
    user: User,
    vehicle: Vehicle,
    payload: ImageDiagnoseRequest,
) -> ImageDiagnoseResponse:
    settings = get_settings()
    # MALİYET KURALI: vision modeli Opus OLAMAZ.
    model = settings.vision_model
    assert "opus" not in model.lower(), "Vision için Opus modeli yasak."

    system = build_vision_prompt(vehicle, payload.task, payload.step)
    content: list[dict] = [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": payload.media_type,
                "data": payload.frame_base64,
            },
        },
        {"type": "text", "text": payload.user_note or "Doğru yerde miyim? Kontrol et."},
    ]

    result = await claude.complete_json(model=model, system=system, content=content)

    # Token loglama (maliyet denetimi).
    db.add(
        AISession(
            user_id=user.id,
            vehicle_id=vehicle.id,
            kind=AIKind.image,
            model=model,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
        )
    )
    await db.commit()

    parsed = ImageDiagnoseResponse(**result.data)
    return enforce_image_safety(parsed, context=payload.user_note or "")
