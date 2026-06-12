"""Görüntü teşhis servisi.

Akış: prompt oluştur -> Claude (sonnet) çağır -> şemaya doğrula ->
güvenlik kurallarını zorla -> token logla -> yanıt döndür.
"""

from __future__ import annotations

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from ...config import get_settings
from ...domain.ai_errors import AIUpstreamError
from ...domain.enums import AIKind
from ...domain.models import AISession, User, Vehicle
from ...domain.safety import enforce_image_safety
from ...domain.schemas import ImageDiagnoseRequest, ImageDiagnoseResponse
from ...domain.taxonomy import sistem_for_task
from .claude_client import ClaudeClient
from .cost import build_cost_estimate
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

    # Token + teşhis özeti loglama (maliyet denetimi + "Teşhis Geçmişi").
    session = AISession(
        user_id=user.id,
        vehicle_id=vehicle.id,
        kind=AIKind.image,
        model=model,
        tokens_in=result.tokens_in,
        tokens_out=result.tokens_out,
        task=payload.task,
    )

    try:
        parsed = ImageDiagnoseResponse(**result.data)
    except ValidationError as exc:
        # Şema bozuk olsa da token maliyetini kaybetme.
        db.add(session)
        await db.commit()
        raise AIUpstreamError("AI yanıtı beklenen şemada değil.") from exc

    final = enforce_image_safety(parsed, context=payload.user_note or "")
    # Özet, güvenlik kuralları zorlandıktan SONRAKİ metinden yazılır.
    session.tespit = final.tespit[:500]
    session.guven = final.guven.value
    session.tamirciye_git = final.tamirciye_git_onerisi
    session.kategori = payload.task  # görüntüde kategori = görev id'si
    session.ariza_sistem = sistem_for_task(payload.task).value
    db.add(session)
    await db.commit()
    await db.refresh(session)
    # Fiyat şeffaflığı: tamirciye tahmini maliyet (arıza sistemine göre).
    cost = await build_cost_estimate(db, session.ariza_sistem, vehicle.vehicle_type)
    # 👍/👎 geri bildirimi bu id'ye bağlanır.
    return final.model_copy(update={"session_id": session.id, "cost_estimate": cost})
