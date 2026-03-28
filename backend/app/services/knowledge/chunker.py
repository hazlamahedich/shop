"""Document chunking service for knowledge base.

Handles extraction and chunking of text from various document types.
"""

from __future__ import annotations

import structlog
from docx import Document
from PyPDF2 import PdfReader

logger = structlog.get_logger()


class ChunkingError(Exception):
    """Raised when document chunking fails."""

    pass


class DocumentChunker:
    """Service for chunking documents into text segments.

    Enhanced for better RAG performance:
    - Larger chunks (1500 chars) for more complete information
    - More overlap (300 chars) for better continuity
    - This improves context quality and reduces information loss at boundaries
    """

    CHUNK_SIZE_MIN = 500
    CHUNK_SIZE_MAX = 1500  # Increased from 1000 for more context per chunk
    OVERLAP_SIZE = 300  # Increased from 100 for better continuity between chunks
    MIN_CHUNK_CHARS = 50

    def chunk_document(self, file_path: str, file_type: str) -> list[str]:
        """Extract text from document and split into chunks.

        Args:
            file_path: Path to the document file
            file_type: File type (pdf, txt, md, docx)

        Returns:
            List of text chunks (500-1000 chars each)

        Raises:
            ChunkingError: If text extraction or chunking fails
        """
        try:
            text = self._extract_text(file_path, file_type)
            if not text or not text.strip():
                raise ChunkingError("Document contains no extractable text")

            chunks = self._split_into_chunks(text)
            chunks = [c for c in chunks if self._validate_chunk_quality(c)]

            if not chunks:
                raise ChunkingError("No valid chunks extracted from document")

            logger.info(
                "document_chunked",
                file_path=file_path,
                file_type=file_type,
                chunk_count=len(chunks),
            )
            return chunks

        except ChunkingError:
            raise
        except Exception as e:
            logger.error("chunking_failed", file_path=file_path, error=str(e))
            raise ChunkingError(f"Failed to chunk document: {str(e)}") from e

    def _extract_text(self, file_path: str, file_type: str) -> str:
        """Extract text content from document based on file type."""
        file_type = file_type.lower()

        if file_type == "pdf":
            return self._extract_from_pdf(file_path)
        elif file_type in ("txt", "md"):
            return self._extract_from_text(file_path)
        elif file_type == "docx":
            return self._extract_from_docx(file_path)
        else:
            raise ChunkingError(f"Unsupported file type: {file_type}")

    def _extract_from_text(self, file_path: str) -> str:
        """Extract text from plain text file (txt, md)."""
        try:
            with open(file_path, encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            with open(file_path, encoding="latin-1") as f:
                return f.read()
        except Exception as e:
            raise ChunkingError(f"Failed to read text file: {str(e)}") from e

    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        try:
            doc = Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n".join(paragraphs)
        except Exception as e:
            raise ChunkingError(f"Failed to extract text from DOCX: {str(e)}") from e

    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            reader = PdfReader(file_path)
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            return "\n".join(text_parts)
        except Exception as e:
            raise ChunkingError(f"Failed to extract text from PDF: {str(e)}") from e

    def _split_into_chunks(self, text: str) -> list[str]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(start + self.CHUNK_SIZE_MAX, text_length)
            chunk = text[start:end]
            chunks.append(chunk.strip())
            start += self.CHUNK_SIZE_MAX - self.OVERLAP_SIZE

            if start >= text_length:
                break

        return chunks

    def _validate_chunk_quality(self, chunk: str) -> bool:
        """Ensure chunk has meaningful content."""
        stripped = chunk.strip()
        if len(stripped) < self.MIN_CHUNK_CHARS:
            return False
        if not any(c.isalnum() for c in stripped):
            return False
        return True
