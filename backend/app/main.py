"""FastAPI application main entry point.

Shopping Assistant Bot - AI-powered conversational commerce for Facebook Messenger.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import settings
from app.core.errors import APIError, ErrorCode
from app.core.database import init_db, close_db, engine
from app.api.onboarding import router as onboarding_router
from app.api.deployment import router as deployment_router
from app.api.integrations import router as integrations_router
from app.api.data_deletion import router as data_deletion_router
from app.api.merchant import router as merchant_router
from app.api.business_info import router as business_info_router
from app.api.bot_config import router as bot_config_router
from app.api.product_pins import router as product_pins_router
from app.api.faqs import router as faqs_router
from app.api.webhooks.facebook import router as facebook_webhook_router
from app.api.webhooks.shopify import router as shopify_webhook_router
from app.api.webhooks.verification import router as verification_router
from app.api.llm import router as llm_router
from app.api.tutorial import router as tutorial_router
from app.api.conversations import router as conversation_router
from app.api.csrf import router as csrf_router
from app.api.export import router as export_router
from app.api.preview import router as preview_router
from app.api.auth import router as auth_router
from app.api.cost_tracking import router as cost_tracking_router
from app.api.business_hours import router as business_hours_router
from app.api.handoff_alerts import router as handoff_alerts_router
from app.api.settings import router as settings_router
from app.middleware.security import setup_security_middleware
from app.middleware.csrf import setup_csrf_middleware
from app.middleware.auth import AuthenticationMiddleware
from app.background_jobs.data_retention import start_scheduler, shutdown_scheduler
from app.api import health as health_router

from app.schemas.onboarding import (  # noqa: F401 (export for type generation)
    MinimalEnvelope,
    MetaData,
    PrerequisiteCheckRequest,
    PrerequisiteCheckResponse,
)
from app.schemas.deployment import (  # noqa: F401 (export for type generation)
    Platform,
    DeploymentStatus,
    LogLevel,
    DeploymentStep,
    StartDeploymentRequest,
    DeploymentLogEntry,
    DeploymentState,
    StartDeploymentResponse,
)
from app.schemas.webhook_verification import (  # noqa: F401 (export for type generation)
    WebhookStatusResponse,
    WebhookTestResponse,
    WebhookResubscribeResponse,
    FacebookWebhookStatus,
    ShopifyWebhookStatus,
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
    await init_db()
    start_scheduler()  # Story 2-7: Start data retention cleanup scheduler

    # Story 4-4: Start Shopify order polling scheduler
    try:
        from app.tasks.polling_scheduler import start_polling_scheduler

        await start_polling_scheduler()
    except Exception as e:
        # Log but don't fail startup if polling scheduler fails
        import structlog

        structlog.get_logger().warning("polling_scheduler_startup_failed", error=str(e))

    yield
    # Shutdown
    # Story 4-4: Shutdown Shopify order polling scheduler
    try:
        from app.tasks.polling_scheduler import shutdown_polling_scheduler

        await shutdown_polling_scheduler()
    except Exception as e:
        import structlog

        structlog.get_logger().warning("polling_scheduler_shutdown_failed", error=str(e))

    shutdown_scheduler()  # Story 2-7: Shutdown scheduler gracefully
    await close_db()


# Create FastAPI application
app = FastAPI(
    title="Shopping Assistant Bot",
    description="AI-powered conversational commerce for Facebook Messenger",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS - limit to specific methods for better security
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings()["CORS_ORIGINS"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Webhook-Signature", "X-CSRF-Token"],
)

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
        "message": "Shopping Assistant Bot API",
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


# Exception handlers
@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle APIError exceptions with appropriate status codes.

    Args:
        request: The request object
        exc: The APIError exception

    Returns:
        JSONResponse with error details
    """
    status_code = get_error_status_code(exc.code)
    return JSONResponse(
        status_code=status_code,
        content=exc.to_dict(),
    )


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
app.include_router(health_router.router, prefix="/api/health", tags=["health"])
# Story 1.13: Bot Preview Mode
app.include_router(preview_router, prefix="/api/v1", tags=["preview"])
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
