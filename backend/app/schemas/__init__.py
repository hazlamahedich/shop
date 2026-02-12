"""Pydantic schemas for API request/response validation."""

from app.schemas.onboarding import (
    MinimalEnvelope,
    MetaData,
    PrerequisiteCheckRequest,
    PrerequisiteCheckResponse,
)

from app.schemas.llm import (  # noqa: F401 (export for type generation)
    LLMConfigureRequest,
    LLMUpdateRequest,
    LLMTestRequest,
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

# Story 1.11: Business Info & FAQ Configuration schemas
from app.schemas.business_info import (  # noqa: F401
    BusinessInfoRequest,
    BusinessInfoResponse,
    BusinessInfoEnvelope,
)

# Story 1.12: Bot Naming Configuration schemas
from app.schemas.bot_config import (  # noqa: F401
    BotNameUpdate,
    BotConfigResponse,
    BotConfigEnvelope,
)

# Story 1.14: Greeting Configuration schemas
from app.schemas.greeting import (  # noqa: F401
    GreetingConfigUpdate,
    GreetingConfigResponse,
    GreetingEnvelope,
)

from app.schemas.faq import (  # noqa: F401
    FaqRequest,
    FaqResponse,
    FaqListEnvelope,
    FaqEnvelope,
    FaqReorderRequest,
)

# Story 1.13: Bot Preview Mode schemas
from app.schemas.preview import (  # noqa: F401
    PreviewMessageRequest,
    PreviewMessageResponse,
    PreviewMessageMetadata,
    PreviewSessionResponse,
    PreviewResetResponse,
    PreviewMessageEnvelope,
    PreviewSessionEnvelope,
    PreviewResetEnvelope,
    STARTER_PROMPTS,
)

__all__ = [
    "MinimalEnvelope",
    "MetaData",
    "PrerequisiteCheckRequest",
    "PrerequisiteCheckResponse",
    "LLMConfigureRequest",
    "LLMUpdateRequest",
    "LLMTestRequest",
    "LLMStatusResponse",
    "LLMTestResponse",
    "LLMProvidersResponse",
    "LLMProviderInfo",
    "LLMHealthResponse",
    "LLMConfigureResponse",
    "LLMUpdateResponse",
    "LLMClearResponse",
    "MinimalLLMEnvelope",
    # Story 1.11: Business Info & FAQ schemas
    "BusinessInfoRequest",
    "BusinessInfoResponse",
    "BusinessInfoEnvelope",
    # Story 1.12: Bot Naming schemas
    "BotNameUpdate",
    "BotConfigResponse",
    "BotConfigEnvelope",
    # Story 1.11: FAQ schemas
    "FaqRequest",
    "FaqResponse",
    "FaqListEnvelope",
    "FaqEnvelope",
    "FaqReorderRequest",
    # Story 1.13: Bot Preview Mode schemas
    "PreviewMessageRequest",
    "PreviewMessageResponse",
    "PreviewMessageMetadata",
    "PreviewSessionResponse",
    "PreviewResetResponse",
    "PreviewMessageEnvelope",
    "PreviewSessionEnvelope",
    "PreviewResetEnvelope",
    "STARTER_PROMPTS",
    # Story 1.14: Greeting Configuration schemas
    "GreetingConfigUpdate",
    "GreetingConfigResponse",
    "GreetingEnvelope",
]
