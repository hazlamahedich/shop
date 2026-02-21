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
import structlog

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
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
    # Provider Switching (Story 3.4)
    SwitchProviderRequest,
    SwitchProviderResponse,
    ProviderValidationRequest,
    ProviderValidationResponse,
    ProviderListResponse,
    CurrentProviderInfo,
    ProviderMetadata,
    # Model Discovery
    DiscoveredModel,
    ModelDiscoveryResponse,
    ModelPricing,
)
from app.services.llm.llm_factory import LLMProviderFactory
from app.services.llm.base_llm_service import LLMMessage
from app.services.messaging.message_processor import MessageProcessor
from app.schemas.messaging import FacebookWebhookPayload, FacebookEntry


logger = structlog.get_logger(__name__)
router = APIRouter()


def _get_merchant_id_from_request(request: Request) -> int:
    """Extract merchant_id from authenticated request.

    Uses request.state.merchant_id set by authentication middleware.
    Falls back to X-Merchant-Id header in DEBUG mode or X-Test-Mode for testing.
    Defaults to merchant_id=1 for development when no auth is present.

    Args:
        request: FastAPI Request object

    Returns:
        Merchant ID from authentication or default

    Raises:
        HTTPException: If not in DEBUG mode and no merchant_id is available
    """
    # Try to get from request.state (set by auth middleware)
    merchant_id = getattr(request.state, "merchant_id", None)

    if merchant_id:
        return merchant_id

    # Check for IS_TESTING environment variable - allow default merchant 1
    if settings().get("IS_TESTING"):
        return 1

    # Check for X-Test-Mode header - requires explicit X-Merchant-Id
    if request.headers.get("X-Test-Mode", "").lower() == "true":
        merchant_id_header = request.headers.get("X-Merchant-Id")
        if merchant_id_header:
            try:
                return int(merchant_id_header)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid X-Merchant-Id header format",
                )
        # Return 1 as default when X-Test-Mode is set (for API testing)
        return 1

    # DEBUG mode: Allow X-Merchant-Id header for easier testing
    if settings()["DEBUG"]:
        merchant_id_header = request.headers.get("X-Merchant-Id")
        if merchant_id_header:
            try:
                return int(merchant_id_header)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid X-Merchant-Id header format",
                )
        # Only default to merchant 1 if explicitly provided via X-Merchant-Id
        # Otherwise require authentication even in DEBUG mode for security
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide X-Merchant-Id header for testing.",
        )

    # Production: Require authentication
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
    )


@router.post("/configure", response_model=MinimalLLMEnvelope)
async def configure_llm(
    request_obj: LLMConfigureRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(check_llm_rate_limit),
) -> dict[str, Any]:
    """Configure LLM provider for merchant.

    Validates configuration with test LLM call before saving.
    Rate limited: 1 request per 10 seconds per merchant.
    """
    # Get merchant_id from authentication
    merchant_id = _get_merchant_id_from_request(http_request)

    # Check if configuration already exists
    result = await db.execute(
        select(LLMConfiguration).where(LLMConfiguration.merchant_id == merchant_id)
    )
    existing_config = result.scalar_one_or_none()

    if existing_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LLM configuration already exists. Use update endpoint.",
        )

    # Prepare configuration based on provider
    if request_obj.provider == "ollama":
        if not request_obj.ollama_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ollama_config required for Ollama provider",
            )

        config = {
            "provider": "ollama",
            "ollama_url": request_obj.ollama_config.ollama_url,
            "model": request_obj.ollama_config.ollama_model,
        }
        api_key_encrypted = None
        cloud_model = None
        ollama_url = request_obj.ollama_config.ollama_url
        ollama_model = request_obj.ollama_config.ollama_model

    else:
        if not request_obj.cloud_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="cloud_config required for cloud providers",
            )

        config = {
            "provider": request_obj.cloud_config.provider,
            "api_key": request_obj.cloud_config.api_key,
            "model": request_obj.cloud_config.model,
        }
        # Encrypt API key
        api_key_encrypted = encrypt_access_token(request_obj.cloud_config.api_key)
        cloud_model = request_obj.cloud_config.model
        ollama_url = None
        ollama_model = None

    # Test connection before saving
    try:
        llm_service = LLMProviderFactory.create_provider(request_obj.provider, config)
        is_connected = await llm_service.test_connection()

        if not is_connected:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "LLM connection test failed",
                    "troubleshooting": _get_troubleshooting_steps(request_obj.provider),
                },
            )

    except APIError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": str(e),
                "troubleshooting": _get_troubleshooting_steps(request_obj.provider),
            },
        )

    # Create configuration
    llm_config = LLMConfiguration(
        merchant_id=merchant_id,
        provider=request_obj.provider,
        ollama_url=ollama_url,
        ollama_model=ollama_model,
        api_key_encrypted=api_key_encrypted,
        cloud_model=cloud_model,
        backup_provider=request_obj.backup_provider,
        backup_api_key_encrypted=(
            encrypt_access_token(request_obj.backup_api_key) if request_obj.backup_api_key else None
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
            "provider": request_obj.provider,
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
    http_request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get current LLM configuration status."""
    merchant_id = _get_merchant_id_from_request(http_request)

    result = await db.execute(
        select(LLMConfiguration).where(LLMConfiguration.merchant_id == merchant_id)
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
    request_obj: LLMTestRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Test LLM configuration with validation call."""
    merchant_id = _get_merchant_id_from_request(http_request)

    # Validate test prompt for security (NFR-S6)
    is_safe, error_msg = validate_test_prompt(request_obj.test_prompt)
    if not is_safe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Invalid test prompt",
                "message": error_msg,
            },
        )

    result = await db.execute(
        select(LLMConfiguration).where(LLMConfiguration.merchant_id == merchant_id)
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
            service_config["api_key"] = decrypt_access_token(config.api_key_encrypted)

    # Test connection
    try:
        llm_service = LLMProviderFactory.create_provider(config.provider, service_config)

        start_time = time.time()
        response = await llm_service.chat(
            [LLMMessage(role="user", content=request_obj.test_prompt)]
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
    request_obj: LLMUpdateRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update existing LLM configuration."""
    merchant_id = _get_merchant_id_from_request(http_request)

    result = await db.execute(
        select(LLMConfiguration).where(LLMConfiguration.merchant_id == merchant_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LLM configuration not found",
        )

    updated_fields = []

    # Update provider
    if request_obj.provider:
        config.provider = request_obj.provider
        updated_fields.append("provider")

    # Update Ollama config
    if request_obj.ollama_url is not None:
        config.ollama_url = request_obj.ollama_url
        updated_fields.append("ollama_url")

    if request_obj.ollama_model is not None:
        config.ollama_model = request_obj.ollama_model
        updated_fields.append("ollama_model")

    # Update cloud config
    if request_obj.api_key is not None:
        config.api_key_encrypted = encrypt_access_token(request_obj.api_key)
        updated_fields.append("api_key")

    if request_obj.model is not None:
        config.cloud_model = request_obj.model
        updated_fields.append("model")

    # Update backup config
    if request_obj.backup_provider is not None:
        config.backup_provider = request_obj.backup_provider
        updated_fields.append("backup_provider")

    if request_obj.backup_api_key is not None:
        config.backup_api_key_encrypted = encrypt_access_token(request_obj.backup_api_key)
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
    http_request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Clear LLM configuration."""
    merchant_id = _get_merchant_id_from_request(http_request)

    result = await db.execute(
        select(LLMConfiguration).where(LLMConfiguration.merchant_id == merchant_id)
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


@router.get("/models/{provider_id}", response_model=MinimalLLMEnvelope)
async def get_provider_models(
    provider_id: str,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get available models for a specific provider.

    Fetches models from:
    - OpenRouter API for cloud providers (OpenAI, Anthropic, Gemini, GLM)
    - Local Ollama instance + Ollama library for Ollama provider

    Results are cached for 24 hours to avoid repeated API calls.
    """
    from app.services.llm.model_discovery_service import get_model_discovery_service

    valid_providers = {"ollama", "openai", "anthropic", "gemini", "glm"}
    if provider_id not in valid_providers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider_id. Allowed: {', '.join(valid_providers)}",
        )

    ollama_url = None
    if provider_id == "ollama":
        merchant_id = _get_merchant_id_from_request(http_request)
        result = await db.execute(
            select(LLMConfiguration).where(LLMConfiguration.merchant_id == merchant_id)
        )
        config = result.scalar_one_or_none()
        ollama_url = config.ollama_url if config else "http://localhost:11434"

    discovery_service = get_model_discovery_service()
    cache_info_before = discovery_service.get_cache_info()

    models = await discovery_service.get_models_for_provider(provider_id, ollama_url)

    cache_info_after = discovery_service.get_cache_info()
    cached = cache_info_before.get("keys", []) == cache_info_after.get("keys", [])

    discovered_models = []
    for model_data in models:
        try:
            pricing = model_data.get("pricing", {})
            discovered_models.append(
                DiscoveredModel(
                    id=model_data.get("id", ""),
                    name=model_data.get("name", model_data.get("id", "")),
                    provider=model_data.get("provider", provider_id),
                    description=model_data.get("description", ""),
                    context_length=model_data.get(
                        "contextLength", model_data.get("context_length", 4096)
                    ),
                    pricing=ModelPricing(
                        input_cost_per_million=pricing.get(
                            "inputCostPerMillion", pricing.get("input_cost_per_million", 0.0)
                        ),
                        output_cost_per_million=pricing.get(
                            "outputCostPerMillion", pricing.get("output_cost_per_million", 0.0)
                        ),
                        currency=pricing.get("currency", "USD"),
                    ),
                    is_local=model_data.get("isLocal", model_data.get("is_local", False)),
                    is_downloaded=model_data.get(
                        "isDownloaded", model_data.get("is_downloaded", False)
                    ),
                    features=model_data.get("features", []),
                )
            )
        except Exception as e:
            logger.warning("model_parse_failed", model_id=model_data.get("id"), error=str(e))
            continue

    return {
        "data": {
            "provider": provider_id,
            "models": [m.model_dump(by_alias=True) for m in discovered_models],
            "cached": cached,
            "cacheInfo": discovery_service.get_cache_info() if not cached else None,
        },
        "meta": {
            "request_id": "get-provider-models",
            "timestamp": datetime.utcnow().isoformat(),
        },
    }


@router.post("/models/refresh", response_model=MinimalLLMEnvelope)
async def refresh_models_cache(
    http_request: Request,
) -> dict[str, Any]:
    """Clear model cache and fetch fresh data.

    Use this to force refresh of model data from OpenRouter and Ollama.
    """
    from app.services.llm.model_discovery_service import get_model_discovery_service

    discovery_service = get_model_discovery_service()
    discovery_service.clear_cache()

    return {
        "data": {
            "message": "Model cache cleared. Next requests will fetch fresh data.",
            "cacheInfo": discovery_service.get_cache_info(),
        },
        "meta": {
            "request_id": "refresh-models-cache",
            "timestamp": datetime.utcnow().isoformat(),
        },
    }


@router.get("/health", response_model=MinimalLLMEnvelope)
async def health_check(
    http_request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Health check endpoint for monitoring."""
    merchant_id = _get_merchant_id_from_request(http_request)

    result = await db.execute(
        select(LLMConfiguration).where(LLMConfiguration.merchant_id == merchant_id)
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
            service_config["api_key"] = decrypt_access_token(config.api_key_encrypted)

        try:
            llm_service = LLMProviderFactory.create_provider(config.provider, service_config)
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


@router.post("/chat", response_model=MinimalLLMEnvelope)
async def chat_with_bot(
    request_obj: dict[str, str],
    http_request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Test chat endpoint for manual verification.

    Simulates a Facebook Messenger message and processes it through
    the full Shopping Assistant Bot flow.
    """
    message_text = request_obj.get("message", "")
    if not message_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message text required",
        )

    # Use a fixed test PSID for the simulation
    test_psid = "TEST_USER_123"

    # Create a simulated webhook payload
    simulated_payload = FacebookWebhookPayload(
        object="page",
        entry=[
            FacebookEntry(
                id="PAGE_123",
                time=int(time.time() * 1000),
                messaging=[
                    {
                        "sender": {"id": test_psid},
                        "recipient": {"id": "PAGE_123"},
                        "timestamp": int(time.time() * 1000),
                        "message": {"text": message_text},
                    }
                ],
            )
        ],
    )

    try:
        # Process the message through the actual flow
        processor = MessageProcessor()
        response = await processor.process_message(simulated_payload)

        return {
            "data": {
                "response": response.text,
                "recipient_id": response.recipient_id,
            },
            "meta": {
                "request_id": "simulated-chat",
                "timestamp": datetime.utcnow().isoformat(),
            },
        }

    except Exception as e:
        raise APIError(
            ErrorCode.UNKNOWN_ERROR,
            f"Failed to process chat message: {str(e)}",
        ) from e


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


# Provider Switching Endpoints (Story 3.4)


@router.post("/switch-provider", response_model=MinimalLLMEnvelope)
async def switch_llm_provider(
    request_obj: SwitchProviderRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(check_llm_rate_limit),
) -> dict[str, Any]:
    """Switch merchant's LLM provider with validation.

    Validates new provider configuration before applying changes.
    Previous provider remains active if validation fails.

    Rate limited: 1 request per 10 seconds per merchant.
    """
    # Get merchant_id from authentication
    merchant_id = _get_merchant_id_from_request(http_request)

    from app.services.llm.provider_switch_service import (
        ProviderSwitchService,
        ProviderValidationError,
    )

    try:
        service = ProviderSwitchService(db)

        result = await service.switch_provider(
            merchant_id=merchant_id,
            provider_id=request_obj.provider_id,
            api_key=request_obj.api_key,
            server_url=request_obj.server_url,
            model=request_obj.model,
        )

        return {
            "data": result,
            "meta": {
                "request_id": "switch-provider",
                "timestamp": datetime.utcnow().isoformat(),
            },
        }

    except ProviderValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": int(e.error_code),
                "message": e.message,
                "details": e.details,
            },
        )


@router.post("/validate-provider", response_model=MinimalLLMEnvelope)
async def validate_llm_provider(
    request_obj: ProviderValidationRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(check_llm_rate_limit),
) -> dict[str, Any]:
    """Validate LLM provider configuration without switching.

    Makes a test call to verify provider connectivity and credentials.
    Use this endpoint to validate configuration before switching.

    Returns validation result with test response and latency.
    """
    # Get merchant_id from authentication
    merchant_id = _get_merchant_id_from_request(http_request)

    from app.services.llm.provider_switch_service import (
        ProviderSwitchService,
        ProviderValidationError,
    )

    try:
        service = ProviderSwitchService(db)

        result = await service.validate_provider_config(
            merchant_id=merchant_id,
            provider_id=request_obj.provider_id,
            api_key=request_obj.api_key,
            server_url=request_obj.server_url,
            model=request_obj.model,
        )

        return {
            "data": result,
            "meta": {
                "request_id": "validate-provider",
                "timestamp": datetime.utcnow().isoformat(),
            },
        }

    except ProviderValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": int(e.error_code),
                "message": e.message,
                "details": e.details,
            },
        )


@router.get("/providers-list", response_model=MinimalLLMEnvelope)
async def get_providers_list(
    http_request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get list of available providers with current provider indicator.

    Returns all available LLM providers with pricing, features, and models.
    Includes current provider status and estimated monthly costs.
    """
    # Get merchant_id from authentication
    merchant_id = _get_merchant_id_from_request(http_request)
    logger.info(
        "providers_list_request",
        merchant_id=merchant_id,
        has_state=getattr(http_request.state, "merchant_id", None),
    )

    from app.services.llm.provider_switch_service import (
        ProviderSwitchService,
        ProviderValidationError,
    )

    service = ProviderSwitchService(db)

    try:
        # Get current provider info
        current_provider_result = await service.get_current_provider(merchant_id)
        current_provider_id = current_provider_result["provider"]["id"]
    except ProviderValidationError:
        # No LLM configuration found - return defaults with ollama as active
        current_provider_result = {
            "provider": {
                "id": "ollama",
                "name": "Ollama",
                "description": "Local LLM for development",
                "model": "llama3",
            },
            "status": "not_configured",
            "configured_at": None,
            "last_test_at": None,
            "total_tokens_used": 0,
            "total_cost_usd": 0.0,
        }
        current_provider_id = "ollama"

    # Get available providers from factory
    available_providers = LLMProviderFactory.get_available_providers()

    providers_with_metadata = []
    for provider in available_providers:
        is_active = provider["id"] == current_provider_id

        # Calculate estimated monthly cost (simple placeholder calculation)
        # TODO: Use actual merchant usage data for accurate estimates
        estimated_cost = 0.0
        if provider["pricing"]["inputCost"] > 0:
            # Estimate based on 100K input + 50K output tokens per month
            estimated_cost = (100000 / 1000000) * provider["pricing"]["inputCost"] + (
                50000 / 1000000
            ) * provider["pricing"]["outputCost"]

        providers_with_metadata.append(
            {
                **provider,
                "isActive": is_active,
                "estimatedMonthlyCost": round(estimated_cost, 2),
            }
        )

    return {
        "data": {
            "currentProvider": {
                **current_provider_result["provider"],
                "status": current_provider_result["status"],
                "configuredAt": current_provider_result["configured_at"],
                "totalTokensUsed": current_provider_result["total_tokens_used"],
                "totalCostUsd": current_provider_result["total_cost_usd"],
            },
            "providers": providers_with_metadata,
        },
        "meta": {
            "request_id": "providers-list",
            "timestamp": datetime.utcnow().isoformat(),
        },
    }
