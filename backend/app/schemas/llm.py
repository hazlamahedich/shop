"""Pydantic schemas for LLM configuration API.

Provides request/response schemas for LLM provider configuration,
testing, and status endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from enum import Enum

from pydantic import BaseModel, Field, field_validator


# Enum Types


class LLMProvider(str, Enum):
    """LLM provider identifiers."""

    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    GLM = "glm"


class LLMStatus(str, Enum):
    """LLM configuration status."""

    PENDING = "pending"
    ACTIVE = "active"
    ERROR = "error"


# Request Schemas


class LLMProviderMetadata(BaseModel):
    """LLM provider information with pricing and features."""

    id: str
    name: str
    description: str
    pricing: dict[str, Any]
    models: list[str]
    features: list[str]


class OllamaConfigRequest(BaseModel):
    """Ollama provider configuration request."""

    ollama_url: str = Field(
        default="http://localhost:11434",
        description="Ollama server URL",
    )
    ollama_model: str = Field(
        default="llama3",
        description="Ollama model to use",
    )


class CloudConfigRequest(BaseModel):
    """Cloud provider configuration request."""

    provider: LLMProvider
    api_key: str = Field(..., description="API key for the provider")
    model: str = Field(..., description="Model to use")


class LLMConfigureRequest(BaseModel):
    """LLM configuration request (union of all provider types)."""

    provider: LLMProvider
    ollama_config: OllamaConfigRequest | None = None
    cloud_config: CloudConfigRequest | None = None
    backup_provider: str | None = None
    backup_api_key: str | None = None

    @field_validator("backup_api_key")
    @classmethod
    def validate_backup_api_key(cls, v: str | None, info) -> str | None:
        """Validate backup API key is provided if backup provider is set."""
        if info.data.get("backup_provider") and not v:
            raise ValueError("backup_api_key required when backup_provider is set")
        return v


class LLMUpdateRequest(BaseModel):
    """LLM configuration update request."""

    provider: LLMProvider | None = None
    ollama_url: str | None = None
    ollama_model: str | None = None
    api_key: str | None = None
    model: str | None = None
    backup_provider: str | None = None
    backup_api_key: str | None = None


class LLMTestRequest(BaseModel):
    """LLM test request."""

    test_prompt: str = Field(
        default="Hello, this is a test.",
        description="Test prompt to validate LLM connectivity",
    )


# Response Schemas


class LLMStatusResponse(BaseModel):
    """LLM configuration status response."""

    provider: str
    model: str
    status: LLMStatus
    configured_at: datetime
    last_test_at: datetime | None
    test_result: dict[str, Any] | None
    total_tokens_used: int
    total_cost_usd: float
    backup_provider: str | None


class LLMTestResponse(BaseModel):
    """LLM test response."""

    success: bool
    provider: str
    model: str
    response: str
    tokens_used: int
    latency_ms: float
    error: str | None


class LLMProviderInfo(BaseModel):
    """LLM provider information."""

    id: str
    name: str
    description: str
    pricing: dict[str, Any]
    models: list[str]
    features: list[str]


class LLMProvidersResponse(BaseModel):
    """Available LLM providers response."""

    providers: list[LLMProviderInfo]


class LLMHealthResponse(BaseModel):
    """LLM health check response."""

    router: str
    primary_provider: dict[str, Any] | None
    backup_provider: dict[str, Any] | None


# Envelope Schemas (for consistent API responses)


class MinimalLLMEnvelope(BaseModel):
    """Minimal envelope for LLM API responses."""

    data: Any
    meta: dict[str, Any]


class LLMConfigureResponse(BaseModel):
    """LLM configuration response."""

    message: str
    provider: str
    model: str
    status: str


class LLMUpdateResponse(BaseModel):
    """LLM update response."""

    message: str
    updated_fields: list[str]


class LLMClearResponse(BaseModel):
    """LLM configuration clear response."""

    message: str
