"""CSRF token endpoint for token retrieval (NFR-S8).

This endpoint provides CSRF tokens to clients for use in state-changing
operations. The token is set as an httpOnly cookie and also returned
in the response body for inclusion in request headers.

NFR-S8: CSRF tokens for state-changing operations
- CSRF tokens for all POST/PUT/DELETE operations
- Double-submit cookie pattern
- Token validation on state-changing endpoints
- Per-session token generation
- Secure token storage (httpOnly, secure, sameSite)
"""

from __future__ import annotations

import uuid
from fastapi import APIRouter, Request, Response, HTTPException, status
from fastapi.responses import JSONResponse

from app.core.csrf import (
    CSRFProtection,
    get_csrf_protection,
    init_csrf_protection,
    CSRFTokenError,
)
from app.core.config import settings

router = APIRouter()

# Initialize CSRF protection
# In debug mode, use a test key for development
secret_key = settings()["SECRET_KEY"]
if settings()["DEBUG"] and secret_key == "dev-secret-key-DO-NOT-USE-IN-PRODUCTION":
    # Generate a test key for debug mode
    import secrets
    secret_key = secrets.token_urlsafe(32)

_csrf: CSRFProtection = init_csrf_protection(secret_key)


@router.get("/csrf-token")
async def get_csrf_token(request: Request) -> JSONResponse:
    """Get CSRF token for session.

    This endpoint generates a new CSRF token for the session and returns it
    both in the response body and as an httpOnly, secure, sameSite cookie.

    The client should:
    1. Store the token from the response body
    2. Include it in subsequent state-changing requests via X-CSRF-Token header
    3. The cookie will be automatically sent by the browser

    Example:
        # Get CSRF token
        response = await fetch('/api/v1/csrf-token')
        csrfToken = await response.text()

        # Use in state-changing request
        fetch('/api/checkout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrfToken
            },
            body: JSON.stringify(cartItems)
        })

    Returns:
        JSONResponse with CSRF token
    """
    try:
        # Generate session ID (in production, use actual session)
        session_id = str(uuid.uuid4())

        # Generate CSRF token
        token = _csrf.generate_token(session_id)

        # Create response with token in body
        response_data = {
            "csrf_token": token,
            "session_id": session_id,
            "max_age": 3600,  # 1 hour
        }

        response = JSONResponse(content=response_data)

        # Set CSRF token as httpOnly cookie
        _csrf.set_csrf_cookie(response, token)

        return response

    except CSRFTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": 1002,
                "message": "Failed to generate CSRF token",
                "details": str(e),
            },
        )


@router.post("/csrf-token/refresh")
async def refresh_csrf_token(request: Request) -> JSONResponse:
    """Refresh CSRF token for session.

    This endpoint generates a new CSRF token for an existing session.
    The old token is invalidated.

    Returns:
        JSONResponse with new CSRF token
    """
    try:
        # Get old session ID from cookie if available
        old_token = request.cookies.get("csrf_token")
        session_id = None

        if old_token:
            session_id = _csrf.parse_session_id_from_token(old_token)

        # Generate new session ID if none exists
        if not session_id:
            session_id = str(uuid.uuid4())

        # Generate new CSRF token
        new_token = _csrf.generate_token(session_id)

        # Create response
        response_data = {
            "csrf_token": new_token,
            "session_id": session_id,
            "max_age": 3600,  # 1 hour
        }

        response = JSONResponse(content=response_data)

        # Set new CSRF token cookie
        _csrf.set_csrf_cookie(response, new_token)

        return response

    except CSRFTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": 1002,
                "message": "Failed to refresh CSRF token",
                "details": str(e),
            },
        )


@router.delete("/csrf-token")
async def clear_csrf_token(request: Request) -> JSONResponse:
    """Clear CSRF token from session.

    This endpoint invalidates the current CSRF token by clearing it from
    the client's cookies.

    Returns:
        JSONResponse confirming token deletion
    """
    response = JSONResponse(content={"message": "CSRF token cleared"})

    # Clear CSRF token cookie
    _csrf.clear_csrf_cookie(response)

    return response


@router.get("/csrf-token/validate")
async def validate_csrf_token(request: Request) -> JSONResponse:
    """Validate current CSRF token.

    This endpoint checks if the current CSRF token is valid without
    consuming it (useful for checking token status).

    Returns:
        JSONResponse with validation result
    """
    # Get token from header
    token = _csrf.extract_token_from_headers(request.headers)

    # Validate token
    is_valid = _csrf.validate_token(request, token)

    return JSONResponse(
        content={
            "valid": is_valid,
            "message": "CSRF token is valid" if is_valid else "CSRF token is invalid or missing",
        }
    )
