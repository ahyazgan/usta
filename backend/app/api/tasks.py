"""Bakım görevi rotaları: mevcut görevleri listeler (JWT + rate limit)."""

from fastapi import APIRouter, Depends

from ..core.deps import get_current_user
from ..core.rate_limit import enforce_rate_limit
from ..domain.models import User
from ..domain.schemas import TaskOut
from ..domain.tasks import get_tasks

router = APIRouter(
    prefix="/v1/tasks",
    tags=["tasks"],
    dependencies=[Depends(enforce_rate_limit)],
)


@router.get("", response_model=list[TaskOut])
async def list_tasks(user: User = Depends(get_current_user)) -> list[TaskOut]:
    return [
        TaskOut(id=t.id, title_tr=t.title_tr, title_en=t.title_en, risk=t.risk)
        for t in get_tasks()
    ]
