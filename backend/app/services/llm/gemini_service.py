"""Google Gemini provider implementation.

Uses Gemini API for Flash models.
Pricing fetched dynamically from OpenRouter via ModelDiscoveryService.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import httpx
import structlog

from app.services.llm.base_llm_service import (
    BaseLLMService,
    LLMMessage,
    LLMResponse,
)
from app.core.errors import APIError, ErrorCode


logger = structlog.get_logger(__name__)


class GeminiService(BaseLLMService):
    """Google Gemini provider implementation.

    Uses Gemini API for Flash models.
    Pricing fetched dynamically from config (via ModelDiscoveryService).
    """

    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    DEFAULT_MODEL = "gemini-2.0-flash"

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def async_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client with testing support."""
        if self._async_client is None:
            if self.is_testing:
                from httpx import ASGITransport

                self._async_client = httpx.AsyncClient(
                    transport=ASGITransport(),
                    base_url="http://test",
                    timeout=30.0,
                )
            else:
                self._async_client = httpx.AsyncClient(
                    base_url=self.GEMINI_API_URL,
                    timeout=60.0,
                )
        return self._async_client

    async def test_connection(self) -> bool:
        """Test Gemini API connectivity with simple message."""
        try:
            if self.is_testing:
                return True

            api_key = self.config.get("api_key")
            if not api_key:
                return False

            # Get model from config, strip google/ prefix if present
            model_name = self.config.get("model") or self.DEFAULT_MODEL

            if model_name.startswith("google/"):
                model_name = model_name[7:]  # Remove "google/" prefix

            # Build full URL (httpx has issues with colon in path when using base_url)
            full_url = f"{self.GEMINI_API_URL}/{model_name}:generateContent?key={api_key}"

            # Use a fresh client without base_url for this request
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    full_url,
                    headers={"Content-Type": "application/json"},
                    json={"contents": [{"parts": [{"text": "Hello"}]}]},
                )
            response.raise_for_status()
            return True

        except httpx.HTTPStatusError as e:
            logger.error(
                "gemini_connection_failed",
                status_code=e.response.status_code,
                error=str(e),
            )
            return False

    async def chat(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """Send chat completion to Gemini."""
        api_key = self.config.get("api_key")
        if not api_key:
            raise APIError(
                ErrorCode.LLM_API_KEY_MISSING,
                "Gemini API key not configured",
            )

        model_name = model or self.config.get("model") or self.DEFAULT_MODEL

        # Ensure model_name is not empty
        if not model_name or not model_name.strip():
            model_name = self.DEFAULT_MODEL

        # Strip OpenRouter prefix if present (e.g., "google/gemini-2.0-flash" -> "gemini-2.0-flash")
        if model_name.startswith("google/"):
            model_name = model_name[7:]  # Remove "google/" prefix

        logger.debug("gemini_chat_model", model=model_name, original=self.config.get("model"))

        # Convert LLMMessage to Gemini format
        # Gemini only accepts "user" and "model" roles
        gemini_contents = []
        for msg in messages:
            # Map roles to Gemini format
            if msg.role == "assistant":
                gemini_role = "model"
            elif msg.role == "system":
                # Gemini doesn't support system role in contents
                # Skip system messages - they should be handled via systemInstruction
                continue
            else:
                gemini_role = "user"

            gemini_contents.append({"role": gemini_role, "parts": [{"text": msg.content}]})

        payload = {
            "contents": gemini_contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        try:
            if self.is_testing:
                return LLMResponse(
                    content="Test response from Gemini",
                    tokens_used=10,
                    model=model_name,
                    provider="gemini",
                    metadata={"test": True},
                )

            # Build full URL (httpx has issues with colon in path when using base_url)
            full_url = f"{self.GEMINI_API_URL}/{model_name}:generateContent?key={api_key}"

            # Use a fresh client without base_url
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    full_url,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                )
            response.raise_for_status()
            data = response.json()

            # Extract response
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            usage = data.get("usageMetadata", {})
            total_tokens = usage.get("totalTokenCount", 0)

            return LLMResponse(
                content=content,
                tokens_used=total_tokens,
                model=model_name,
                provider="gemini",
                metadata={
                    "finish_reason": data["candidates"][0].get("finishReason", ""),
                },
            )

        except httpx.HTTPStatusError as e:
            logger.error(
                "gemini_chat_failed",
                status_code=e.response.status_code,
                error=str(e),
            )
            raise APIError(
                ErrorCode.LLM_PROVIDER_ERROR,
                f"Gemini chat failed: {e.response.text}",
            )

    def count_tokens(self, text: str) -> int:
        """Approximate token count for Gemini.

        Gemini uses tokenization similar to Google models.
        Approximately 4 characters per token.
        """
        return len(text) // 4
