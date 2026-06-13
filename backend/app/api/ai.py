"""AI teşhis rotaları: görüntü ve ses. JWT + rate limit + sahiplik (403)."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.deps import get_current_user
from ..core.rate_limit import enforce_rate_limit
from ..database import get_db
from ..domain.models import User
from ..domain.schemas import (
    DashboardDiagnoseRequest,
    DashboardDiagnoseResponse,
    DtcDiagnoseRequest,
    DtcDiagnoseResponse,
    ImageDiagnoseRequest,
    ImageDiagnoseResponse,
    SoundDiagnoseRequest,
    SoundDiagnoseResponse,
)
from ..services import vehicle_service
from ..services.ai import audio_service, dashboard_service, dtc_service, vision_service
from ..services.ai.claude_client import ClaudeClient, get_claude_client

router = APIRouter(
    prefix="/v1/ai",
    tags=["ai"],
    dependencies=[Depends(enforce_rate_limit)],
)


@router.post("/diagnose/image", response_model=ImageDiagnoseResponse)
async def diagnose_image(
    payload: ImageDiagnoseRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    claude: ClaudeClient = Depends(get_claude_client),
) -> ImageDiagnoseResponse:
    vehicle = await vehicle_service.get_owned(db, user.id, payload.vehicle_id)
    return await vision_service.diagnose_image(
        db=db, claude=claude, user=user, vehicle=vehicle, payload=payload
    )


@router.post("/diagnose/sound", response_model=SoundDiagnoseResponse)
async def diagnose_sound(
    payload: SoundDiagnoseRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    claude: ClaudeClient = Depends(get_claude_client),
) -> SoundDiagnoseResponse:
    vehicle = await vehicle_service.get_owned(db, user.id, payload.vehicle_id)
    return await audio_service.diagnose_sound(
        db=db, claude=claude, user=user, vehicle=vehicle, payload=payload
    )


@router.post("/diagnose/dashboard", response_model=DashboardDiagnoseResponse)
async def diagnose_dashboard(
    payload: DashboardDiagnoseRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    claude: ClaudeClient = Depends(get_claude_client),
) -> DashboardDiagnoseResponse:
    vehicle = await vehicle_service.get_owned(db, user.id, payload.vehicle_id)
    return await dashboard_service.diagnose_dashboard(
        db=db, claude=claude, user=user, vehicle=vehicle, payload=payload
    )


@router.post("/diagnose/code", response_model=DtcDiagnoseResponse)
async def diagnose_code(
    payload: DtcDiagnoseRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    claude: ClaudeClient = Depends(get_claude_client),
) -> DtcDiagnoseResponse:
    vehicle = await vehicle_service.get_owned(db, user.id, payload.vehicle_id)
    return await dtc_service.diagnose_dtc(
        db=db, claude=claude, user=user, vehicle=vehicle, payload=payload
    )
