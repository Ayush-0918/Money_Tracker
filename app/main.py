"""
app/main.py
─────────────────────────────────────────────────────────────────────────────
FastAPI application factory.

This module:
  1. Creates the FastAPI app instance with metadata (title, version, docs URL).
  2. Sets up the lifespan context manager (database startup/shutdown).
  3. Attaches middleware (CORS, rate limiting).
  4. Registers all API routers.
  5. Adds a health-check endpoint for deployment monitoring.

Run locally:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from app.utils.limiter import limiter
from app.api import auth, reports, transactions, admin, dashboard, budgets, categories
from app.config import settings
from app.database import engine
from app.models import Base
from app.utils.logging_config import configure_logging, get_logger

logger = get_logger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.

    Startup:
      - Configure logging.
      - (Development only) Create all tables via SQLAlchemy metadata.
        In production, use Alembic migrations instead.

    Shutdown:
      - Dispose the database connection pool gracefully.
    """
    # ── Startup ───────────────────────────────────────────────────────────────
    configure_logging()
    logger.info("Money Tracker API starting up | environment=%s", settings.ENVIRONMENT)

    if settings.ENVIRONMENT == "development":
        # Auto-create tables in development for convenience.
        # In production: run `alembic upgrade head` instead.
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified/created (development mode)")

    yield  # Application runs here

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("Money Tracker API shutting down — disposing DB pool")
    await engine.dispose()


# ── App Factory ───────────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Fully configured FastAPI app instance ready to be served by uvicorn.
    """
    app = FastAPI(
        title="Money Tracker API",
        description=(
            "Backend for the Money Tracker Android app. "
            "Receives payment notifications, parses transactions, "
            "and generates WhatsApp-ready spending reports."
        ),
        version="1.0.0",
        docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
        lifespan=lifespan,
    )

    # ── State (for slowapi) ───────────────────────────────────────────────────
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # ── CORS Middleware ───────────────────────────────────────────────────────
    # Only allow requests from configured origins (Android app + dev frontend).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH"],
        allow_headers=["Authorization", "Content-Type"],
    )

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(auth.router)
    app.include_router(transactions.router)
    app.include_router(reports.router)
    app.include_router(admin.router)
    app.include_router(dashboard.router)
    app.include_router(budgets.router)
    app.include_router(categories.router)

    # ── Health Check ──────────────────────────────────────────────────────────
    @app.get(
        "/health",
        tags=["System"],
        summary="Health check",
        description="Returns 200 OK if the API is running. Used by deployment monitors.",
    )
    async def health_check() -> dict[str, str]:
        """Simple liveness probe for load balancers and uptime monitors."""
        db_status = "ok"
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception as e:
            logger.error("Health check DB ping failed: %s", e)
            db_status = "failed"
            
        return {
            "status": "ok", 
            "database": db_status,
            "version": "1.0.0"
        }

    # ── Global Exception Handler ──────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        Catch-all handler for unhandled exceptions.
        Returns a generic 500 without leaking internal error details.
        Logs the full traceback for debugging.
        """
        logger.exception(
            "Unhandled exception | path=%s | method=%s",
            request.url.path,
            request.method,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
            },
        )

    return app


# ── App Instance ──────────────────────────────────────────────────────────────
# Module-level app instance for uvicorn: `uvicorn app.main:app`
app = create_app()
