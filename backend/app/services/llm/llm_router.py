"""LLM Router with primary/backup provider selection and automatic failover.

Supports Ollama as primary (local, free) with cloud backup.
Automatically switches to backup if primary fails.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import structlog

from app.services.llm.base_llm_service import (
    BaseLLMService,
    LLMMessage,
    LLMResponse,
)
from app.services.llm.llm_factory import LLMProviderFactory
from app.core.errors import APIError, ErrorCode


logger = structlog.get_logger(__name__)


class LLMRouter:
    """Router with primary/backup provider selection and automatic failover.

    Supports Ollama as primary (local, free) with cloud backup.
    Automatically switches to backup if primary fails.
    """

    def __init__(self, config: Dict[str, Any], is_testing: bool = False) -> None:
        """Initialize LLM router with configuration.

        Args:
            config: Router configuration with primary and backup providers
            is_testing: Force mock responses (deprecated, use IS_TESTING env var)
        """
        self.config = config
        self.is_testing = is_testing

        # Create primary and backup providers
        # Note: is_testing parameter is ignored - factory reads from IS_TESTING env var
        self.primary_provider = LLMProviderFactory.create_provider(
            config.get("primary_provider", "ollama"),
            config.get("primary_config", {}),
        )

        backup_provider_name = config.get("backup_provider")
        backup_config = config.get("backup_config", {})

        if backup_provider_name and backup_config:
            self.backup_provider = LLMProviderFactory.create_provider(
                backup_provider_name,
                backup_config,
            )
        else:
            self.backup_provider = None

        self.current_provider = "primary"

    async def chat(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        use_backup: bool = False,
    ) -> LLMResponse:
        """Send chat completion using primary provider with automatic failover.

        Args:
            messages: Conversation history
            model: Model override (optional)
            temperature: Response randomness
            max_tokens: Maximum tokens in response
            use_backup: Force use of backup provider

        Returns:
            LLM response with content and metadata

        Raises:
            APIError: If both primary and backup providers fail
        """
        provider = self.backup_provider if use_backup else self.primary_provider
        provider_name = "backup" if use_backup else "primary"

        try:
            logger.info(
                "llm_router_attempt",
                provider=provider_name,
                use_backup=use_backup,
            )

            response = await provider.chat(messages, model, temperature, max_tokens)

            # Log successful request
            logger.info(
                "llm_router_success",
                provider=provider_name,
                tokens_used=response.tokens_used,
                model=response.model,
            )

            return response

        except Exception as e:
            logger.warning(
                "llm_router_primary_failed",
                error=str(e),
                backup_available=self.backup_provider is not None,
            )

            if self.backup_provider and not use_backup:
                logger.info(
                    "llm_router_fallback",
                    fallback_to="backup",
                )

                try:
                    response = await self.backup_provider.chat(
                        messages, model, temperature, max_tokens
                    )

                    logger.info(
                        "llm_router_backup_success",
                        tokens_used=response.tokens_used,
                        model=response.model,
                    )

                    return response

                except Exception as backup_error:
                    logger.error(
                        "llm_router_both_failed",
                        primary_error=str(e),
                        backup_error=str(backup_error),
                    )

                    raise APIError(
                        ErrorCode.LLM_ROUTER_BOTH_FAILED,
                        f"Both LLM providers failed. "
                        f"Primary: {str(e)}, Backup: {str(backup_error)}",
                    )
            else:
                raise APIError(
                    ErrorCode.LLM_SERVICE_UNAVAILABLE,
                    f"LLM provider failed: {str(e)}",
                )

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all configured providers.

        Returns:
            Health status dict with primary and backup provider status
        """
        health_status = {
            "router": "healthy",
            "primary_provider": await self.primary_provider.health_check(),
            "backup_provider": None,
        }

        if self.backup_provider:
            health_status["backup_provider"] = (
                await self.backup_provider.health_check()
            )

        return health_status
