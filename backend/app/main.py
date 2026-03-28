"""FastAPI application main entry point.

Mantisbot - AI-powered conversational commerce for Facebook Messenger.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path as FilePath
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api import health as health_router
from app.api.analytics import router as analytics_router
from app.api.audit import router as audit_router
from app.api.auth import router as auth_router
from app.api.bot_config import router as bot_config_router
from app.api.business_hours import router as business_hours_router
from app.api.business_info import router as business_info_router
from app.api.carriers import router as carriers_router
from app.api.consent import router as consent_router
from app.api.conversations import router as conversation_router
from app.api.cost_tracking import router as cost_tracking_router
from app.api.csrf import router as csrf_router
from app.api.data_deletion import router as data_deletion_router
from app.api.data_export import router as data_export_router
from app.api.deployment import router as deployment_router
from app.api.export import router as export_router
from app.api.faqs import router as faqs_router
from app.api.feedback import router as feedback_router
from app.api.faq_click import router as faq_click_router
from app.api.handoff_alerts import router as handoff_alerts_router
from app.api.health import router as health_router
from app.api.integrations import router as integrations_router
from app.api.knowledge_base import router as knowledge_base_router
from app.api.llm import router as llm_router
from app.api.merchant import router as merchant_router
from app.api.onboarding import router as onboarding_router
from app.api.preview import router as preview_router
from app.api.product_pins import router as product_pins_router
from app.api.search import router as search_router
from app.api.settings import router as settings_router
from app.api.tutorial import router as tutorial_router
from app.api.webhooks.facebook import router as facebook_webhook_router
from app.api.webhooks.shopify import router as shopify_webhook_router
from app.api.webhooks.verification import router as verification_router
from app.api.widget import router as widget_router
from app.api.widget_events import router as widget_events_router
from app.api.widget_settings import router as widget_settings_router
from app.api.widget_ws import router as widget_ws_router
from app.background_jobs.data_retention import shutdown_scheduler, start_scheduler
from app.background_jobs.widget_cleanup import (
    shutdown_widget_cleanup_scheduler,
    start_widget_cleanup_scheduler,
)
from app.core.config import settings
from app.core.database import close_db, engine, init_db
from app.core.errors import APIError, ErrorCode
from app.middleware.auth import AuthenticationMiddleware
from app.middleware.cors import CORSHeaderMiddleware
from app.middleware.csrf import setup_csrf_middleware
from app.middleware.security import setup_security_middleware
from app.schemas.deployment import (  # noqa: F401 (export for type generation)
    DeploymentLogEntry,
    DeploymentState,
    DeploymentStatus,
    DeploymentStep,
    LogLevel,
    Platform,
    StartDeploymentRequest,
    StartDeploymentResponse,
)
from app.schemas.onboarding import (  # noqa: F401 (export for type generation)
    MetaData,
    MinimalEnvelope,
    PrerequisiteCheckRequest,
    PrerequisiteCheckResponse,
)
from app.schemas.webhook_verification import (  # noqa: F401 (export for type generation)
    FacebookWebhookStatus,
    ShopifyWebhookStatus,
    WebhookResubscribeResponse,
    WebhookStatusResponse,
    WebhookTestResponse,
)


def get_error_status_code(error_code: ErrorCode) -> int:
    """Map error codes to appropriate HTTP status codes.

    Args:
        error_code: The ErrorCode to map

    Returns:
        HTTP status code
    """
    # 2xxx: Auth/Security errors -> 401/403/400
    if 2000 <= error_code < 3000:
        if error_code in (ErrorCode.AUTH_FAILED, ErrorCode.TOKEN_EXPIRED, ErrorCode.UNAUTHORIZED):
            return status.HTTP_401_UNAUTHORIZED
        if error_code in (
            ErrorCode.PREREQUISITES_INCOMPLETE,
            ErrorCode.DEPLOYMENT_IN_PROGRESS,
            ErrorCode.MERCHANT_ALREADY_EXISTS,
        ):
            return status.HTTP_400_BAD_REQUEST
        if error_code in (ErrorCode.MERCHANT_NOT_FOUND,):
            return status.HTTP_404_NOT_FOUND
        return status.HTTP_403_FORBIDDEN

    # 6xxx: Cart/Checkout errors -> 400 or 404
    if 6000 <= error_code < 7000:
        if error_code in (
            ErrorCode.CART_NOT_FOUND,
            ErrorCode.CHECKOUT_EXPIRED,
            ErrorCode.CART_SESSION_EXPIRED,
        ):
            return status.HTTP_404_NOT_FOUND
        return status.HTTP_400_BAD_REQUEST

    # 7xxx: Conversation/Session errors -> 404 or 400
    if 7000 <= error_code < 8000:
        if error_code in (ErrorCode.SESSION_EXPIRED, ErrorCode.CONVERSATION_NOT_FOUND):
            return status.HTTP_404_NOT_FOUND
        return status.HTTP_400_BAD_REQUEST

    # 8xxx: Export errors -> 400 or 408
    if 8000 <= error_code < 9000:
        if error_code == ErrorCode.EXPORT_TIMEOUT:
            return status.HTTP_408_REQUEST_TIMEOUT
        return status.HTTP_400_BAD_REQUEST

    # 12xxx: Widget errors -> 400, 401, 403, 404, or 429
    if 12000 <= error_code < 13000:
        if error_code in (ErrorCode.WIDGET_SESSION_NOT_FOUND, ErrorCode.WIDGET_SETTINGS_NOT_FOUND):
            return status.HTTP_404_NOT_FOUND
        if error_code == ErrorCode.WIDGET_SESSION_EXPIRED:
            return status.HTTP_401_UNAUTHORIZED
        if error_code in (ErrorCode.WIDGET_MERCHANT_DISABLED, ErrorCode.WIDGET_DOMAIN_NOT_ALLOWED):
            return status.HTTP_403_FORBIDDEN
        if error_code == ErrorCode.WIDGET_RATE_LIMITED:
            return status.HTTP_429_TOO_MANY_REQUESTS
        return status.HTTP_400_BAD_REQUEST

    # 11xxx: Data Export errors -> 400, 429
    if 11000 <= error_code < 12000:
        if error_code in (ErrorCode.EXPORT_RATE_LIMITED, ErrorCode.EXPORT_ALREADY_IN_PROGRESS):
            return status.HTTP_429_TOO_MANY_REQUESTS
        return status.HTTP_400_BAD_REQUEST

    # 1xxx: General errors
    if error_code == ErrorCode.VALIDATION_ERROR:
        return status.HTTP_422_UNPROCESSABLE_ENTITY
    if error_code == ErrorCode.NOT_FOUND:
        return status.HTTP_404_NOT_FOUND
    if error_code == ErrorCode.FORBIDDEN:
        return status.HTTP_403_FORBIDDEN

    # Default for unknown errors
    return status.HTTP_400_BAD_REQUEST


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan.

    Yields:
        None
    """
    # Startup
    try:
        await init_db()
    except Exception as e:
        import structlog
        structlog.get_logger().warning("db_init_failed_during_startup", error=str(e))
        # Database will be initialized lazily on first use
    start_scheduler()  # Story 2-7: Start data retention cleanup scheduler
    await start_widget_cleanup_scheduler()  # Story 5-2: Start widget session cleanup scheduler

    # Initialize LLM pricing from OpenRouter
    try:
        from app.services.cost_tracking.pricing import initialize_pricing_from_openrouter

        await initialize_pricing_from_openrouter()
    except Exception as e:
        import structlog

        structlog.get_logger().warning("pricing_init_failed", error=str(e))

    # Story 4-4: Start Shopify order polling scheduler
    try:
        from app.tasks.polling_scheduler import start_polling_scheduler

        await start_polling_scheduler()
    except Exception as e:
        # Log but don't fail startup if polling scheduler fails
        import structlog

        logger = structlog.get_logger()
        logger.warning("polling_scheduler_startup_failed", error=str(e))

    yield
    # Shutdown
    # Story 4-4: Shutdown Shopify order polling scheduler
    try:
        from app.tasks.polling_scheduler import shutdown_polling_scheduler

        await shutdown_polling_scheduler()
    except Exception as e:
        import structlog

        logger = structlog.get_logger()
        logger.warning("polling_scheduler_shutdown_failed", error=str(e))
    await shutdown_widget_cleanup_scheduler()  # Story 5-2: Shutdown widget cleanup scheduler
    shutdown_scheduler()  # Story 2-7: Shutdown scheduler gracefully
    await close_db()


# Create FastAPI application
app = FastAPI(
    title="Mantisbot",
    description="AI-powered conversational commerce for Facebook Messenger",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


def _is_allowed_origin(origin: str) -> bool:
    from urllib.parse import urlparse

    allowed_origins = settings()["CORS_ORIGINS"]
    if origin in allowed_origins:
        return True

    try:
        parsed = urlparse(origin)
        hostname = parsed.hostname
        if hostname and hostname.lower().endswith(".myshopify.com"):
            return True
        if hostname and hostname.lower().endswith(".trycloudflare.com"):
            return True
        if hostname and hostname.lower().endswith(".vercel.app"):
            return True
    except Exception:
        pass
    return False


# Configure CORS - limit to specific methods for better security
# regex matches:
# 1. *.myshopify.com (with optional port)
# 2. *.trycloudflare.com (with optional port)
# 3. *.vercel.app (with optional port)
# 4. localhost and other origins from settings
cors_patterns = [
    r"https?://([a-z0-9-]+\.)?myshopify\.com(:\d+)?",
    r"https?://([a-z0-9-]+\.)?trycloudflare\.com(:\d+)?",
    r"https?://([a-z0-9-]+\.)+vercel\.app(:\d+)?",
]

# Add custom origins from settings, escaping special characters
for origin in settings()["CORS_ORIGINS"]:
    if origin:
        pattern = origin.replace(".", r"\.").replace(":", r":")
        cors_patterns.append(pattern)

allow_origin_regex = "^(" + "|".join(cors_patterns) + ")$"

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Webhook-Signature",
        "X-CSRF-Token",
        "X-Merchant-Id",
        "X-Test-Mode",
        "Accept",
    ],
)

# Setup CORS header middleware to ensure headers are always present
# This fixes issues with proxies like zrok stripping CORS headers
app.add_middleware(CORSHeaderMiddleware)

# Setup security middleware (HTTPS enforcement, HSTS, CSP, etc.)
# NFR-S1: HTTPS Enforcement with HSTS
# NFR-S7: Content Security Policy and other security headers
setup_security_middleware(app)

# Setup CSRF middleware for state-changing operations
# NFR-S8: CSRF tokens for POST/PUT/DELETE operations
setup_csrf_middleware(app)

# Authentication middleware (MEDIUM-11: added for cookie validation)
app.add_middleware(AuthenticationMiddleware)


# Root endpoints
@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with API information."""
    return {
        "message": "Mantisbot API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health() -> dict[str, Any]:
    """Health check endpoint with database connectivity."""
    health_status = {"status": "healthy", "database": "connected"}

    # Check database connectivity
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["database"] = f"disconnected: {str(e)}"

    return health_status


WIDGET_DIST_PATH = FilePath(__file__).parent.parent.parent / "frontend" / "dist" / "widget"


@app.get("/widget/{filename:path}")
async def serve_widget_file(filename: str):
    """Serve widget files for local development."""
    if not filename.endswith((".js", ".css", ".map")):
        return JSONResponse(status_code=403, content={"error": "Invalid file type"})

    widget_file = WIDGET_DIST_PATH / filename
    if widget_file.exists():
        return FileResponse(
            widget_file,
            media_type="application/javascript" if filename.endswith(".js") else "text/css",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "no-cache, no-store, must-revalidate",
            },
        )
    return JSONResponse(status_code=404, content={"error": f"File not found: {filename}"})


# Exception handlers
@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle APIError exceptions with appropriate status codes.

    Args:
        request: The request object
        exc: The APIError exception

    Returns:
        JSONResponse with error details and optional Retry-After header
    """
    status_code = get_error_status_code(exc.code)
    headers = {}

    if (
        exc.code
        in (
            ErrorCode.WIDGET_RATE_LIMITED,
            ErrorCode.EXPORT_RATE_LIMITED,
            ErrorCode.EXPORT_ALREADY_IN_PROGRESS,
        )
        and "retry_after" in exc.details
    ):
        headers["Retry-After"] = str(exc.details["retry_after"])

    return JSONResponse(
        status_code=status_code,
        content=exc.to_dict(),
        headers=headers if headers else None,
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unhandled exceptions with JSON error response.

    Ensures all errors return JSON instead of plain text "Internal Server Error".

    Args:
        request: The request object
        exc: The unhandled exception

    Returns:
        JSONResponse with generic error message
    """
    import structlog

    structlog.get_logger().exception(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
    )

    return JSONResponse(
        status_code=500,
        content={
            "code": 1000,
            "message": "Internal server error",
            "details": {},
        },
    )


# Mount static files for widget
from pathlib import Path as FilePath

_static_dir = FilePath(__file__).parent.parent / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


# Include API routes
# Story 1.8: Authentication
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(onboarding_router, prefix="/api/onboarding", tags=["onboarding"])
app.include_router(deployment_router, prefix="/api/deployment", tags=["deployment"])
app.include_router(merchant_router, prefix="/api/merchant", tags=["merchant"])
# Story 1.11: Business Info & FAQ Configuration
app.include_router(business_info_router, prefix="/api/v1/merchant", tags=["business-info"])
# Story 1.12: Bot Naming Configuration
# Story 1.15: Product Highlight Pins
app.include_router(bot_config_router, prefix="/api/v1/merchant", tags=["bot-config"])
app.include_router(product_pins_router, prefix="/api/v1/merchant", tags=["product-pins"])
app.include_router(faqs_router, prefix="/api/v1/merchant", tags=["faqs"])
app.include_router(integrations_router, prefix="/api", tags=["integrations"])
app.include_router(data_deletion_router, prefix="/api", tags=["data-deletion"])
app.include_router(llm_router, prefix="/api/llm", tags=["llm"])
app.include_router(tutorial_router, prefix="/api/tutorial", tags=["tutorial"])
app.include_router(csrf_router, prefix="/api/v1", tags=["csrf"])
app.include_router(facebook_webhook_router, prefix="/api/webhooks", tags=["webhooks"])
app.include_router(shopify_webhook_router, prefix="/api/webhooks", tags=["webhooks"])
app.include_router(verification_router, prefix="/api/webhooks/verification", tags=["webhooks"])
app.include_router(conversation_router, prefix="/api/conversations", tags=["conversations"])
app.include_router(export_router, tags=["export"])
app.include_router(cost_tracking_router, tags=["costs"])
app.include_router(business_hours_router, prefix="/api/v1/merchant", tags=["business-hours"])
app.include_router(handoff_alerts_router, prefix="/api/handoff-alerts", tags=["handoff-alerts"])
app.include_router(settings_router, prefix="/api/settings", tags=["settings"])
# Story 4-4: Polling health endpoint
app.include_router(health_router, prefix="/api/v1/health", tags=["health"])
# Story 1.13: Bot Preview Mode
app.include_router(preview_router, prefix="/api/v1", tags=["preview"])
# Story 5-1: Widget API
app.include_router(widget_router, prefix="/api/v1", tags=["widget"])
# Widget SSE Events (deprecated - keeping for backward compatibility)
app.include_router(widget_events_router, prefix="/api/v1", tags=["widget-events"])
# Widget WebSocket (preferred for real-time communication)
app.include_router(widget_ws_router, tags=["widget-websocket"])
# Story 5-6: Widget Settings API
app.include_router(widget_settings_router, prefix="/api/v1/merchants", tags=["widget-settings"])
# Story 4-13: Geographic Analytics API
app.include_router(analytics_router, prefix="/api/v1", tags=["analytics"])
app.include_router(data_export_router, prefix="/api/v1", tags=["data-export"])
app.include_router(consent_router, prefix="/api/v1/consent", tags=["consent"])
app.include_router(audit_router, prefix="/api/v1/audit", tags=["audit"])
app.include_router(search_router, prefix="/api/v1", tags=["search"])
# Story 10-4: Feedback Rating Widget
app.include_router(feedback_router, tags=["feedback"])
# Story 10-10: FAQ Usage Widget - FAQ Click Tracking
app.include_router(faq_click_router, prefix="/api/v1/widget", tags=["faq-click"])
# Epic 6: Carrier Configuration API
app.include_router(carriers_router, tags=["carriers"])
# Epic 8: Knowledge Base API
app.include_router(knowledge_base_router, prefix="/api", tags=["knowledge-base"])
# These will be added as features are implemented:
# from app.api.routes import chat, cart, checkout
# app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
# app.include_router(cart.router, prefix="/api/v1", tags=["cart"])
# app.include_router(checkout.router, prefix="/api/v1", tags=["checkout"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings()["DEBUG"],
    )
