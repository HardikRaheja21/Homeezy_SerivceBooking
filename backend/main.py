# backend/main.py
"""
Homeezy FastAPI application entry point.

Responsibilities:
- App factory with lifespan hooks
- Middleware: CORS, rate-limiting, request logging, process-time header
- Global exception handlers (standardized JSON errors)
- Router registration
- Health + readiness probes
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logging_config import get_logger
from app.core.rate_limiter import RateLimiter
from app.core.redis import redis_client

import sentry_sdk
if getattr(settings, "SENTRY_DSN", None):
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )
from app.api.v1 import (
    auth, users, services, bookings,
    payments, admin, workers, reviews,
    chat, ai, complaints,
)
import app.models  # noqa: F401 — registers all ORM models

logger = get_logger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup / shutdown hook.
    NOTE: Schema creation is handled by Alembic (`alembic upgrade head`).
          create_all() is intentionally removed — Alembic is the single truth.
    """
    logger.info("Homeezy API starting up — version %s", settings.APP_NAME)

    # Seed default service catalog (idempotent)
    from app.api.v1.services import seed_default_service_categories
    db = SessionLocal()
    try:
        seed_default_service_categories(db)
        logger.info("Service catalog seeded")
    except Exception:
        logger.exception("Service catalog seed failed — continuing startup")
    finally:
        db.close()

    yield

    # Graceful shutdown
    logger.info("Homeezy API shutting down")
    await redis_client.close()


# ── App factory ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Homeezy API",
    description=(
        "Production-ready AI-powered home services marketplace.\n\n"
        "## Authentication\n"
        "Use Bearer JWT tokens. Obtain via `POST /api/v1/auth/login`.\n\n"
        "## Roles\n"
        "- **customer** — book services, review workers, raise complaints\n"
        "- **worker** — accept bookings, manage availability, view earnings\n"
        "- **admin** — approve workers, manage users, view platform analytics\n"
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Rate limiter ──────────────────────────────────────────────────────────────

rate_limiter = RateLimiter(redis_client)


# ── Middleware ────────────────────────────────────────────────────────────────

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    if not await rate_limiter.check_rate_limit(client_ip):
        return JSONResponse(
            status_code=429,
            content={"success": False, "message": "Too many requests. Please slow down."},
        )
    return await call_next(request)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log every request with method, path, status, and duration."""
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"
    logger.info(
        "%s %s → %s (%.0fms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


# ── Global exception handlers ─────────────────────────────────────────────────

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors — return structured 422 responses."""
    errors = [
        {"field": " → ".join(str(loc) for loc in e["loc"]), "message": e["msg"]}
        for e in exc.errors()
    ]
    logger.warning("Validation error on %s: %s", request.url.path, errors)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"success": False, "message": "Validation failed", "errors": errors},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch-all — never leak stack traces to clients."""
    logger.exception("Unhandled exception on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "An internal server error occurred."},
    )


# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(auth.router,       prefix="/api/v1/auth",       tags=["Authentication"])
app.include_router(users.router,      prefix="/api/v1/users",      tags=["Users"])
app.include_router(services.router,   prefix="/api/v1/services",   tags=["Services"])
app.include_router(bookings.router,   prefix="/api/v1/bookings",   tags=["Bookings"])
app.include_router(payments.router,   prefix="/api/v1/payments",   tags=["Payments"])
app.include_router(workers.router,    prefix="/api/v1/workers",    tags=["Workers"])
app.include_router(reviews.router,    prefix="/api/v1/reviews",    tags=["Reviews"])
app.include_router(complaints.router, prefix="/api/v1/complaints", tags=["Complaints"])
from app.api.v1 import notifications, uploads
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])
app.include_router(uploads.router,       prefix="/api/v1/uploads",       tags=["Uploads"])
app.include_router(chat.router,       prefix="/api/v1/chat",       tags=["Chat"])
app.include_router(admin.router,      prefix="/api/v1/admin",      tags=["Admin"])
app.include_router(ai.router,         prefix="/api/v1/ai",         tags=["AI"])

from app.websockets.routes import router as websocket_router
app.include_router(websocket_router)


# ── Prometheus Metrics ────────────────────────────────────────────────────────
# Instrumentator().instrument(app).expose(app)
# Temporarily disabled due to incompatibility with latest FastAPI/Starlette (ValueError: too many values to unpack)
# ── Health & Readiness ────────────────────────────────────────────────────────

@app.get(
    "/",
    tags=["System"],
    summary="API root",
    response_description="Welcome message",
)
async def root():
    return {"message": "Welcome to Homeezy API", "version": "1.0.0", "docs": "/docs"}


@app.get(
    "/health",
    tags=["System"],
    summary="Liveness probe",
    response_description="API is alive",
)
async def health():
    """Lightweight liveness check — no DB call. Used by load balancers."""
    return {"status": "healthy"}


@app.get(
    "/ready",
    tags=["System"],
    summary="Readiness probe",
    response_description="API and DB are ready",
)
async def ready():
    """
    Readiness check — verifies the database connection is alive.
    Returns 503 if the DB is unreachable so orchestrators can hold traffic.
    """
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "connected"
    except Exception as exc:
        logger.error("Readiness check failed: %s", exc)
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "database": "unreachable"},
        )
    return {"status": "ready", "database": db_status}
