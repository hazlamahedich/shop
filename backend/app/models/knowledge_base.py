"""Knowledge Base ORM models for RAG document storage.

Implements document storage and chunking for the knowledge base feature (Epic 8).

Story 8-11: Changed embedding column from Vector(1536) to JSONB for flexible
dimension support (768 for Gemini/Ollama, 1536 for OpenAI).
"""

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.merchant import Merchant


def _utcnow_naive() -> datetime:
    """Return current UTC time as a naive datetime (for TIMESTAMP WITHOUT TIME ZONE columns)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class DocumentStatus(str, Enum):
    """Document processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class KnowledgeDocument(Base):
    """Knowledge document model.

    Stores uploaded documents for knowledge base RAG retrieval.
    """

    __tablename__ = "knowledge_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    file_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=DocumentStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    # Re-embedding status fields (Story 8-11)
    re_embedding_status: Mapped[str | None] = mapped_column(
        String(20),
        default="none",
        nullable=True,
        server_default="none",
    )
    re_embedding_progress: Mapped[int | None] = mapped_column(
        Integer,
        default=0,
        nullable=True,
        server_default="0",
    )
    embedding_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=_utcnow_naive,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=_utcnow_naive,
        onupdate=_utcnow_naive,
        nullable=False,
    )

    # Relationships
    merchant: Mapped["Merchant"] = relationship(
        "Merchant",
        back_populates="knowledge_documents",
    )
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentChunk.chunk_index",
    )

    def __repr__(self) -> str:
        return f"<KnowledgeDocument(id={self.id}, filename={self.filename}, status={self.status})>"


class DocumentChunk(Base):
    """Document chunk model for RAG retrieval.

    Stores text chunks extracted from documents with optional embeddings.

    Story 8-11: Changed embedding from Vector(1536) to JSONB for flexible
    dimension support. Different providers have different dimensions:
    - OpenAI text-embedding-3-small: 1536
    - Gemini text-embedding-004: 768
    - Ollama nomic-embed-text: 768
    """

    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    # Story 8-11: JSONB for flexible embedding dimensions (768 or 1536)
    # Cast to vector at query time: embedding::jsonb::float[]::vector(N)
    embedding: Mapped[Optional[list[float]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    embedding_dimension: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=_utcnow_naive,
        nullable=False,
    )

    # Relationships
    document: Mapped["KnowledgeDocument"] = relationship(
        "KnowledgeDocument",
        back_populates="chunks",
    )

    def __repr__(self) -> str:
        return (
            f"<DocumentChunk(id={self.id}, doc_id={self.document_id}, "
            f"chunk_idx={self.chunk_index}, dim={self.embedding_dimension})>"
        )
