#!/usr/bin/env python3
"""Direct test of RAG retrieval."""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, '/Users/sherwingorechomante/shop/backend')

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.rag.embedding_service import EmbeddingService
from app.services.rag.retrieval_service import RetrievalService

DATABASE_URL = "postgresql+asyncpg://developer:developer@127.0.0.1:5433/shop_dev"

async def test_rag():
    """Test RAG retrieval directly."""
    # Create database connection
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Create embedding service
        embedding_service = EmbeddingService(
            provider="gemini",
            api_key=None,  # Will use env var
            model="gemini-embedding-001",
            ollama_url=None,
        )

        # Create retrieval service
        retrieval_service = RetrievalService(
            db=db,
            embedding_service=embedding_service,
            similarity_threshold=0.3,  # Lower threshold for testing
            top_k=10,
        )

        # Test query
        query = "where did he graduate"
        print(f"\n🔍 Testing query: '{query}'")
        print("=" * 60)

        try:
            chunks = await retrieval_service.retrieve_relevant_chunks(
                merchant_id=1,
                query=query,
                top_k=10,
                threshold=0.3,
                embedding_version="gemini-gemini-embedding-001",
            )

            print(f"\n✅ Found {len(chunks)} chunks")

            if chunks:
                print("\n📄 Top chunks:")
                for i, chunk in enumerate(chunks[:5], 1):
                    print(f"\n{i}. Chunk ID: {chunk.chunk_id}")
                    print(f"   Document: {chunk.document_name}")
                    print(f"   Similarity: {chunk.similarity:.4f}")
                    print(f"   Content: {chunk.content[:200]}...")

                    # Check for education keywords
                    content_lower = chunk.content.lower()
                    if any(word in content_lower for word in ['ateneo', 'university', 'education', 'college', 'graduated', 'school']):
                        print(f"   ✅ Contains education keywords!")

            else:
                print("\n❌ No chunks found!")
                print("Possible issues:")
                print("1. Embedding generation failed")
                print("2. Similarity threshold too high")
                print("3. Embedding dimension mismatch")
                print("4. Documents not indexed")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_rag())
