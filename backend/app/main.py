"""FastAPI application main entry point.

Shopping Assistant Bot - AI-powered conversational commerce for Facebook Messenger.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.errors import APIError, ErrorCode
from app.core.database import init_db, close_db, engine


def get_error_status_code(error_code: ErrorCode) -> int:
    """Map error codes to appropriate HTTP status codes.

    Args:
        error_code: The ErrorCode to map

    Returns:
        HTTP status code
    """
    # 2xxx: Auth/Security errors -> 401/403
    if 2000 <= error_code < 3000:
        if error_code in (ErrorCode.AUTH_FAILED, ErrorCode.TOKEN_EXPIRED, ErrorCode.UNAUTHORIZED):
            return status.HTTP_401_UNAUTHORIZED
        return status.HTTP_403_FORBIDDEN

    # 6xxx: Cart/Checkout errors -> 400 or 404
    if 6000 <= error_code < 7000:
        if error_code in (ErrorCode.CART_NOT_FOUND, ErrorCode.CHECKOUT_EXPIRED, ErrorCode.CART_SESSION_EXPIRED):
            return status.HTTP_404_NOT_FOUND
        return status.HTTP_400_BAD_REQUEST

    # 7xxx: Conversation/Session errors -> 404 or 400
    if 7000 <= error_code < 8000:
        if error_code in (ErrorCode.SESSION_EXPIRED, ErrorCode.CONVERSATION_NOT_FOUND):
            return status.HTTP_404_NOT_FOUND
        return status.HTTP_400_BAD_REQUEST

    # 1xxx: General errors
    if error_code == ErrorCode.VALIDATION_ERROR:
        return status.HTTP_422_UNPROCESSABLE_ENTITY

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
    yield
    # Shutdown
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
    allow_headers=["Content-Type", "Authorization", "X-Webhook-Signature"],
)


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
async def health() -> dict[str, any]:
    """Health check endpoint with database connectivity."""
    health_status = {"status": "healthy", "database": "connected"}

    # Check database connectivity
    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["database"] = f"disconnected: {str(e)}"

    return health_status


# Exception handlers
@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError) -> tuple[dict, int]:
    """Handle APIError exceptions with appropriate status codes.

    Args:
        request: The request object
        exc: The APIError exception

    Returns:
        Tuple of (error response dict, HTTP status code)
    """
    status_code = get_error_status_code(exc.code)
    return exc.to_dict(), status_code


# Include API routes
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
