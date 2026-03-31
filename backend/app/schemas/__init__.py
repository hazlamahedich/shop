"""Pydantic schemas for API request/response validation."""

# Story 1.12: Bot Naming Configuration schemas
from app.schemas.bot_config import (  # noqa: F401
    BotConfigEnvelope,
    BotConfigResponse,
    BotNameUpdate,
)

# Story 1.11: Business Info & FAQ Configuration schemas
from app.schemas.business_info import (  # noqa: F401
    BusinessInfoEnvelope,
    BusinessInfoRequest,
    BusinessInfoResponse,
)
from app.schemas.conversation_context import (  # noqa: F401
    ContextSummary,
    ConversationContextResponse,
    ConversationContextUpdate,
    ConversationTurnResponse,
    ContextSummaryResponse,
    ContextUpdateResponse,
)
from app.schemas.faq import (  # noqa: F401
    FaqEnvelope,
    FaqListEnvelope,
    FaqReorderRequest,
    FaqRequest,
    FaqResponse,
)

# Story 1.14: Greeting Configuration schemas
from app.schemas.greeting import (  # noqa: F401
    GreetingConfigResponse,
    GreetingConfigUpdate,
    GreetingEnvelope,
)
from app.schemas.llm import (  # noqa: F401 (export for type generation)
    LLMClearResponse,
    LLMConfigureRequest,
    LLMConfigureResponse,
    LLMHealthResponse,
    LLMProviderInfo,
    LLMProvidersResponse,
    LLMStatusResponse,
    LLMTestRequest,
    LLMTestResponse,
    LLMUpdateRequest,
    LLMUpdateResponse,
    MinimalLLMEnvelope,
)
from app.schemas.onboarding import (
    MetaData,
    MinimalEnvelope,
    PrerequisiteCheckRequest,
    PrerequisiteCheckResponse,
)

# Story 1.13: Bot Preview Mode schemas
from app.schemas.preview import (  # noqa: F401
    STARTER_PROMPTS,
    PreviewMessageEnvelope,
    PreviewMessageMetadata,
    PreviewMessageRequest,
    PreviewMessageResponse,
    PreviewResetEnvelope,
    PreviewResetResponse,
    PreviewSessionEnvelope,
    PreviewSessionResponse,
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
    # Story 11-1: Conversation Context schemas
    "ConversationContextResponse",
    "ConversationContextUpdate",
    "ConversationTurnResponse",
    "ContextSummary",
    "ContextUpdateResponse",
    "ContextSummaryResponse",
]
