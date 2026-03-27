# Definitive Fix for RAG Greenlet Errors

## Root Cause Analysis

The recurring greenlet error `"greenlet_spawn has not been called; can't call await_only() here"` occurs because:

1. **Mixed async/sync contexts**: The RAG pipeline is initialized in one async context but accessed from another
2. **Database session reuse**: `AsyncSession` objects are being passed across async boundaries incorrectly
3. **HTTP client lifecycle**: The `httpx.AsyncClient` in EmbeddingService is not properly managed across requests
4. **No session isolation**: Each request should have its own isolated database session for RAG operations

## The Problems

### Problem 1: Session Lifecycle Mismanagement
```python
# Current problematic flow:
async def process_message(...):
    # Create RAG components with shared session
    rag_builder = await self._build_rag_context_builder(db=self.db, ...)
    # Pass to UnifiedConversationService
    unified_service = UnifiedConversationService(
        db=self.db,  # Same session passed around
        rag_context_builder=rag_builder  # Contains RetrievalService with self.db
    )
    # Later, when RAG is used:
    await rag_builder.build_rag_context_with_chunks(...)
    # This tries to use the session from a different async context!
```

### Problem 2: Retrieval Service Holding Session Reference
```python
class RetrievalService:
    def __init__(self, db: AsyncSession, ...):
        self.db = db  # Stores session that might expire or be from wrong context

    async def retrieve_relevant_chunks(...):
        result = await self.db.execute(...)  # Greenlet error here!
```

### Problem 3: No Request-Scoped Isolation
Each RAG request should use a fresh database session, not share one across the entire request lifecycle.

## Definitive Solution

### Step 1: Create Request-Scoped Session Factory

```python
# backend/app/services/rag/session_factory.py
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

class RAGSessionFactory:
    """Factory for creating request-scoped database sessions for RAG operations."""

    def __init__(self, session_maker):
        self.session_maker = session_maker

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Create a fresh database session for each RAG operation."""
        async with self.session_maker() as session:
            yield session
```

### Step 2: Modify Retrieval Service to Accept Session Factory

```python
# backend/app/services/rag/retrieval_service.py
class RetrievalService:
    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],  # Factory, not instance
        embedding_service: EmbeddingService,
        similarity_threshold: float = SIMILARITY_THRESHOLD,
        top_k: int = TOP_K_DEFAULT,
    ):
        self.session_factory = session_factory
        self.embedding_service = embedding_service
        self.similarity_threshold = similarity_threshold
        self.top_k = top_k

    async def retrieve_relevant_chunks(
        self,
        merchant_id: int,
        query: str,
        top_k: int | None = None,
        threshold: float | None = None,
        embedding_version: str | None = None,
    ) -> list[RetrievedChunk]:
        # Create fresh session for this retrieval
        async with self.session_factory() as db:
            # Use db only within this scope
            ...
```

### Step 3: Update RAG Context Builder

```python
# backend/app/services/rag/context_builder.py
class RAGContextBuilder:
    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],  # Factory
        embedding_service: EmbeddingService,
        llm_service: BaseLLMService | None = None,
    ):
        self.retrieval_service = RetrievalService(
            session_factory=session_factory,  # Pass factory
            embedding_service=embedding_service,
        )
```

### Step 4: Update Widget Message Service

```python
# backend/app/services/widget/widget_message_service.py
async def _build_rag_context_builder(
    self,
    merchant_id: int,
    ...
):
    # Create session factory instead of passing session directly
    from app.core.database import async_session

    def session_factory():
        return async_session()

    embedding_service = EmbeddingService(...)

    rag_context_builder = RAGContextBuilder(
        session_factory=session_factory,  # Pass factory
        embedding_service=embedding_service,
        llm_service=None,  # Don't pass LLM service (causes issues)
    )

    return rag_context_builder
```

### Step 5: Add Regression Tests

```python
# backend/tests/integration/test_rag_greenlet_fix.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_rag_with_concurrent_requests(async_client: AsyncClient):
    """Test that RAG works with multiple concurrent requests."""
    session_responses = await asyncio.gather(*[
        async_client.post("/api/v1/widget/session", json={"merchant_id": "1"})
        for _ in range(5)
    ])

    session_ids = [r.json()["data"]["sessionId"] for r in session_responses]

    # Send concurrent messages with RAG queries
    message_responses = await asyncio.gather(*[
        async_client.post("/api/v1/widget/message", json={
            "session_id": sid,
            "message": "where did he graduate"
        })
        for sid in session_ids
    ])

    # All should succeed without greenlet errors
    for r in message_responses:
        assert r.status_code == 200
        assert "greenlet" not in r.text.lower()

@pytest.mark.asyncio
async def test_rag_multiple_queries_same_session(async_client: AsyncClient):
    """Test that RAG works for multiple queries in the same session."""
    # Create session
    session_resp = await async_client.post("/api/v1/widget/session", json={"merchant_id": "1"})
    session_id = session_resp.json()["data"]["sessionId"]

    queries = [
        "where did he graduate",
        "what university did he attend",
        "education background"
    ]

    for query in queries:
        response = await async_client.post("/api/v1/widget/message", json={
            "session_id": session_id,
            "message": query
        })
        assert response.status_code == 200
        assert "greenlet" not in response.text.lower()
```

### Step 6: Add Health Check Monitoring

```python
# backend/app/api/health.py
@router.get("/health/rag")
async def check_rag_health(db: AsyncSession = Depends(get_db)):
    """Check if RAG is working properly."""
    try:
        # Test RAG with a simple query
        merchant = await db.execute(select(Merchant).where(Merchant.id == 1))
        merchant = merchant.scalar_one_or_none()

        if not merchant or merchant.onboarding_mode != "general":
            return {"status": "skipped", "reason": "No general mode merchant"}

        # Try RAG retrieval
        from app.services.rag.embedding_service import EmbeddingService
        from app.services.rag.retrieval_service import RetrievalService

        embedding_service = EmbeddingService(provider="gemini", ...)
        retrieval_service = RetrievalService(
            session_factory=lambda: db,
            embedding_service=embedding_service,
        )

        chunks = await retrieval_service.retrieve_relevant_chunks(
            merchant_id=1,
            query="test query",
            top_k=1,
            threshold=0.1,
        )

        return {"status": "healthy", "chunks_found": len(chunks)}

    except Exception as e:
        logger.error("rag_health_check_failed", error=str(e))
        return {"status": "unhealthy", "error": str(e)}
```

## Implementation Priority

1. **HIGH**: Modify RetrievalService to use session factory (Step 2)
2. **HIGH**: Update RAGContextBuilder initialization (Step 3)
3. **HIGH**: Update WidgetMessageService to pass session factory (Step 4)
4. **MEDIUM**: Add regression tests (Step 5)
5. **LOW**: Add health check monitoring (Step 6)

## Why This Fix is Permanent

1. **Session isolation**: Each RAG operation gets its own database session
2. **No cross-context sharing**: Sessions are created and destroyed within the same async context
3. **Testable**: The factory pattern makes it easy to test with mock sessions
4. **Monitorable**: Health checks can detect issues before they affect users
5. **No regression tests**: Tests ensure future changes don't break RAG

## Testing the Fix

After implementation:

```bash
# Run the regression tests
pytest backend/tests/integration/test_rag_greenlet_fix.py -v

# Run the existing test script
./test_graduation_simple.sh

# Check health endpoint
curl http://localhost:8000/health/rag
```
