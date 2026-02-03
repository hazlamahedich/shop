"""LLM Configuration ORM model.

Stores LLM provider configuration per merchant including provider type,
credentials, models, and status. Supports Ollama (local) and cloud providers
(OpenAI, Anthropic, Gemini, GLM-4.7).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, Float, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class LLMConfiguration(Base):
    """LLM provider configuration model.

    Stores LLM provider settings for each merchant including:
    - Provider type (Ollama, OpenAI, Anthropic, Gemini, GLM)
    - Encrypted API keys for cloud providers
    - Ollama server URL for local provider
    - Model selection and status tracking
    - Backup provider configuration for failover
    """

    __tablename__ = "llm_configurations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Relationship to Merchant for proper ORM ordering
    merchant: Mapped["Merchant"] = relationship(
        "Merchant",
        back_populates="llm_configuration",
    )

    # Provider configuration - use ENUM for type safety
    provider: Mapped[str] = mapped_column(
        ENUM(
            "ollama",
            "openai",
            "anthropic",
            "gemini",
            "glm",
            name="llm_provider",
            create_type=False,  # Type already exists from migration
        ),
        nullable=False,
        index=True,
    )

    # Ollama-specific configuration
    ollama_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )  # e.g., http://localhost:11434
    ollama_model: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )  # e.g., llama3, mistral

    # Cloud provider configuration
    api_key_encrypted: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )  # Fernet encrypted API key
    cloud_model: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )  # Provider-specific model

    # Fallback configuration (backup provider)
    backup_provider: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )  # Backup provider if primary fails
    backup_api_key_encrypted: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )  # Encrypted backup API key

    # Configuration metadata
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        index=True,
    )
    configured_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    last_test_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )
    test_result: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )  # Test response metadata

    # Cost tracking metadata (aggregated from conversation_costs)
    total_tokens_used: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    total_cost_usd: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<LLMConfiguration(id={self.id}, merchant_id={self.merchant_id}, "
            f"provider={self.provider}, status={self.status})>"
        )
