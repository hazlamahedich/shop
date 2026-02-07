"""Integration tests for conversations search and filter API endpoints.

Tests full API flow with search and filter parameters including:
- Search by customer ID and message content
- Date range filtering
- Status multi-select filtering
- Sentiment multi-select filtering
- Handoff status filtering
- Combined filters
- Pagination with filtered results
- Merchant isolation with filters
"""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.merchant import Merchant


async def _create_test_merchant(async_session: AsyncSession, key: str = "test") -> Merchant:
    """Helper to create a test merchant."""
    merchant = Merchant(
        merchant_key=f"test-search-{key}",
        platform="facebook",
        status="active",
    )
    async_session.add(merchant)
    await async_session.commit()
    await async_session.refresh(merchant)
    return merchant


async def _get_authenticated_client(async_session: AsyncSession, merchant: Merchant):
    """Create an authenticated client for testing conversations endpoint."""
    from app.main import app
    from app.core.database import get_db
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.types import ASGIApp

    # Override get_db dependency
    async def override_get_db():
        yield async_session

    # Create middleware to inject merchant_id into request.state
    class AuthMiddleware(BaseHTTPMiddleware):
        def __init__(self, app: ASGIApp, merchant_id: int):
            super().__init__(app)
            self.merchant_id = merchant_id

        async def dispatch(self, request, call_next):
            # Inject merchant_id into request.state for authenticated requests
            request.state.merchant_id = self.merchant_id
            response = await call_next(request)
            return response

    # Add middleware and override dependencies
    original_user_middleware = app.user_middleware.copy()
    app.dependency_overrides[get_db] = override_get_db
    app.add_middleware(AuthMiddleware, merchant_id=merchant.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            yield client
    finally:
        # Clean up
        app.dependency_overrides.clear()
        app.user_middleware = original_user_middleware
        # Reset middleware stack
        app.middleware_stack = None
        app.build_middleware_stack()  # type: ignore


@pytest.fixture(scope="function")
async def authenticated_client(async_session: AsyncSession):
    """Create an authenticated client with a test merchant."""
    merchant = await _create_test_merchant(async_session)
    async for client in _get_authenticated_client(async_session, merchant):
        yield client, merchant.id


@pytest.mark.asyncio
class TestConversationsSearchFiltersIntegration:
    """Integration tests for conversations search and filter functionality."""

    async def test_search_by_customer_id_filters_results(
        self, authenticated_client: tuple[AsyncClient, int], async_session: AsyncSession
    ):
        """Test searching by customer ID returns only matching conversations."""
        client, merchant_id = authenticated_client

        conv1 = Conversation(
            merchant_id=merchant_id,
            platform="facebook",
            platform_sender_id="customer_search_123",
            status="active",
        )
        conv2 = Conversation(
            merchant_id=merchant_id,
            platform="facebook",
            platform_sender_id="different_customer",
            status="active",
        )
        async_session.add_all([conv1, conv2])
        await async_session.commit()

        # Search for specific customer
        response = await client.get(
            "/api/conversations",
            params={"search": "customer_search_123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["platformSenderIdMasked"] == "cust****"

    async def test_search_by_message_content_filters_results(
        self, authenticated_client: tuple[AsyncClient, int], async_session: AsyncSession
    ):
        """Test searching by bot message content returns matching conversations."""
        client, merchant_id = authenticated_client

        # Create conversations with messages
        conv1 = Conversation(
            merchant_id=merchant_id,
            platform="facebook",
            platform_sender_id="customer_1",
            status="active",
        )
        conv2 = Conversation(
            merchant_id=merchant_id,
            platform="facebook",
            platform_sender_id="customer_2",
            status="active",
        )

        async_session.add_all([conv1, conv2])
        await async_session.flush()

        # Add bot messages (plaintext, searchable)
        msg1 = Message(
            conversation_id=conv1.id,
            sender="bot",
            content="I found running shoes for you",
            message_type="text",
        )
        msg2 = Message(
            conversation_id=conv2.id,
            sender="bot",
            content="Product recommendation",
            message_type="text",
        )
        async_session.add_all([msg1, msg2])
        await async_session.commit()

        # Search for "shoes" in bot messages
        response = await client.get(
            "/api/conversations",
            params={"search": "shoes"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1

    async def test_search_case_insensitive(
        self, authenticated_client: tuple[AsyncClient, int], async_session: AsyncSession
    ):
        """Test search is case-insensitive."""
        client, merchant_id = authenticated_client

        conv = Conversation(
            merchant_id=merchant_id,
            platform="facebook",
            platform_sender_id="CUSTOMER_ABC",
            status="active",
        )
        async_session.add(conv)
        await async_session.commit()

        # Search with lowercase
        response = await client.get(
            "/api/conversations",
            params={"search": "customer_abc"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1

    async def test_date_range_filter_from_date_only(
        self, authenticated_client: tuple[AsyncClient, int], async_session: AsyncSession
    ):
        """Test filtering by date range with only start date."""
        from datetime import datetime, timedelta

        client, merchant_id = authenticated_client
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        two_days_ago = today - timedelta(days=2)

        conv1 = Conversation(
            merchant_id=merchant_id,
            platform="facebook",
            platform_sender_id="customer_1",
            status="active",
            created_at=yesterday,
        )
        conv2 = Conversation(
            merchant_id=merchant_id,
            platform="facebook",
            platform_sender_id="customer_2",
            status="active",
            created_at=two_days_ago,
        )
        async_session.add_all([conv1, conv2])
        await async_session.commit()

        # Filter from yesterday onwards
        response = await client.get(
            "/api/conversations",
            params={"date_from": yesterday.strftime("%Y-%m-%d")},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1

    async def test_status_filter_single_value(
        self, authenticated_client: tuple[AsyncClient, int], async_session: AsyncSession
    ):
        """Test filtering by single status value."""
        client, merchant_id = authenticated_client

        conv1 = Conversation(
            merchant_id=merchant_id,
            platform="facebook",
            platform_sender_id="customer_1",
            status="active",
        )
        conv2 = Conversation(
            merchant_id=merchant_id,
            platform="facebook",
            platform_sender_id="customer_2",
            status="closed",
        )
        async_session.add_all([conv1, conv2])
        await async_session.commit()

        # Filter for active only
        response = await client.get(
            "/api/conversations",
            params={"status": "active"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["status"] == "active"

    async def test_status_filter_multiple_values(
        self, authenticated_client: tuple[AsyncClient, int], async_session: AsyncSession
    ):
        """Test filtering by multiple status values."""
        client, merchant_id = authenticated_client

        conv1 = Conversation(
            merchant_id=merchant_id,
            platform="facebook",
            platform_sender_id="customer_1",
            status="active",
        )
        conv2 = Conversation(
            merchant_id=merchant_id,
            platform="facebook",
            platform_sender_id="customer_2",
            status="handoff",
        )
        conv3 = Conversation(
            merchant_id=merchant_id,
            platform="facebook",
            platform_sender_id="customer_3",
            status="closed",
        )
        async_session.add_all([conv1, conv2, conv3])
        await async_session.commit()

        # Filter for active and handoff
        response = await client.get(
            "/api/conversations",
            params={"status": ["active", "handoff"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        statuses = {c["status"] for c in data["data"]}
        assert statuses == {"active", "handoff"}

    async def test_sentiment_filter_multiple_values(
        self, authenticated_client: tuple[AsyncClient, int], async_session: AsyncSession
    ):
        """Test filtering by multiple sentiment values.

        Note: Sentiment analysis is not yet implemented - all conversations return "neutral".
        This test verifies the API accepts sentiment filter params even though filtering is a no-op.
        """
        client, merchant_id = authenticated_client

        conv1 = Conversation(
            merchant_id=merchant_id,
            platform="facebook",
            platform_sender_id="customer_1",
            status="active",
        )
        conv2 = Conversation(
            merchant_id=merchant_id,
            platform="facebook",
            platform_sender_id="customer_2",
            status="active",
        )
        conv3 = Conversation(
            merchant_id=merchant_id,
            platform="facebook",
            platform_sender_id="customer_3",
            status="active",
        )
        async_session.add_all([conv1, conv2, conv3])
        await async_session.commit()

        # Filter for positive and negative - API accepts params but filtering is placeholder
        # All conversations will be returned with sentiment="neutral"
        response = await client.get(
            "/api/conversations",
            params={"sentiment": ["positive", "negative"]},
        )

        assert response.status_code == 200
        data = response.json()
        # All 3 conversations returned (no actual filtering implemented)
        assert len(data["data"]) == 3
        # All sentiments are "neutral" (placeholder)
        sentiments = {c["sentiment"] for c in data["data"]}
        assert sentiments == {"neutral"}

    async def test_handoff_filter_has_handoff(
        self, authenticated_client: tuple[AsyncClient, int], async_session: AsyncSession
    ):
        """Test filtering for conversations with handoff status."""
        client, merchant_id = authenticated_client

        conv1 = Conversation(
            merchant_id=merchant_id,
            platform="facebook",
            platform_sender_id="customer_1",
            status="handoff",
        )
        conv2 = Conversation(
            merchant_id=merchant_id,
            platform="facebook",
            platform_sender_id="customer_2",
            status="active",
        )
        async_session.add_all([conv1, conv2])
        await async_session.commit()

        # Filter for has_handoff=true (status=handoff)
        response = await client.get(
            "/api/conversations",
            params={"has_handoff": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["status"] == "handoff"

    async def test_combined_filters_search_and_status(
        self, authenticated_client: tuple[AsyncClient, int], async_session: AsyncSession
    ):
        """Test combining search and status filters."""
        client, merchant_id = authenticated_client

        conv1 = Conversation(
            merchant_id=merchant_id,
            platform="facebook",
            platform_sender_id="searchable_customer_1",
            status="active",
        )
        conv2 = Conversation(
            merchant_id=merchant_id,
            platform="facebook",
            platform_sender_id="searchable_customer_2",
            status="closed",
        )
        conv3 = Conversation(
            merchant_id=merchant_id,
            platform="facebook",
            platform_sender_id="other_customer",
            status="active",
        )
        async_session.add_all([conv1, conv2, conv3])
        await async_session.commit()

        # Search for "searchable" and status=active
        response = await client.get(
            "/api/conversations",
            params={
                "search": "searchable",
                "status": "active",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["platformSenderIdMasked"] == "sear****"

    async def test_pagination_with_filters(
        self, authenticated_client: tuple[AsyncClient, int], async_session: AsyncSession
    ):
        """Test pagination total count reflects filtered results."""
        client, merchant_id = authenticated_client

        # Create 25 conversations, 10 with "test" in sender ID
        for i in range(25):
            conv = Conversation(
                merchant_id=merchant_id,
                platform="facebook",
                platform_sender_id=f"test_customer_{i}" if i < 10 else f"other_customer_{i}",
                status="active",
            )
            async_session.add(conv)
        await async_session.commit()

        # Search for "test" with per_page=5
        response = await client.get(
            "/api/conversations",
            params={
                "search": "test",
                "per_page": 5,
                "page": 1,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 5
        assert data["meta"]["pagination"]["total"] == 10
        assert data["meta"]["pagination"]["totalPages"] == 2

    async def test_empty_search_returns_no_results(
        self, authenticated_client: tuple[AsyncClient, int], async_session: AsyncSession
    ):
        """Test search with no matches returns empty result."""
        client, merchant_id = authenticated_client

        conv = Conversation(
            merchant_id=merchant_id,
            platform="facebook",
            platform_sender_id="customer_123",
            status="active",
        )
        async_session.add(conv)
        await async_session.commit()

        # Search for non-existent term
        response = await client.get(
            "/api/conversations",
            params={"search": "nonexistent_term_xyz"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 0
        assert data["meta"]["pagination"]["total"] == 0

    async def test_invalid_date_format_returns_error(
        self, authenticated_client: tuple[AsyncClient, int], async_session: AsyncSession
    ):
        """Test invalid date format returns proper error code."""
        client, merchant_id = authenticated_client

        response = await client.get(
            "/api/conversations",
            params={"date_from": "invalid-date"},
        )

        assert response.status_code == 400
        data = response.json()
        # APIError responses have 'error_code', 'message' format
        assert "error_code" in data
        assert "message" in data
        assert "date" in str(data["message"]).lower() or "format" in str(data["message"]).lower()

    async def test_invalid_status_value_returns_error(
        self, authenticated_client: tuple[AsyncClient, int], async_session: AsyncSession
    ):
        """Test invalid status value returns proper error code."""
        client, merchant_id = authenticated_client

        response = await client.get(
            "/api/conversations",
            params={"status": "invalid_status"},
        )

        assert response.status_code == 400
        data = response.json()
        # APIError responses have 'error_code', 'message' format
        assert "error_code" in data
        assert "message" in data
        assert "status" in str(data["message"]).lower()

    async def test_invalid_sentiment_value_returns_error(
        self, authenticated_client: tuple[AsyncClient, int], async_session: AsyncSession
    ):
        """Test invalid sentiment value returns proper error code."""
        client, merchant_id = authenticated_client

        response = await client.get(
            "/api/conversations",
            params={"sentiment": "invalid_sentiment"},
        )

        assert response.status_code == 400
        data = response.json()
        # APIError responses have 'error_code', 'message' format
        assert "error_code" in data
        assert "message" in data
        assert "sentiment" in str(data["message"]).lower()

    @pytest.mark.parametrize(
        "search_term,expected_count",
        [
            ("test", 2),  # Partial match
            ("TEST", 2),  # Case insensitive
            ("est", 2),  # Partial match middle
            ("xyz", 0),  # No match
        ],
    )
    async def test_search_partial_matching(
        self,
        authenticated_client: tuple[AsyncClient, int],
        async_session: AsyncSession,
        search_term: str,
        expected_count: int,
    ):
        """Test search uses partial matching (contains, not exact)."""
        client, merchant_id = authenticated_client

        conv1 = Conversation(
            merchant_id=merchant_id,
            platform="facebook",
            platform_sender_id="test_customer_1",
            status="active",
        )
        conv2 = Conversation(
            merchant_id=merchant_id,
            platform="facebook",
            platform_sender_id="test_customer_2",
            status="active",
        )
        async_session.add_all([conv1, conv2])
        await async_session.commit()

        response = await client.get(
            "/api/conversations",
            params={"search": search_term},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == expected_count
