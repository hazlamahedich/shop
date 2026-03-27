"""Test RAG regression to ensure greenlet errors don't resurface."""
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_rag_graduation_question():
    """Test that RAG correctly answers 'where did he graduate' without greenlet errors.

    This is a regression test for the recurring greenlet error:
    "greenlet_spawn has not been called; can't call await_only() here"

    The fix ensures that:
    1. Database sessions are created per-request (not reused)
    2. EmbeddingService uses proper async HTTP clients
    3. RAG operations use session factories, not direct session instances

    Related issues:
    - Commit: 0f6375c8 "fix: resolve RAG greenlet error in widget message service"
    - Definitive fix: IMPLEMENTATIVE_RAG_FIX.md
    """
    from app.main import app
    from app.core.database import async_session

    # Create test client
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Step 1: Create session
        session_response = await client.post(
            "/api/v1/widget/session",
            json={"merchant_id": "1"}
        )
        assert session_response.status_code == 200
        session_data = session_response.json()
        session_id = session_data["data"]["sessionId"]

        # Step 2: Send greeting
        greeting_response = await client.post(
            "/api/v1/widget/message",
            json={
                "session_id": session_id,
                "message": "hello"
            }
        )
        assert greeting_response.status_code == 200

        # Step 3: Ask about graduation (the critical RAG test)
        graduation_response = await client.post(
            "/api/v1/widget/message",
            json={
                "session_id": session_id,
                "message": "where did he graduate"
            }
        )

        # Must succeed without greenlet errors
        assert graduation_response.status_code == 200, \
            f"Expected 200, got {graduation_response.status_code}: {graduation_response.text}"

        response_data = graduation_response.json()
        content = response_data["data"]["content"].lower()
        sources = response_data["data"].get("sources")

        # Verify RAG worked
        assert "ateneo" in content or "university" in content, \
            f"RAG failed to find university info. Response: {content}"

        # Verify sources are provided (proves RAG was used)
        assert sources is not None and len(sources) > 0, \
            "RAG sources not provided - retrieval may have failed"

        # Verify the correct document was retrieved
        source_titles = [s.get("title", "") for s in sources]
        assert any("resume" in title.lower() for title in source_titles), \
            f"Wrong document retrieved. Expected resume, got: {source_titles}"


@pytest.mark.asyncio
async def test_rag_concurrent_requests():
    """Test that RAG works with multiple concurrent requests without greenlet errors.

    This tests that the session factory approach properly isolates
    database operations across concurrent requests.
    """
    from app.main import app
    from httpx import AsyncClient, ASGITransport

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create 5 sessions
        session_ids = []
        for _ in range(5):
            response = await client.post(
                "/api/v1/widget/session",
                json={"merchant_id": "1"}
            )
            assert response.status_code == 200
            session_ids.append(response.json()["data"]["sessionId"])

        # Send concurrent RAG queries
        async def send_query(session_id: str):
            response = await client.post(
                "/api/v1/widget/message",
                json={
                    "session_id": session_id,
                    "message": "what is his education background"
                }
            )
            return response

        # Execute all queries concurrently
        responses = await asyncio.gather(*[
            send_query(sid) for sid in session_ids
        ])

        # All should succeed
        for i, response in enumerate(responses):
            assert response.status_code == 200, \
                f"Concurrent query {i} failed: {response.text}"
            content = response.json()["data"]["content"].lower()
            # Each should find education info
            assert "education" in content or "university" in content or "ateneo" in content, \
                f"Concurrent query {i} didn't find education info"


@pytest.mark.asyncio
async def test_rag_multiple_queries_same_session():
    """Test that RAG works for multiple queries in the same session.

    This ensures session factory doesn't break sequential queries.
    """
    from app.main import app
    from httpx import AsyncClient, ASGITransport

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create session
        response = await client.post(
            "/api/v1/widget/session",
            json={"merchant_id": "1"}
        )
        session_id = response.json()["data"]["sessionId"]

        # Send multiple RAG queries sequentially
        queries = [
            "where did he graduate",
            "what university did he attend",
            "education background"
        ]

        for i, query in enumerate(queries):
            response = await client.post(
                "/api/v1/widget/message",
                json={
                    "session_id": session_id,
                    "message": query
                }
            )

            assert response.status_code == 200, \
                f"Query {i+1} '{query}' failed: {response.text}"

            content = response.json()["data"]["content"].lower()
            sources = response.json()["data"].get("sources")

            # Verify RAG worked for each query
            assert sources is not None and len(sources) > 0, \
                f"Query {i+1} '{query}' has no sources (RAG failed)"

            # At least one should mention Ateneo specifically
            if i == 0:  # First query should be specific
                assert "ateneo" in content, \
                    f"Query {i+1} should mention Ateneo: {content}"


if __name__ == "__main__":
    # Run tests locally
    import sys
    pytest.main([__file__, "-v", "-s"] + sys.argv[1:])
