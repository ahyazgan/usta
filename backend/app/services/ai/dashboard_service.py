"""Gösterge paneli uyarı ışığı tanıma servisi.

Akış: pano prompt'u oluştur -> Claude (sonnet) çağır -> şemaya doğrula ->
güvenlik kurallarını zorla -> token logla -> yanıt döndür.

Görüntü teşhisinden farkı: 'doğru yer mi?' değil, panodaki YANAN uyarı ışıklarını
tanır ve aciliyet/yönlendirme verir. AISession'a kind=image, kategori='pano_uyari'
olarak loglanır (token/maliyet denetimi + Teşhis Geçmişi).
"""

from __future__ import annotations

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from ...config import get_settings
from ...domain.ai_errors import AIUpstreamError
from ...domain.enums import AIKind
from ...domain.models import AISession, User, Vehicle
from ...domain.safety import enforce_dashboard_safety
from ...domain.schemas import DashboardDiagnoseRequest, DashboardDiagnoseResponse
from .claude_client import ClaudeClient
from .prompts import build_dashboard_prompt

# Pano teşhisleri taksonomide tek bir kovaya düşmez; geçmiş/istatistik için işaret.
DASHBOARD_KATEGORI = "pano_uyari"
DASHBOARD_SISTEM = "diger"


async def diagnose_dashboard(
    *,
    db: AsyncSession,
    claude: ClaudeClient,
    user: User,
    vehicle: Vehicle,
    payload: DashboardDiagnoseRequest,
) -> DashboardDiagnoseResponse:
    settings = get_settings()
    # MALİYET KURALI: vision modeli Opus OLAMAZ.
    model = settings.vision_model
    assert "opus" not in model.lower(), "Vision için Opus modeli yasak."

    system = build_dashboard_prompt(vehicle)
    content: list[dict] = [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": payload.media_type,
                "data": payload.frame_base64,
            },
        },
        {
            "type": "text",
            "text": payload.user_note or "Gösterge panelimde yanan uyarı ışıkları neler?",
        },
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
        task=DASHBOARD_KATEGORI,
    )

    try:
        parsed = DashboardDiagnoseResponse(**result.data)
    except ValidationError as exc:
        # Şema bozuk olsa da token maliyetini kaybetme.
        db.add(session)
        await db.commit()
        raise AIUpstreamError("AI yanıtı beklenen şemada değil.") from exc

    final = enforce_dashboard_safety(parsed, context=payload.user_note or "")
    # Özet, güvenlik kuralları zorlandıktan SONRAKİ metinden yazılır.
    session.tespit = final.tespit[:500]
    session.guven = final.guven.value
    session.tamirciye_git = final.tamirciye_git_onerisi
    session.kategori = DASHBOARD_KATEGORI
    session.ariza_sistem = DASHBOARD_SISTEM
    db.add(session)
    await db.commit()
    await db.refresh(session)
    # 👍/👎 geri bildirimi bu id'ye bağlanır.
    return final.model_copy(update={"session_id": session.id})
