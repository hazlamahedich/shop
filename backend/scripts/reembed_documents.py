#!/usr/bin/env python
"""Re-embed documents for a merchant using Gemini's embedding model.

This script updates stored embeddings to use the correct dimension (3072)
for Gemini's embedding models (gemini-embedding-001 or gemini-embedding-2-preview).

Usage:
    python scripts/reembed_documents.py --merchant-id 1
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import decrypt_access_token
from app.models.knowledge_base import DocumentChunk, KnowledgeDocument
from app.services.knowledge.chunker import DocumentChunker
from app.services.rag.embedding_service import EmbeddingService


async def reembed_documents(merchant_id: int, db_url: str):
    """Re-embed all documents for a merchant."""

    # Create async engine
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Get merchant's LLM config for API key
        result = await db.execute(
            text("SELECT api_key_encrypted, ollama_url FROM llm_configurations WHERE merchant_id = :mid"),
            {"mid": merchant_id}
        )
        config_row = result.fetchone()

        if not config_row or not config_row[0]:
            print(f"ERROR: No API key found for merchant {merchant_id}")
            return False

        api_key = decrypt_access_token(config_row[0])
        print(f"API key found: {api_key[:10]}...")

        # Get documents to re-embed
        result = await db.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.merchant_id == merchant_id,
                KnowledgeDocument.status == "ready"
            )
        )
        documents = result.scalars().all()

        if not documents:
            print(f"No documents found for merchant {merchant_id}")
            return True

        print(f"Found {len(documents)} documents to re-embed")

        # Create embedding service with Gemini
        embedding_service = EmbeddingService(
            provider="gemini",
            api_key=api_key,
            model="gemini-embedding-001",
        )

        print("Using embedding model: gemini-embedding-001")
        print(f"Expected dimension: {embedding_service.dimension}")

        # Create chunker
        chunker = DocumentChunker()

        total_chunks = 0
        total_docs = 0

        for doc in documents:
            print(f"\nProcessing: {doc.filename}...")

            try:
                # Get file path
                file_path = get_file_path(doc)
                if not file_path:
                    print("  WARNING: File not found, skipping")
                    continue

                # Chunk document
                chunks = chunker.chunk_document(file_path, doc.file_type)
                if not chunks:
                    print("  WARNING: No chunks extracted, skipping")
                    continue

                print(f"  Extracted {len(chunks)} chunks")

                # Generate embeddings
                print("  Generating embeddings...")
                embedding_result = await embedding_service.embed_texts(chunks)
                embeddings = embedding_result.embeddings

                print(f"  Embedding dimension: {embedding_result.dimension}")

                # Delete existing chunks
                await db.execute(
                    text("DELETE FROM document_chunks WHERE document_id = :doc_id"),
                    {"doc_id": doc.id}
                )

                # Store new chunks with correct dimension
                for idx, (content, embedding) in enumerate(zip(chunks, embeddings)):
                    embedding_str = "[" + ",".join(map(str, embedding)) + "]"

                    chunk = DocumentChunk(
                        document_id=doc.id,
                        chunk_index=idx,
                        content=content,
                        embedding=embedding_str,
                        embedding_dimension=embedding_result.dimension,
                    )
                    db.add(chunk)

                await db.commit()

                total_chunks += len(chunks)
                total_docs += 1
                print(f"  SUCCESS: Stored {len(chunks)} chunks with {embedding_result.dimension} dimensions")

            except Exception as e:
                print(f"  ERROR: {e}")
                await db.rollback()
                continue

        print(f"\n{'='*50}")
        print("Re-embedding complete!")
        print(f"  Documents processed: {total_docs}")
        print(f"  Total chunks updated: {total_chunks}")
        print(f"  New embedding dimension: {embedding_result.dimension}")

        return True


def get_file_path(document: KnowledgeDocument) -> str | None:
    """Get file path for document."""
    import os

    upload_dir = "uploads/knowledge-base"
    merchant_dir = os.path.join(upload_dir, str(document.merchant_id))

    if not os.path.exists(merchant_dir):
        return None

    # Find the actual file (has UUID prefix)
    for filename in os.listdir(merchant_dir):
        if filename.endswith(f"_{document.filename}"):
            return os.path.join(merchant_dir, filename)

    return None


def main():
    parser = argparse.ArgumentParser(description="Re-embed documents for a merchant")
    parser.add_argument("--merchant-id", type=int, required=True, help="Merchant ID")
    parser.add_argument("--db-url", type=str, default=None, help="Database URL")

    args = parser.parse_args()

    # Default database URL
    db_url = args.db_url or "postgresql+asyncpg://developer:developer@localhost:5433/shop_dev"

    print(f"Re-embedding documents for merchant {args.merchant_id}")
    print(f"Database: {db_url.split('@')[1] if '@' in db_url else db_url}")

    asyncio.run(reembed_documents(args.merchant_id, db_url))


if __name__ == "__main__":
    main()
