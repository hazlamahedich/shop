"""Pydantic schemas for Knowledge Base API.

Request and response schemas for knowledge base document endpoints.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    """Response schema for document upload."""

    id: int
    filename: str
    file_type: str = Field(..., alias="fileType")
    file_size: int = Field(..., alias="fileSize")
    status: str
    created_at: datetime = Field(..., alias="createdAt")

    class Config:
        populate_by_name = True


class DocumentDetail(BaseModel):
    """Detailed document response with chunk count."""

    id: int
    filename: str
    file_type: str = Field(..., alias="fileType")
    file_size: int = Field(..., alias="fileSize")
    status: str
    error_message: str | None = Field(None, alias="errorMessage")
    chunk_count: int = Field(0, alias="chunkCount")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    class Config:
        populate_by_name = True


class DocumentListResponse(BaseModel):
    """Response schema for document list."""

    documents: list[DocumentDetail]


class DocumentStatusResponse(BaseModel):
    """Response schema for document processing status."""

    status: str
    progress: int = Field(..., ge=0, le=100)
    chunk_count: int = Field(..., alias="chunkCount")
    error_message: str | None = Field(None, alias="errorMessage")

    class Config:
        populate_by_name = True


class DocumentDeleteResponse(BaseModel):
    """Response schema for document deletion."""

    deleted: bool
    message: str = "Document deleted successfully"


class KnowledgeBaseStatsResponse(BaseModel):
    """Response schema for knowledge base statistics."""

    total_docs: int = Field(..., alias="totalDocs")
    processing_count: int = Field(..., alias="processingCount")
    ready_count: int = Field(..., alias="readyCount")
    error_count: int = Field(..., alias="errorCount")
    last_upload_date: datetime | None = Field(None, alias="lastUploadDate")

    class Config:
        populate_by_name = True
