"""LLM Configuration API endpoints.

Provides endpoints for:
- Configuring LLM provider
- Getting current LLM status
- Testing LLM connection
- Updating LLM configuration
- Clearing LLM configuration
- Listing available providers
- Health check
"""

from __future__ import annotations

from typing import Any
from datetime import datetime
import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import APIError, ErrorCode
from app.core.security import encrypt_access_token, decrypt_access_token
from app.core.input_sanitizer import validate_test_prompt
from app.core.rate_limiter import check_llm_rate_limit
from app.models.llm_configuration import LLMConfiguration
from app.models.merchant import Merchant
from app.schemas.llm import (
    # Requests
    LLMConfigureRequest,
    LLMUpdateRequest,
    LLMTestRequest,
    # Responses
    LLMStatusResponse,
    LLMTestResponse,
    LLMProvidersResponse,
    LLMProviderInfo,
    LLMHealthResponse,
    LLMConfigureResponse,
    LLMUpdateResponse,
    LLMClearResponse,
    MinimalLLMEnvelope,
)
from app.services.llm.llm_factory import LLMProviderFactory
from app.services.llm.base_llm_service import LLMMessage


router = APIRouter()


@router.post("/configure", response_model=MinimalLLMEnvelope)
async def configure_llm(
    request: LLMConfigureRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(check_llm_rate_limit),
) -> dict[str, Any]:
    """Configure LLM provider for merchant.

    Validates configuration with test LLM call before saving.
    Rate limited: 1 request per 10 seconds per merchant.
    """
    # For now, use merchant_id=1 (TODO: get from auth)
    merchant_id = 1

    # Check if configuration already exists
    result = await db.execute(
        select(LLMConfiguration).where(
            LLMConfiguration.merchant_id == merchant_id
        )
    )
    existing_config = result.scalar_one_or_none()

    if existing_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LLM configuration already exists. Use update endpoint.",
        )

    # Prepare configuration based on provider
    if request.provider == "ollama":
        if not request.ollama_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ollama_config required for Ollama provider",
            )

        config = {
            "provider": "ollama",
            "ollama_url": request.ollama_config.ollama_url,
            "model": request.ollama_config.ollama_model,
        }
        api_key_encrypted = None
        cloud_model = None
        ollama_url = request.ollama_config.ollama_url
        ollama_model = request.ollama_config.ollama_model

    else:
        if not request.cloud_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="cloud_config required for cloud providers",
            )

        config = {
            "provider": request.cloud_config.provider,
            "api_key": request.cloud_config.api_key,
            "model": request.cloud_config.model,
        }
        # Encrypt API key
        api_key_encrypted = encrypt_access_token(request.cloud_config.api_key)
        cloud_model = request.cloud_config.model
        ollama_url = None
        ollama_model = None

    # Test connection before saving
    try:
        llm_service = LLMProviderFactory.create_provider(request.provider, config)
        is_connected = await llm_service.test_connection()

        if not is_connected:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "LLM connection test failed",
                    "troubleshooting": _get_troubleshooting_steps(request.provider),
                },
            )

    except APIError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": str(e),
                "troubleshooting": _get_troubleshooting_steps(request.provider),
            },
        )

    # Create configuration
    llm_config = LLMConfiguration(
        merchant_id=merchant_id,
        provider=request.provider,
        ollama_url=ollama_url,
        ollama_model=ollama_model,
        api_key_encrypted=api_key_encrypted,
        cloud_model=cloud_model,
        backup_provider=request.backup_provider,
        backup_api_key_encrypted=(
            encrypt_access_token(request.backup_api_key)
            if request.backup_api_key
            else None
        ),
        status="active",
        configured_at=datetime.utcnow(),
        last_test_at=datetime.utcnow(),
        test_result={"success": True, "tested_at": datetime.utcnow().isoformat()},
    )

    db.add(llm_config)
    await db.commit()
    await db.refresh(llm_config)

    # Prepare response
    model = ollama_model or cloud_model or "default"

    return {
        "data": {
            "message": "LLM provider configured successfully",
            "provider": request.provider,
            "model": model,
            "status": "active",
        },
        "meta": {
            "request_id": "config-llm",
            "timestamp": datetime.utcnow().isoformat(),
        },
    }


@router.get("/status", response_model=MinimalLLMEnvelope)
async def get_llm_status(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get current LLM configuration status."""
    merchant_id = 1  # TODO: get from auth

    result = await db.execute(
        select(LLMConfiguration).where(
            LLMConfiguration.merchant_id == merchant_id
        )
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LLM configuration not found",
        )

    # Determine model
    model = config.ollama_model or config.cloud_model or "default"

    return {
        "data": {
            "provider": config.provider,
            "model": model,
            "status": config.status,
            "configured_at": config.configured_at.isoformat(),
            "last_test_at": config.last_test_at.isoformat() if config.last_test_at else None,
            "test_result": config.test_result,
            "total_tokens_used": config.total_tokens_used,
            "total_cost_usd": config.total_cost_usd,
            "backup_provider": config.backup_provider,
        },
        "meta": {
            "request_id": "get-llm-status",
            "timestamp": datetime.utcnow().isoformat(),
        },
    }


@router.post("/test", response_model=MinimalLLMEnvelope)
async def test_llm(
    request: LLMTestRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Test LLM configuration with validation call."""
    merchant_id = 1  # TODO: get from auth

    # Validate test prompt for security (NFR-S6)
    is_safe, error_msg = validate_test_prompt(request.test_prompt)
    if not is_safe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Invalid test prompt",
                "message": error_msg,
            },
        )

    result = await db.execute(
        select(LLMConfiguration).where(
            LLMConfiguration.merchant_id == merchant_id
        )
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LLM configuration not found",
        )

    # Build service config
    service_config: dict[str, Any] = {
        "provider": config.provider,
        "model": config.ollama_model or config.cloud_model,
    }

    if config.provider == "ollama":
        service_config["ollama_url"] = config.ollama_url
    else:
        if config.api_key_encrypted:
            service_config["api_key"] = decrypt_access_token(
                config.api_key_encrypted
            )

    # Test connection
    try:
        llm_service = LLMProviderFactory.create_provider(
            config.provider, service_config
        )

        start_time = time.time()
        response = await llm_service.chat(
            [LLMMessage(role="user", content=request.test_prompt)]
        )
        latency = (time.time() - start_time) * 1000

        # Update test result
        config.last_test_at = datetime.utcnow()
        config.test_result = {
            "success": True,
            "latency_ms": latency,
            "tokens_used": response.tokens_used,
            "tested_at": datetime.utcnow().isoformat(),
        }
        await db.commit()

        return {
            "data": {
                "success": True,
                "provider": config.provider,
                "model": response.model,
                "response": response.content,
                "tokens_used": response.tokens_used,
                "latency_ms": latency,
                "error": None,
            },
            "meta": {
                "request_id": "test-llm",
                "timestamp": datetime.utcnow().isoformat(),
            },
        }

    except APIError as e:
        # Update test result with failure
        config.last_test_at = datetime.utcnow()
        config.test_result = {
            "success": False,
            "error": str(e),
            "tested_at": datetime.utcnow().isoformat(),
        }
        await db.commit()

        return {
            "data": {
                "success": False,
                "provider": config.provider,
                "model": config.ollama_model or config.cloud_model or "unknown",
                "response": "",
                "tokens_used": 0,
                "latency_ms": 0,
                "error": str(e),
            },
            "meta": {
                "request_id": "test-llm",
                "timestamp": datetime.utcnow().isoformat(),
            },
        }


@router.put("/update", response_model=MinimalLLMEnvelope)
async def update_llm(
    request: LLMUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update existing LLM configuration."""
    merchant_id = 1  # TODO: get from auth

    result = await db.execute(
        select(LLMConfiguration).where(
            LLMConfiguration.merchant_id == merchant_id
        )
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LLM configuration not found",
        )

    updated_fields = []

    # Update provider
    if request.provider:
        config.provider = request.provider
        updated_fields.append("provider")

    # Update Ollama config
    if request.ollama_url is not None:
        config.ollama_url = request.ollama_url
        updated_fields.append("ollama_url")

    if request.ollama_model is not None:
        config.ollama_model = request.ollama_model
        updated_fields.append("ollama_model")

    # Update cloud config
    if request.api_key is not None:
        config.api_key_encrypted = encrypt_access_token(request.api_key)
        updated_fields.append("api_key")

    if request.model is not None:
        config.cloud_model = request.model
        updated_fields.append("model")

    # Update backup config
    if request.backup_provider is not None:
        config.backup_provider = request.backup_provider
        updated_fields.append("backup_provider")

    if request.backup_api_key is not None:
        config.backup_api_key_encrypted = encrypt_access_token(
            request.backup_api_key
        )
        updated_fields.append("backup_api_key")

    if not updated_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    await db.commit()

    return {
        "data": {
            "message": "LLM configuration updated",
            "updated_fields": updated_fields,
        },
        "meta": {
            "request_id": "update-llm",
            "timestamp": datetime.utcnow().isoformat(),
        },
    }


@router.delete("/clear", response_model=MinimalLLMEnvelope)
async def clear_llm(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Clear LLM configuration."""
    merchant_id = 1  # TODO: get from auth

    result = await db.execute(
        select(LLMConfiguration).where(
            LLMConfiguration.merchant_id == merchant_id
        )
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LLM configuration not found",
        )

    await db.delete(config)
    await db.commit()

    return {
        "data": {
            "message": "LLM configuration cleared",
        },
        "meta": {
            "request_id": "clear-llm",
            "timestamp": datetime.utcnow().isoformat(),
        },
    }


@router.get("/providers", response_model=MinimalLLMEnvelope)
async def get_providers() -> dict[str, Any]:
    """List available LLM providers with pricing info."""
    providers = LLMProviderFactory.get_available_providers()

    return {
        "data": {
            "providers": providers,
        },
        "meta": {
            "request_id": "get-providers",
            "timestamp": datetime.utcnow().isoformat(),
        },
    }


@router.get("/health", response_model=MinimalLLMEnvelope)
async def health_check(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Health check endpoint for monitoring."""
    merchant_id = 1  # TODO: get from auth

    result = await db.execute(
        select(LLMConfiguration).where(
            LLMConfiguration.merchant_id == merchant_id
        )
    )
    config = result.scalar_one_or_none()

    health_status = {
        "router": "not_configured",
        "primary_provider": None,
        "backup_provider": None,
    }

    if config:
        # Build service config
        service_config: dict[str, Any] = {
            "provider": config.provider,
            "model": config.ollama_model or config.cloud_model,
        }

        if config.provider == "ollama":
            service_config["ollama_url"] = config.ollama_url
        elif config.api_key_encrypted:
            service_config["api_key"] = decrypt_access_token(
                config.api_key_encrypted
            )

        try:
            llm_service = LLMProviderFactory.create_provider(
                config.provider, service_config
            )
            health_status["primary_provider"] = await llm_service.health_check()
            health_status["router"] = "configured"
        except Exception:
            health_status["primary_provider"] = {
                "provider": config.provider,
                "status": "error",
                "error": "Failed to create service",
            }

    return {
        "data": health_status,
        "meta": {
            "request_id": "health-check",
            "timestamp": datetime.utcnow().isoformat(),
        },
    }


def _get_troubleshooting_steps(provider: str) -> list[str]:
    """Get troubleshooting steps for provider."""
    steps = {
        "ollama": [
            "Verify Ollama is running: curl http://localhost:11434/api/tags",
            "Check Ollama logs for errors",
            "Ensure model is downloaded: ollama pull llama3",
            "Verify firewall allows connection to Ollama port",
        ],
        "openai": [
            "Verify API key is valid",
            "Check API key has sufficient credits",
            "Verify no rate limits exceeded",
            "Check OpenAI service status: https://status.openai.com",
        ],
        "anthropic": [
            "Verify API key is valid",
            "Check API key has sufficient credits",
            "Verify correct API version in headers",
            "Check Anthropic service status",
        ],
        "gemini": [
            "Verify API key is valid",
            "Enable Gemini API in Google Cloud Console",
            "Check API quota limits",
            "Verify model name is correct",
        ],
        "glm": [
            "Verify API key is valid",
            "Check Zhipu AI account status",
            "Verify sufficient API credits",
            "Check API endpoint accessibility",
        ],
    }
    return steps.get(provider, ["Check provider configuration and credentials"])
