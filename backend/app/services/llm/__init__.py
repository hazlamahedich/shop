"""LLM services package.

Provides abstraction layer for multiple LLM providers including:
- Ollama (local, free)
- OpenAI (GPT models)
- Anthropic (Claude models)
- Google Gemini
- GLM-4.7 (Zhipu AI, China market)
"""

from app.services.llm.base_llm_service import (
    BaseLLMService,
    LLMMessage,
    LLMResponse,
)
from app.services.llm.ollama_service import OllamaService
from app.services.llm.openai_service import OpenAIService
from app.services.llm.anthropic_service import AnthropicService
from app.services.llm.gemini_service import GeminiService
from app.services.llm.glm_service import GLMService
from app.services.llm.llm_router import LLMRouter
from app.services.llm.llm_factory import LLMProviderFactory

__all__ = [
    "BaseLLMService",
    "LLMMessage",
    "LLMResponse",
    "OllamaService",
    "OpenAIService",
    "AnthropicService",
    "GeminiService",
    "GLMService",
    "LLMRouter",
    "LLMProviderFactory",
]
