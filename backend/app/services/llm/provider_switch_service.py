"""LLM Provider Switching Service.

Handles provider validation, switching, and rollback logic.
Enables merchants to switch between LLM providers (Ollama, OpenAI, Anthropic, Gemini, GLM).
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import APIError, ErrorCode
from app.models.llm_configuration import LLMConfiguration
from app.models.merchant import Merchant
from app.services.llm.llm_factory import LLMProviderFactory


class ProviderValidationError(Exception):
    """Provider validation or switching error."""

    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(message)


class ProviderSwitchService:
    """Service for LLM provider switching operations.

    Handles:
    - Provider configuration validation
    - Provider switching with rollback on failure
    - Test calls to verify provider connectivity
    - Current provider retrieval
    """

    # API key format patterns for validation
    # Note: Some providers (glm) skip format validation and rely on API test
    API_KEY_PATTERNS = {
        "openai": re.compile(r"^sk-[a-zA-Z0-9]{32,}$"),  # OpenAI API key format
        "anthropic": re.compile(r"^sk-ant-[a-zA-Z0-9\-]{20,}$"),  # Anthropic API key
        "gemini": re.compile(r"^AIza[a-zA-Z0-9_\-]{33,}$"),  # Google API key (starts with AIza)
        # GLM keys vary in format - validation done via API test only
    }

    def __init__(self, db: AsyncSession) -> None:
        """Initialize provider switching service.

        Args:
            db: Database session for async operations
        """
        self.db = db
        self._factory = LLMProviderFactory()

    async def validate_provider_config(
        self,
        merchant_id: int,
        provider_id: str,
        api_key: Optional[str] = None,
        server_url: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Validate provider configuration with test call.

        Args:
            merchant_id: Merchant ID for authorization check
            provider_id: Provider to validate (ollama, openai, anthropic, gemini, glm)
            api_key: API key for cloud providers (required for non-Ollama)
            server_url: Ollama server URL (required for Ollama)
            model: Optional model override

        Returns:
            Validation result with provider info and test response

        Raises:
            ProviderValidationError: If validation fails
        """
        # Verify merchant exists
        merchant = await self._get_merchant(merchant_id)

        # Validate provider ID
        available_providers = self._factory.get_available_providers()
        provider_ids = [p["id"] for p in available_providers]

        if provider_id not in provider_ids:
            raise ProviderValidationError(
                ErrorCode.LLM_PROVIDER_NOT_FOUND,
                f"Unknown provider: {provider_id}. Available: {', '.join(provider_ids)}",
                {"available_providers": provider_ids},
            )

        # Validate provider-specific configuration
        is_ollama = provider_id == "ollama"

        if is_ollama:
            await self._validate_ollama_config(server_url)
            provider_config = {"server_url": server_url, "model": model or "llama3"}
        else:
            await self._validate_cloud_provider_config(provider_id, api_key)
            provider_config = {
                "api_key": api_key,
                "model": model or self._get_default_model(provider_id),
            }

        # Make test call to verify connectivity
        test_result = await self.test_provider_call(
            provider_id=provider_id,
            **provider_config,
        )

        return {
            "valid": True,
            "provider": {
                "id": provider_id,
                "name": next(p["name"] for p in available_providers if p["id"] == provider_id),
                "test_response": test_result.get("response", "Connection successful"),
                "latency_ms": test_result.get("latency_ms"),
            },
            "validated_at": datetime.utcnow().isoformat(),
        }

    async def switch_provider(
        self,
        merchant_id: int,
        provider_id: str,
        api_key: Optional[str] = None,
        server_url: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Switch merchant's LLM provider with validation.

        Validates new provider configuration before applying changes.
        Rolls back to previous provider if validation fails.

        Args:
            merchant_id: Merchant ID
            provider_id: New provider ID
            api_key: API key for cloud providers
            server_url: Ollama server URL
            model: Optional model override

        Returns:
            Switch result with new provider details and timestamp

        Raises:
            ProviderValidationError: If validation fails (original provider unchanged)
        """
        # Get current configuration for potential rollback
        current_config = await self._get_llm_config(merchant_id)

        # Store current state for rollback
        previous_provider = current_config.provider
        previous_ollama_url = current_config.ollama_url
        previous_ollama_model = current_config.ollama_model
        previous_api_key = current_config.api_key_encrypted
        previous_cloud_model = current_config.cloud_model

        try:
            # Validate new configuration first (DOES NOT modify database)
            validation_result = await self.validate_provider_config(
                merchant_id=merchant_id,
                provider_id=provider_id,
                api_key=api_key,
                server_url=server_url,
                model=model,
            )

            # Validation succeeded - now apply changes
            is_ollama = provider_id == "ollama"

            if is_ollama:
                current_config.provider = provider_id
                current_config.ollama_url = server_url
                current_config.ollama_model = model or "llama3"
                # Clear cloud provider credentials
                current_config.api_key_encrypted = None
                current_config.cloud_model = None
            else:
                current_config.provider = provider_id
                # TODO: Encrypt API key before storing (requires encryption service)
                current_config.api_key_encrypted = api_key
                current_config.cloud_model = model or self._get_default_model(provider_id)
                # Clear Ollama configuration
                current_config.ollama_url = None
                current_config.ollama_model = None

            current_config.last_test_at = datetime.utcnow()
            current_config.test_result = {
                "validation": "passed",
                "latency_ms": validation_result["provider"].get("latency_ms"),
            }
            current_config.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(current_config)

            return {
                "success": True,
                "provider": {
                    "id": provider_id,
                    "name": validation_result["provider"]["name"],
                    "model": model
                    or (self._get_default_model(provider_id) if not is_ollama else "llama3"),
                },
                "switched_at": datetime.utcnow().isoformat(),
                "previous_provider": previous_provider,
            }

        except ProviderValidationError:
            # Validation failed - rollback to previous configuration
            current_config.provider = previous_provider
            current_config.ollama_url = previous_ollama_url
            current_config.ollama_model = previous_ollama_model
            current_config.api_key_encrypted = previous_api_key
            current_config.cloud_model = previous_cloud_model

            await self.db.commit()

            # Re-raise validation error
            raise

    async def test_provider_call(
        self,
        provider_id: str,
        api_key: Optional[str] = None,
        server_url: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Make a test call to provider API to verify connectivity.

        Args:
            provider_id: Provider to test
            api_key: API key for cloud providers
            server_url: Ollama server URL
            model: Model to use for test
            **kwargs: Additional provider-specific config

        Returns:
            Test result with success status, response, and latency

        Raises:
            ProviderValidationError: If test call fails
        """
        import time

        # Build provider configuration
        if provider_id == "ollama":
            config = {"server_url": server_url or "http://localhost:11434"}
        else:
            config = {"api_key": api_key, "model": model or self._get_default_model(provider_id)}

        # Create provider instance
        try:
            provider = self._factory.create_provider(provider_id, config)
        except APIError as e:
            raise ProviderValidationError(
                e.code,
                f"Failed to create provider instance: {e.message}",
            )

        # Make test call
        start_time = time.time()

        try:
            from app.services.llm.base_llm_service import LLMMessage

            test_message = LLMMessage(role="user", content="Hello")
            is_connected = await provider.test_connection()

            latency = (time.time() - start_time) * 1000  # Convert to ms

            if not is_connected:
                raise ProviderValidationError(
                    ErrorCode.LLM_CONNECTION_FAILED,
                    f"Provider connectivity test failed for {provider_id}",
                    {"provider_id": provider_id, "latency_ms": latency},
                )

            return {
                "success": True,
                "response": "Connection successful",
                "latency_ms": round(latency, 2),
                "provider_id": provider_id,
            }

        except Exception as e:
            latency = (time.time() - start_time) * 1000

            if isinstance(e, ProviderValidationError):
                raise

            raise ProviderValidationError(
                ErrorCode.LLM_CONNECTION_FAILED,
                f"Provider test call failed: {str(e)}",
                {"provider_id": provider_id, "error": str(e), "latency_ms": latency},
            )

    async def get_current_provider(
        self,
        merchant_id: int,
    ) -> Dict[str, Any]:
        """Get merchant's current LLM provider configuration.

        Args:
            merchant_id: Merchant ID

        Returns:
            Current provider configuration with metadata

        Raises:
            ProviderValidationError: If no configuration found
        """
        config = await self._get_llm_config(merchant_id)

        available_providers = self._factory.get_available_providers()
        provider_info = next(
            (p for p in available_providers if p["id"] == config.provider),
            None,
        )

        if not provider_info:
            raise ProviderValidationError(
                ErrorCode.LLM_PROVIDER_NOT_FOUND,
                f"Current provider '{config.provider}' not found in available providers",
            )

        # Determine active model
        if config.provider == "ollama":
            active_model = config.ollama_model
        else:
            active_model = config.cloud_model

        return {
            "provider": {
                "id": config.provider,
                "name": provider_info["name"],
                "description": provider_info["description"],
                "model": active_model,
            },
            "status": config.status,
            "configured_at": config.configured_at.isoformat(),
            "last_test_at": config.last_test_at.isoformat() if config.last_test_at else None,
            "total_tokens_used": config.total_tokens_used,
            "total_cost_usd": config.total_cost_usd,
        }

    # Private helper methods

    async def _get_merchant(self, merchant_id: int) -> Merchant:
        """Get merchant by ID.

        Raises:
            ProviderValidationError: If merchant not found
        """
        result = await self.db.execute(select(Merchant).where(Merchant.id == merchant_id))
        merchant = result.scalar_one_or_none()

        if not merchant:
            raise ProviderValidationError(
                ErrorCode.MERCHANT_NOT_FOUND,
                f"Merchant not found: {merchant_id}",
            )

        return merchant

    async def _get_llm_config(self, merchant_id: int) -> LLMConfiguration:
        """Get LLM configuration for merchant.

        Raises:
            ProviderValidationError: If configuration not found
        """
        result = await self.db.execute(
            select(LLMConfiguration).where(LLMConfiguration.merchant_id == merchant_id)
        )
        config = result.scalar_one_or_none()

        if not config:
            raise ProviderValidationError(
                ErrorCode.LLM_CONFIGURATION_MISSING,
                f"LLM configuration not found for merchant: {merchant_id}",
            )

        return config

    async def _validate_ollama_config(self, server_url: Optional[str]) -> None:
        """Validate Ollama server URL format.

        Raises:
            ProviderValidationError: If URL format is invalid
        """
        if not server_url:
            raise ProviderValidationError(
                ErrorCode.VALIDATION_ERROR,
                "Ollama server URL is required",
                {"field": "server_url"},
            )

        # Basic URL format validation
        url_pattern = re.compile(
            r"^https?://"  # http:// or https://
            r"[a-zA-Z0-9\-\.]+"  # hostname
            r"(:\d+)?"  # optional port
            r"(/.*)?$",  # optional path
            re.IGNORECASE,
        )

        if not url_pattern.match(server_url):
            raise ProviderValidationError(
                ErrorCode.VALIDATION_ERROR,
                "Invalid Ollama server URL format",
                {
                    "field": "server_url",
                    "expected_format": "http://localhost:11434 or http://ollama.example.com:11434",
                },
            )

    async def _validate_cloud_provider_config(
        self,
        provider_id: str,
        api_key: Optional[str],
    ) -> None:
        """Validate cloud provider API key format.

        Raises:
            ProviderValidationError: If API key is missing or invalid format
        """
        if not api_key:
            raise ProviderValidationError(
                ErrorCode.LLM_API_KEY_MISSING,
                f"API key is required for {provider_id}",
                {"field": "api_key", "provider_id": provider_id},
            )

        # Validate API key format
        # Skip validation in test mode
        if settings().get("IS_TESTING"):
            return

        pattern = self.API_KEY_PATTERNS.get(provider_id)
        if pattern and not pattern.match(api_key):
            raise ProviderValidationError(
                ErrorCode.LLM_API_KEY_INVALID,
                f"Invalid API key format for {provider_id}",
                {
                    "field": "api_key",
                    "provider_id": provider_id,
                    "expected_pattern": pattern.pattern,
                },
            )

    def _get_default_model(self, provider_id: str) -> str:
        """Get default model for provider.

        Reads default model from config settings, providing centralized
        configuration for all provider defaults.

        Args:
            provider_id: Provider ID

        Returns:
            Default model name from config settings
        """
        # Get all settings once for efficiency
        app_settings = settings()

        # Map provider IDs to their config keys
        provider_config_keys = {
            "openai": "OPENAI_DEFAULT_MODEL",
            "anthropic": "ANTHROPIC_DEFAULT_MODEL",
            "gemini": "GEMINI_DEFAULT_MODEL",
            "glm": "GLM_DEFAULT_MODEL",
            "ollama": "OLLAMA_DEFAULT_MODEL",
        }

        config_key = provider_config_keys.get(provider_id)
        if config_key:
            return app_settings.get(config_key, "default")

        return "default"
