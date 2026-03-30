#!/usr/bin/env python3
"""Test RAG similarity for location queries."""
import asyncio
import sys
import os

# Change to backend directory and add to path
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

from app.core.database import async_session
from app.services.rag.embedding_service import EmbeddingService
from sqlalchemy import text
import numpy as np

async def test_location_similarity():
    """Test embedding similarity for location query."""
    # Create embedding service
    embedding_service = EmbeddingService(
        provider='gemini',
        api_key=None,
        model='gemini-embedding-001',
        ollama_url=None,
    )

    async with async_session() as db:
        # Get the resume chunk with location
        result = await db.execute(text('''
            SELECT dc.id, dc.content, dc.embedding::text
            FROM document_chunks dc
            JOIN knowledge_documents kd ON dc.document_id = kd.id
            WHERE kd.merchant_id = 1
            AND kd.filename ILIKE '%resume%'
            AND dc.chunk_index = 0
        '''))
        chunk = result.fetchone()

        if not chunk:
            print("❌ Resume chunk not found!")
            return

        chunk_id, chunk_content, chunk_embedding_json = chunk
        print(f"📄 Resume Chunk (ID: {chunk_id}):")
        print(f"   Content: {chunk_content[:200]}...")
        print()

        # Test different location queries
        queries = [
            "where is he located",
            "what is his address",
            "where does he live",
            "location",
            "address",
            "contact information",
        ]

        print("🔍 Testing similarity scores:")
        print("=" * 70)

        for query in queries:
            try:
                # Generate query embedding
                query_embedding = await embedding_service.embed_query(query)
                query_np = np.array(query_embedding, dtype=np.float32)

                # Parse chunk embedding
                import json
                inner_string = json.loads(chunk_embedding_json)
                chunk_embedding_list = json.loads(inner_string)
                chunk_np = np.array(chunk_embedding_list, dtype=np.float32)

                # Calculate cosine similarity
                dot_product = np.dot(query_np, chunk_np)
                norm_query = np.linalg.norm(query_np)
                norm_chunk = np.linalg.norm(chunk_np)

                if norm_query > 0 and norm_chunk > 0:
                    similarity = dot_product / (norm_query * norm_chunk)
                else:
                    similarity = 0.0

                status = "✅ PASS" if similarity >= 0.5 else "⚠️  LOW" if similarity >= 0.3 else "❌ FAIL"
                print(f"{status}  '{query}'")
                print(f"       Similarity: {similarity:.4f} (threshold: 0.5)")
                print()

            except Exception as e:
                print(f"❌ Error for '{query}': {e}")
                print()

if __name__ == '__main__':
    asyncio.run(test_location_similarity())
