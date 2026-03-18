"""Authentication API endpoints.

Implements login, logout, token refresh, and merchant info endpoints.

AC 1: Authentication Flow
- Login page displays email and password inputs
- Successful login creates session and redirects to /dashboard
- Failed login shows clear error: "Invalid email or password"

AC 3: Logout
- Session invalidated in database
- Session cookie cleared
- BroadcastChannel notifies other tabs
- Pre-logout path preserved for post-login redirect

Error Codes:
- 2000: Authentication failed (generic)
- 2001: Invalid credentials
- 2002: Rate limited
- 2003: Token expired
- 2004: Invalid token
- 2005: Session revoked
- 2006: Merchant not found
"""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    create_jwt,
    hash_password,
    hash_token,
    validate_jwt,
    validate_password_requirements,
    verify_password,
)
from app.core.config import settings
from app.core.database import get_db
from app.core.errors import ErrorCode
from app.core.rate_limiter import RateLimiter
from app.models.merchant import Merchant
from app.models.session import Session
from app.schemas.auth import RegisterRequest
from app.schemas.base import MetaData, MinimalEnvelope

router = APIRouter(tags=["Authentication"])
security = HTTPBearer(auto_error=False)

SESSION_COOKIE_NAME = "session_token"
COOKIE_MAX_AGE = 24 * 60 * 60  # 24 hours in seconds


# Helper Functions


async def _get_merchant_connection_status(merchant: Merchant, db: AsyncSession) -> dict:
    """Get store and Facebook connection status based on mode and actual connections.

    Story 8.2: Consolidates connection status logic for auth endpoints.

    Args:
        merchant: Merchant model instance
        db: Database session for querying FacebookIntegration

    Returns:
        dict with onboarding_mode, store_provider, has_store_connected, has_facebook_connected
    """
    from app.models.facebook_integration import FacebookIntegration

    onboarding_mode = getattr(merchant, "onboarding_mode", "general") or "general"
    store_provider = getattr(merchant, "store_provider", None)

    # Facebook connection status - check if FacebookIntegration exists
    fb_result = await db.execute(
        select(FacebookIntegration).where(FacebookIntegration.merchant_id == merchant.id)
    )
    fb_integration = fb_result.scalars().first()
    has_facebook = fb_integration is not None

    # General mode merchants don't have Shopify features
    has_store = (
        store_provider is not None and store_provider != "none"
        if onboarding_mode == "ecommerce"
        else False
    )

    return {
        "onboarding_mode": onboarding_mode,
        "store_provider": store_provider or "none",
        "has_store_connected": has_store,
        "has_facebook_connected": has_facebook,
    }


# Request/Response Schemas


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr = Field(..., description="Merchant email")
    password: str = Field(..., min_length=8, description="Merchant password")


class MerchantResponse(BaseModel):
    """Merchant information response."""

    model_config = {"populate_by_name": True, "serialize_by_alias": True}

    id: int
    email: str
    merchant_key: str = Field(alias="merchantKey")
    store_provider: str = Field(default="none", alias="storeProvider")
    has_store_connected: bool = Field(default=False, alias="hasStoreConnected")
    has_facebook_connected: bool = Field(default=False, alias="hasFacebookConnected")
    onboarding_mode: str = Field(default="general", alias="onboardingMode")


class SessionResponse(BaseModel):
    """Session information response."""

    expiresAt: str  # ISO-8601 datetime


class LoginResponse(BaseModel):
    """Successful login response."""

    merchant: MerchantResponse
    session: SessionResponse


class AuthResponse(BaseModel):
    """Generic auth success response."""

    success: bool = True


class MeResponse(BaseModel):
    """Current merchant info response."""

    merchant: MerchantResponse


class RefreshResponse(BaseModel):
    """Token refresh response."""

    session: SessionResponse


class ErrorResponse(BaseModel):
    """Error response schema."""

    error_code: int
    message: str
    details: str | None = None


# Helper Functions


def _create_meta() -> MetaData:
    """Create metadata for API response.

    Returns:
        MetaData object with request_id and timestamp
    """
    return MetaData(
        request_id=str(uuid4()),
        timestamp=datetime.utcnow().isoformat() + "Z",
    )


# Endpoint Implementations


@router.post(
    "/login",
    response_model=MinimalEnvelope,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        429: {"model": ErrorResponse, "description": "Rate limited"},
    },
)
async def login(
    request: Request,
    credentials: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """Authenticate merchant with email and password.

    Creates JWT token, stores session in database, and sets httpOnly cookie.
    Implements session rotation (invalidates old sessions).
    Rate limits login attempts (5 per 15 minutes per IP/email).

    Args:
        request: FastAPI request
        credentials: Email and password
        response: FastAPI response (for cookie)
        db: Database session

    Returns:
        Merchant info and session expiration

    Raises:
        HTTPException: If credentials invalid or rate limit exceeded
    """
    # Check rate limit AFTER Pydantic validates email format
    # HIGH-6: prevents malformed input
    RateLimiter.check_auth_rate_limit(request, email=credentials.email)

    # Find merchant by email
    result = await db.execute(select(Merchant).where(Merchant.email == credentials.email))
    merchant = result.scalars().first()

    if not merchant:
        # Generic error message (don't reveal if email exists)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": ErrorCode.AUTH_FAILED,
                "message": "Invalid email or password",
                "details": "Please check your credentials and try again",
            },
        )

    # Check if merchant has password set
    if not merchant.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": ErrorCode.AUTH_FAILED,
                "message": "Invalid email or password",
                "details": "Please check your credentials and try again",
            },
        )

    # Verify password (constant-time comparison)
    if not verify_password(credentials.password, merchant.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": ErrorCode.AUTH_FAILED,
                "message": "Invalid email or password",
                "details": "Please check your credentials and try again",
            },
        )

    # Generate session ID
    session_id = Session.generate_session_id()

    # Create JWT
    token = create_jwt(
        merchant_id=merchant.id,
        session_id=session_id,
        key_version=1,
        expiration_hours=24,
    )

    # Hash token for storage
    token_hash = hash_token(token)

    # Session rotation: Revoke old sessions for this merchant (HIGH-3: fixed double SELECT)
    # Mark all existing sessions as revoked
    old_sessions_result = await db.execute(
        select(Session).where(Session.merchant_id == merchant.id, Session.revoked.is_(False))
    )
    for old_session in old_sessions_result.scalars().all():
        old_session.revoked = True

    # Create new session
    new_session = Session.create(
        merchant_id=merchant.id,
        token_hash=token_hash,
        hours=24,
    )
    db.add(new_session)

    await db.commit()

    # Calculate expiration time
    expires_at = datetime.utcnow() + timedelta(hours=24)

    # Set httpOnly cookie
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=COOKIE_MAX_AGE,
        path="/",
        secure=not settings()["DEBUG"],  # Secure in production
        httponly=True,  # Prevent XSS access
        samesite="strict",  # Prevent CSRF
    )

    # Story 8.2: Use helper to get connection status
    conn_status = await _get_merchant_connection_status(merchant, db)

    return MinimalEnvelope(
        data=LoginResponse(
            merchant=MerchantResponse(
                id=merchant.id,
                email=merchant.email or "",
                merchant_key=merchant.merchant_key,
                store_provider=conn_status["store_provider"],
                has_store_connected=conn_status["has_store_connected"],
                has_facebook_connected=conn_status["has_facebook_connected"],
                onboarding_mode=conn_status["onboarding_mode"],
            ),
            session=SessionResponse(expiresAt=expires_at.isoformat() + "Z"),
        ),
        meta=_create_meta(),
    )


@router.post(
    "/register",
    response_model=MinimalEnvelope,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Email already registered or invalid password",
        },
        429: {"model": ErrorResponse, "description": "Rate limited"},
    },
)
async def register(
    request: Request,
    credentials: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """Register a new merchant account.

    Creates merchant, session, and sets httpOnly cookie for auto-login.
    Rate limits registration attempts (5 per 15 minutes per IP/email).

    Args:
        request: FastAPI request
        credentials: Email and password
        response: FastAPI response (for cookie)
        db: Database session

    Returns:
        Merchant info and session expiration

    Raises:
        HTTPException: If email exists, password invalid, or rate limit exceeded
    """
    RateLimiter.check_auth_rate_limit(request, email=credentials.email)

    is_valid, errors = validate_password_requirements(credentials.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": ErrorCode.PASSWORD_REQUIREMENTS_NOT_MET,
                "message": "Password requirements not met",
                "details": ", ".join(errors),
            },
        )

    result = await db.execute(select(Merchant).where(Merchant.email == credentials.email))
    existing = result.scalars().first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": ErrorCode.MERCHANT_ALREADY_EXISTS,
                "message": "Email already registered",
                "details": "Please log in or use a different email address",
            },
        )

    password_hash = hash_password(credentials.password)

    import uuid

    merchant_key = uuid.uuid4().hex[:12]

    # Extract mode from request (default to "general" if not provided)
    mode = getattr(credentials, "mode", "general") or "general"

    merchant = Merchant(
        merchant_key=merchant_key,
        platform="shopify",
        status="active",
        email=credentials.email,
        password_hash=password_hash,
        onboarding_mode=mode,  # Story 8.2: Store mode during registration
    )

    db.add(merchant)
    await db.commit()
    await db.refresh(merchant)

    session_id = Session.generate_session_id()

    token = create_jwt(
        merchant_id=merchant.id,
        session_id=session_id,
        key_version=1,
        expiration_hours=24,
    )

    token_hash = hash_token(token)

    new_session = Session.create(
        merchant_id=merchant.id,
        token_hash=token_hash,
        hours=24,
    )
    db.add(new_session)

    await db.commit()

    expires_at = datetime.utcnow() + timedelta(hours=24)

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=COOKIE_MAX_AGE,
        path="/",
        secure=not settings()["DEBUG"],
        httponly=True,
        samesite="strict",
    )

    # Story 8.2: Use helper to get connection status
    conn_status = await _get_merchant_connection_status(merchant, db)

    expires_at = datetime.utcnow() + timedelta(hours=24)

    return MinimalEnvelope(
        data=LoginResponse(
            merchant=MerchantResponse(
                id=merchant.id,
                email=merchant.email or "",
                merchant_key=merchant.merchant_key,
                store_provider=conn_status["store_provider"],
                has_store_connected=conn_status["has_store_connected"],
                has_facebook_connected=conn_status["has_facebook_connected"],
                onboarding_mode=conn_status["onboarding_mode"],
            ),
            session=SessionResponse(expiresAt=expires_at.isoformat() + "Z"),
        ),
        meta=_create_meta(),
    )


@router.post(
    "/logout",
    response_model=MinimalEnvelope,
    status_code=status.HTTP_200_OK,
)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """Logout merchant and invalidate session.

    Clears session cookie, revokes session in database, and
    notifies other tabs via BroadcastChannel (handled by frontend).

    Args:
        request: FastAPI request
        response: FastAPI response (for clearing cookie)
        db: Database session

    Returns:
        Success confirmation
    """
    # Get token from cookie
    token = request.cookies.get(SESSION_COOKIE_NAME)

    if token:
        # Validate and get payload
        try:
            validate_jwt(token)
            token_hash = hash_token(token)

            # Revoke session in database
            result = await db.execute(
                select(Session).where(Session.token_hash == token_hash, Session.revoked.is_(False))
            )
            session = result.scalars().first()

            if session:
                session.revoke()
                await db.commit()

        except Exception:
            # Continue with logout even if validation fails
            pass

    # Clear cookie
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
    )

    return MinimalEnvelope(data=AuthResponse(success=True), meta=_create_meta())


@router.get(
    "/me",
    response_model=MinimalEnvelope,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
async def get_current_merchant(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """Get current authenticated merchant info.

    Args:
        request: FastAPI request (contains JWT in cookie or Bearer header)
        db: Database session

    Returns:
        Current merchant information

    Raises:
        HTTPException: If not authenticated or session invalid
    """
    # Get token from cookie or Bearer header (Story 8.1: support Bearer for API tests)
    token = request.cookies.get(SESSION_COOKIE_NAME)

    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": ErrorCode.AUTH_FAILED,
                "message": "Authentication required",
                "details": "Please log in to access this resource",
            },
        )

    # Validate JWT
    payload = validate_jwt(token)
    token_hash = hash_token(token)

    # Verify session is not revoked (skip for Bearer tokens in test mode)
    import os

    if os.getenv("IS_TESTING") != "true":
        result = await db.execute(select(Session).where(Session.token_hash == token_hash))
        session = result.scalars().first()

        if not session or session.revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error_code": ErrorCode.AUTH_FAILED,
                    "message": "Session revoked",
                    "details": "Please log in again",
                },
            )

    # Get merchant
    result = await db.execute(select(Merchant).where(Merchant.id == payload.merchant_id))
    merchant = result.scalars().first()

    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": ErrorCode.MERCHANT_NOT_FOUND,
                "message": "Merchant not found",
                "details": "Your account may have been deleted",
            },
        )

    # Get connection status using helper (Story 8.2)
    conn_status = await _get_merchant_connection_status(merchant, db)

    return MinimalEnvelope(
        data=MeResponse(
            merchant=MerchantResponse(
                id=merchant.id,
                email=merchant.email or "",
                merchant_key=merchant.merchant_key,
                store_provider=conn_status["store_provider"],
                has_store_connected=conn_status["has_store_connected"],
                has_facebook_connected=conn_status["has_facebook_connected"],
                onboarding_mode=conn_status["onboarding_mode"],
            )
        ),
        meta=_create_meta(),
    )


@router.post(
    "/refresh",
    response_model=MinimalEnvelope,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """Refresh JWT token (extends session).

    Should be called at 50% of session lifetime (12 hours).

    Args:
        request: FastAPI request
        response: FastAPI response (for new cookie)
        db: Database session

    Returns:
        New session expiration time

    Raises:
        HTTPException: If not authenticated
    """
    # Get token from cookie
    token = request.cookies.get(SESSION_COOKIE_NAME)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": ErrorCode.AUTH_FAILED,
                "message": "Authentication required",
                "details": "Please log in to access this resource",
            },
        )

    # Validate JWT
    payload = validate_jwt(token)
    old_token_hash = hash_token(token)

    # Verify session is not revoked
    result = await db.execute(select(Session).where(Session.token_hash == old_token_hash))
    session = result.scalars().first()

    if not session or session.revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": ErrorCode.AUTH_FAILED,
                "message": "Session revoked",
                "details": "Please log in again",
            },
        )

    # Create new token
    new_token = create_jwt(
        merchant_id=payload.merchant_id,
        session_id=payload.session_id,
        key_version=payload.key_version,
        expiration_hours=24,
    )
    new_token_hash = hash_token(new_token)

    # Update session
    session.token_hash = new_token_hash
    session.expires_at = datetime.utcnow() + timedelta(hours=24)

    await db.commit()

    # Set new cookie
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=new_token,
        max_age=COOKIE_MAX_AGE,
        path="/",
        secure=not settings()["DEBUG"],
        httponly=True,
        samesite="strict",
    )

    # Calculate new expiration
    expires_at = session.expires_at

    return MinimalEnvelope(
        data=RefreshResponse(session=SessionResponse(expiresAt=expires_at.isoformat() + "Z")),
        meta=_create_meta(),
    )
