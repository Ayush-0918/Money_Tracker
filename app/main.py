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
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from app.utils.limiter import limiter
from app.api import auth, reports, transactions, admin, dashboard, budgets, categories, predictions
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

    if settings.SENTRY_DSN:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastAPIIntegration

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[FastAPIIntegration()],
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
            environment=settings.ENVIRONMENT,
        )
        logger.info("Sentry monitoring initialized successfully")

    logger.info("Money Tracker API starting up | environment=%s", settings.ENVIRONMENT)

    if settings.ENVIRONMENT == "development":
        # Auto-create tables in development for convenience.
        # In production: run `alembic upgrade head` instead.
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified/created (development mode)")

    # Seed system categories if they don't exist
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.models.category import Category
    from sqlalchemy import select

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        async with session.begin():
            categories_to_seed = [
                ("food", "food-dining", "Food & Dining", "restaurant", "#4CAF7D", 10),
                ("shopping", "shopping", "Shopping", "shopping_bag", "#90CAF9", 20),
                ("bills", "bills-utilities", "Bills & Utilities", "receipt", "#F5A623", 30),
                ("transport", "transport", "Transport", "directions_car", "#B36B00", 40),
                ("entertainment", "entertainment", "Entertainment", "movie", "#1E3A5F", 50),
                ("investment", "investment", "Investment", "trending_up", "#4CAF50", 60),
                ("health", "health", "Health & Wellness", "favorite", "#E91E63", 70),
                ("income", "income", "Income", "attach_money", "#9C27B0", 80),
                ("loans/emi", "loans-emi", "Loans & EMI", "account_balance", "#795548", 90),
                ("credit card payment", "credit-card-payment", "Credit Card Payment", "credit_card", "#607D8B", 100),
                ("others", "others", "Others", "more_horiz", "#9E9E9E", 110),
            ]
            for name, slug, display_name, icon, color, sort_order in categories_to_seed:
                stmt = select(Category).where(Category.name == name)
                res = await session.execute(stmt)
                if not res.scalar_one_or_none():
                    new_cat = Category(
                        name=name,
                        slug=slug,
                        display_name=display_name,
                        icon=icon,
                        color=color,
                        sort_order=sort_order,
                        system=True,
                    )
                    session.add(new_cat)
        logger.info("System categories seeded/verified")

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
    app.include_router(predictions.router)

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

        return {"status": "ok", "database": db_status, "version": "1.0.0"}

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

    # ── Request Validation Error Handler ──────────────────────────────────────
    from fastapi.exceptions import RequestValidationError
    from fastapi.encoders import jsonable_encoder

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.warning("Validation failed: %s", exc.errors())
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder(
                {
                    "error": "VALIDATION_ERROR",
                    "message": "Invalid request payload or query parameters.",
                    "details": exc.errors(),
                }
            ),
        )

    # ── Request ID Middleware ────────────────────────────────────────────────
    import uuid
    from app.utils.logging_config import request_id_ctx_var

    @app.middleware("http")
    async def add_request_id_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        token = request_id_ctx_var.set(request_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            request_id_ctx_var.reset(token)

    return app


# ── App Instance ──────────────────────────────────────────────────────────────
# Module-level app instance for uvicorn: `uvicorn app.main:app`
app = create_app()
