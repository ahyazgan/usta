"""Usta FastAPI uygulaması — lifespan, CORS, güvenlik başlıkları, /health."""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import text

from .api import (
    account,
    admin,
    ai,
    auth,
    billing,
    catalog,
    estimates,
    fuel,
    live,
    maintenance,
    mechanics,
    parts,
    stats,
    tasks,
    vehicles,
)
from .config import get_settings
from .database import SessionLocal, create_all
from .domain.ai_errors import AIError
from .domain.schemas import HealthResponse

settings = get_settings()
logger = structlog.get_logger("usta")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_all()
    logger.info("startup", app=settings.app_name, debug=settings.debug)
    yield
    logger.info("shutdown")


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

# CORS: debug'da "*", prod'da yalnızca https://usta.app
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=not settings.debug,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    """request-id + yapılandırılmış log + güvenlik başlıkları."""
    request_id = request.headers.get("x-request-id", uuid.uuid4().hex)
    start = time.monotonic()
    structlog.contextvars.bind_contextvars(request_id=request_id, path=request.url.path)

    response = await call_next(request)

    duration_ms = round((time.monotonic() - start) * 1000, 2)
    response.headers["x-request-id"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    if not settings.debug:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    logger.info("request", method=request.method, status=response.status_code, ms=duration_ms)
    structlog.contextvars.clear_contextvars()
    return response


@app.exception_handler(AIError)
async def ai_error_handler(request: Request, exc: AIError) -> JSONResponse:
    """AI hatalarını çıplak 500 yerine temiz, kullanıcı-dostu yanıta çevirir."""
    logger.warning("ai_error", code=exc.code, status=exc.status_code, detail=exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "code": exc.code},
    )


@app.get("/health", response_model=HealthResponse, tags=["meta"])
async def health() -> HealthResponse:
    """DB ping'li sağlık kontrolü."""
    db_status = "ok"
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception:  # pragma: no cover
        db_status = "down"
    return HealthResponse(status="ok", database=db_status)


_STATIC_DIR = Path(__file__).resolve().parent / "static"


@app.get("/privacy", include_in_schema=False)
async def privacy_policy() -> FileResponse:
    """Herkese açık gizlilik politikası (mağaza zorunlu URL'i)."""
    return FileResponse(_STATIC_DIR / "privacy.html", media_type="text/html")


@app.get("/terms", include_in_schema=False)
async def terms_of_use() -> FileResponse:
    """Herkese açık Kullanım Şartları / EULA (mağaza için)."""
    return FileResponse(_STATIC_DIR / "terms.html", media_type="text/html")


app.include_router(auth.router)
app.include_router(account.router)
app.include_router(catalog.router)
app.include_router(vehicles.router)
app.include_router(tasks.router)
app.include_router(maintenance.router)
app.include_router(fuel.router)
app.include_router(estimates.router)
app.include_router(ai.router)
app.include_router(live.router)
app.include_router(parts.router)
app.include_router(billing.router)
app.include_router(admin.router)
app.include_router(mechanics.router)
app.include_router(stats.router)
