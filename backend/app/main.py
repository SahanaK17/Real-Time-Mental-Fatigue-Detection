"""
Mental Fatigue Detector — FastAPI Application Entry Point
==========================================================
Production-grade FastAPI app with:
- Structured logging
- CORS middleware
- Rate limiting
- WebSocket support
- Health checks
- Lifespan management (DB + Redis connections)
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.exceptions import setup_exception_handlers
from app.db.session import engine, AsyncSessionLocal
from app.db.base import Base
from app.core.redis_client import redis_client
from app.api.v1.router import api_router
from app.websocket.manager import ws_manager

# Setup structured logging
setup_logging()
logger = structlog.get_logger(__name__)


# ── Rate Limiter ──────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


# ── Application Lifespan ──────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle."""
    logger.info("Starting Mental Fatigue Detector API", version=settings.APP_VERSION)

    # Initialize database tables (development only — use Alembic in prod)
    if settings.APP_ENV == "development":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created/verified")

    # Test Redis connection
    import asyncio

    try:
        await asyncio.wait_for(redis_client.ping(), timeout=1.0)
        logger.info("Redis connection established")
    except asyncio.TimeoutError:
        logger.warning("Redis connection timed out, caching disabled")
    except Exception as e:
        logger.warning("Redis connection failed, caching disabled", error=str(e))

    # Load ML model into memory
    try:
        from app.ml.inference import model_registry

        await model_registry.load()
        logger.info("ML model loaded into memory")
    except Exception as e:
        logger.warning("ML model not found — using fallback", error=str(e))

    logger.info("Application startup complete")
    yield

    # Cleanup
    logger.info("Shutting down application...")
    await redis_client.close()
    await engine.dispose()
    logger.info("✅ Cleanup complete")


# ── Application Instance ──────────────────────────────────
def create_application() -> FastAPI:
    """Application factory pattern."""

    app = FastAPI(
        title=settings.APP_NAME,
        description="""
## Real-Time Mental Fatigue Detection API

A production-grade API for detecting mental fatigue through keyboard and mouse behavioral analysis.

### Features
- 🔐 JWT Authentication with role-based access control
- 📊 Real-time behavioral data ingestion
- 🤖 ML-powered fatigue prediction with SHAP explainability
- 🔌 WebSocket support for live dashboard updates
- 📈 Analytics and reporting endpoints

### Authentication
Most endpoints require a **Bearer token** obtained from `/api/v1/auth/login`.
        """,
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── Middleware Stack ───────────────────────────────────
    # Order matters: outermost middleware runs first on request, last on response

    # GZip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS_LIST,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time"],
    )

    # Rate limiting
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # ── Request ID + Timing Middleware ────────────────────
    @app.middleware("http")
    async def add_process_time_and_request_id(request: Request, call_next):
        import time
        import uuid

        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.4f}s"

        logger.debug(
            "Request processed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time_ms=round(process_time * 1000, 2),
            request_id=request_id,
        )
        return response

    # ── Exception Handlers ────────────────────────────────
    setup_exception_handlers(app)

    # ── Routers ───────────────────────────────────────────
    app.include_router(api_router, prefix=settings.API_PREFIX)

    # ── Health Check ──────────────────────────────────────
    @app.get("/health", tags=["System"], summary="Health check")
    async def health_check():
        """Returns service health status including DB and Redis connectivity."""
        health = {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
            "services": {},
        }

        # Check database
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(__import__("sqlalchemy", fromlist=["text"]).text("SELECT 1"))
            health["services"]["database"] = "healthy"
        except Exception as e:
            health["services"]["database"] = f"unhealthy: {str(e)}"
            health["status"] = "degraded"

        # Check Redis
        try:
            await redis_client.ping()
            health["services"]["redis"] = "healthy"
        except Exception as e:
            health["services"]["redis"] = f"unhealthy: {str(e)}"
            health["status"] = "degraded"

        # Check ML model
        try:
            from app.ml.inference import model_registry

            health["services"]["ml_model"] = "loaded" if model_registry.is_loaded else "not_loaded"
        except Exception:
            health["services"]["ml_model"] = "unavailable"

        status_code = (
            status.HTTP_200_OK
            if health["status"] == "healthy"
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        return JSONResponse(content=health, status_code=status_code)

    @app.get("/", tags=["System"], include_in_schema=False)
    async def root():
        return {
            "message": "Mental Fatigue Detector API",
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "health": "/health",
        }

    return app


app = create_application()


# WebSocket endpoint (registered at app level for simplicity)
from fastapi import WebSocket, WebSocketDisconnect
from app.core.security import decode_access_token


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time fatigue score streaming.
    Clients must authenticate via query param: ?token=<JWT>
    """
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing auth token")
        return

    payload = decode_access_token(token)
    if not payload or payload.get("sub") != user_id:
        await websocket.close(code=4003, reason="Unauthorized")
        return

    await ws_manager.connect(websocket, user_id)
    logger.info("WebSocket connected", user_id=user_id)

    try:
        while True:
            # Keep alive — receive pings from client
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id)
        logger.info("WebSocket disconnected", user_id=user_id)
