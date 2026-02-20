"""Pydantic schemas for LLM configuration API.

Provides request/response schemas for LLM provider configuration,
testing, and status endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from pydantic import BaseModel, Field, field_validator


def to_camel(value: str) -> str:
    """Convert snake_case to camelCase for API compatibility.

    Args:
        value: snake_case string

    Returns:
        camelCase string
    """
    components = value.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


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
    pricing: Dict[str, Any]
    models: List[str]
    features: List[str]


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
    ollama_config: Optional[OllamaConfigRequest] = None
    cloud_config: Optional[CloudConfigRequest] = None
    backup_provider: Optional[str] = None
    backup_api_key: Optional[str] = None

    @field_validator("backup_api_key")
    @classmethod
    def validate_backup_api_key(cls, v: Optional[str], info) -> Optional[str]:
        """Validate backup API key is provided if backup provider is set."""
        if info.data.get("backup_provider") and not v:
            raise ValueError("backup_api_key required when backup_provider is set")
        return v


class LLMUpdateRequest(BaseModel):
    """LLM configuration update request."""

    provider: Optional[LLMProvider] = None
    ollama_url: Optional[str] = None
    ollama_model: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    backup_provider: Optional[str] = None
    backup_api_key: Optional[str] = None


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
    last_test_at: Optional[datetime]
    test_result: Optional[Dict[str, Any]]
    total_tokens_used: int
    total_cost_usd: float
    backup_provider: Optional[str]


class LLMTestResponse(BaseModel):
    """LLM test response."""

    success: bool
    provider: str
    model: str
    response: str
    tokens_used: int
    latency_ms: float
    error: Optional[str]


class LLMProviderInfo(BaseModel):
    """LLM provider information."""

    id: str
    name: str
    description: str
    pricing: Dict[str, Any]
    models: List[str]
    features: List[str]


class LLMProvidersResponse(BaseModel):
    """Available LLM providers response."""

    providers: List[LLMProviderInfo]


class LLMHealthResponse(BaseModel):
    """LLM health check response."""

    router: str
    primary_provider: Optional[Dict[str, Any]]
    backup_provider: Optional[Dict[str, Any]]


# Envelope Schemas (for consistent API responses)


class MinimalLLMEnvelope(BaseModel):
    """Minimal envelope for LLM API responses."""

    data: Any
    meta: Dict[str, Any]


class LLMConfigureResponse(BaseModel):
    """LLM configuration response."""

    message: str
    provider: str
    model: str
    status: str


class LLMUpdateResponse(BaseModel):
    """LLM update response."""

    message: str
    updated_fields: List[str]


class LLMClearResponse(BaseModel):
    """LLM configuration clear response."""

    message: str


# Clarification Flow Schemas (Story 2.4)


class ClarificationState(BaseModel):
    """State of clarification flow for handling ambiguous user requests."""

    active: bool = Field(False, description="Is clarification flow active?")
    attempt_count: int = Field(0, description="Number of clarification attempts")
    questions_asked: list[str] = Field(default_factory=list, description="Constraints asked about")
    last_question: Optional[str] = Field(None, description="Last question asked")
    original_intent: Optional[dict[str, Any]] = Field(
        None, description="Original intent being clarified"
    )
    started_at: Optional[str] = Field(None, description="When clarification started")

    class Config:
        alias_generator = to_camel
        populate_by_name = True


# Provider Switching Schemas (Story 3.4)


class SwitchProviderRequest(BaseModel):
    """Request schema for switching LLM providers.

    Validates provider switching request with provider-specific configuration.
    """

    provider_id: str = Field(
        ..., description="Provider ID (ollama, openai, anthropic, gemini, glm)"
    )
    api_key: Optional[str] = Field(None, description="API key for cloud providers")
    server_url: Optional[str] = Field(None, description="Ollama server URL")
    model: Optional[str] = Field(None, description="Optional model override")

    @field_validator("provider_id")
    @classmethod
    def validate_provider_id(cls, v: str) -> str:
        """Validate provider ID is in allowed list."""
        allowed_providers = {"ollama", "openai", "anthropic", "gemini", "glm"}
        if v not in allowed_providers:
            raise ValueError(f"Invalid provider_id. Allowed: {', '.join(allowed_providers)}")
        return v

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: Optional[str], info) -> Optional[str]:
        """Validate API key is provided for cloud providers.

        Note: api_key is optional for updates to existing providers.
        The service layer handles using the existing key when none is provided.
        """
        # Allow None/empty for updates - service will use existing key
        return v

    @field_validator("server_url")
    @classmethod
    def validate_server_url(cls, v: Optional[str], info) -> Optional[str]:
        """Validate server URL is provided for Ollama.

        Note: server_url is optional for updates to existing providers.
        The service layer handles using the existing URL when none is provided.
        """
        return v

    class Config:
        alias_generator = to_camel
        populate_by_name = True


class SwitchProviderResponse(BaseModel):
    """Response schema for successful provider switch."""

    success: bool = Field(True, description="Switch operation status")
    provider: ProviderInfo = Field(..., description="New provider information")
    switched_at: str = Field(..., description="ISO-8601 timestamp of switch")
    previous_provider: Optional[str] = Field(None, description="Previous provider ID")

    class Config:
        alias_generator = to_camel
        populate_by_name = True


class ProviderInfo(BaseModel):
    """Provider information in switch response."""

    id: str
    name: str
    model: str

    class Config:
        alias_generator = to_camel
        populate_by_name = True


class ProviderValidationRequest(BaseModel):
    """Request schema for validating provider configuration."""

    provider_id: str = Field(..., description="Provider ID to validate")
    api_key: Optional[str] = Field(None, description="API key for validation")
    server_url: Optional[str] = Field(None, description="Server URL for validation")
    model: Optional[str] = Field(None, description="Optional model for validation")

    @field_validator("provider_id")
    @classmethod
    def validate_provider_id(cls, v: str) -> str:
        """Validate provider ID is in allowed list."""
        allowed_providers = {"ollama", "openai", "anthropic", "gemini", "glm"}
        if v not in allowed_providers:
            raise ValueError(f"Invalid provider_id. Allowed: {', '.join(allowed_providers)}")
        return v

    class Config:
        alias_generator = to_camel
        populate_by_name = True


class ProviderValidationResponse(BaseModel):
    """Response schema for provider validation."""

    valid: bool = Field(..., description="Validation result")
    provider: ValidatedProvider = Field(..., description="Validated provider info")
    validated_at: str = Field(..., description="ISO-8601 timestamp of validation")


class ValidatedProvider(BaseModel):
    """Validated provider information."""

    id: str
    name: str
    test_response: str = Field(..., description="Test call response message")
    latency_ms: Optional[float] = Field(None, description="Test call latency in milliseconds")

    class Config:
        alias_generator = to_camel
        populate_by_name = True


class ProviderListResponse(BaseModel):
    """Response schema for available providers list."""

    current_provider: CurrentProviderInfo = Field(..., description="Current active provider")
    providers: List[ProviderMetadata] = Field(..., description="All available providers")


class CurrentProviderInfo(BaseModel):
    """Current provider information."""

    id: str
    name: str
    description: str
    model: str
    status: str
    configured_at: str
    total_tokens_used: int = Field(0, description="Total tokens consumed")
    total_cost_usd: float = Field(0.0, description="Total cost in USD")

    class Config:
        alias_generator = to_camel
        populate_by_name = True


class ProviderMetadata(BaseModel):
    """Provider metadata for listing."""

    id: str
    name: str
    description: str
    pricing: ProviderPricing = Field(..., description="Pricing information")
    models: List[str] = Field(..., description="Available models")
    features: List[str] = Field(..., description="Provider features")
    is_active: bool = Field(False, description="Is this the current provider")
    estimated_monthly_cost: float = Field(0.0, description="Estimated monthly cost based on usage")

    class Config:
        alias_generator = to_camel
        populate_by_name = True


class ProviderPricing(BaseModel):
    """Provider pricing information."""

    input_cost: float = Field(..., alias="inputCost", description="Cost per 1M input tokens")
    output_cost: float = Field(..., alias="outputCost", description="Cost per 1M output tokens")
    currency: str = Field("USD", description="Currency code")

    class Config:
        alias_generator = to_camel
        populate_by_name = True


class ModelDiscoveryRequest(BaseModel):
    """Request schema for fetching available models."""

    provider_id: str = Field(
        ..., description="Provider ID (ollama, openai, anthropic, gemini, glm)"
    )
    ollama_url: Optional[str] = Field(
        None, description="Ollama server URL (required for ollama provider)"
    )

    class Config:
        alias_generator = to_camel
        populate_by_name = True


class ModelPricing(BaseModel):
    """Model pricing information."""

    input_cost_per_million: float = Field(
        ..., alias="inputCostPerMillion", description="Cost per 1M input tokens"
    )
    output_cost_per_million: float = Field(
        ..., alias="outputCostPerMillion", description="Cost per 1M output tokens"
    )
    currency: str = Field("USD", description="Currency code")

    class Config:
        alias_generator = to_camel
        populate_by_name = True


class DiscoveredModel(BaseModel):
    """Discovered model information."""

    id: str = Field(..., description="Model ID")
    name: str = Field(..., description="Model display name")
    provider: str = Field(..., description="Provider ID")
    description: str = Field("", description="Model description")
    context_length: int = Field(4096, alias="contextLength", description="Maximum context length")
    pricing: ModelPricing = Field(..., description="Pricing information")
    is_local: bool = Field(False, alias="isLocal", description="Is this a local model")
    is_downloaded: bool = Field(
        False, alias="isDownloaded", description="Is model downloaded (Ollama only)"
    )
    features: List[str] = Field(default_factory=list, description="Model features")

    class Config:
        alias_generator = to_camel
        populate_by_name = True


class ModelDiscoveryResponse(BaseModel):
    """Response schema for model discovery."""

    provider: str = Field(..., description="Provider ID")
    models: List[DiscoveredModel] = Field(..., description="Available models")
    cached: bool = Field(False, description="Is response from cache")
    cache_info: Optional[Dict[str, Any]] = Field(
        None, alias="cacheInfo", description="Cache information"
    )

    class Config:
        alias_generator = to_camel
        populate_by_name = True
