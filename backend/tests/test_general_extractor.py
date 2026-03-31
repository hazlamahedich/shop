"""Story 11-1: Unit tests for GeneralContextExtractor and context expiry.

Tests general-mode topic extraction, support issue detection,
escalation keyword detection, context merging, and expiry behavior.

Acceptance Criteria:
- Topics extracted from general conversations
- Support issues classified by type
- Escalation keywords detected
- Context merging preserves existing data
- Contexts expire after 24 hours
"""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.conversation_context import ConversationContext
from app.services.conversation_context import ConversationContextService
from app.services.context import GeneralContextExtractor
from tests.helpers.context_factories import (
    create_mock_context,
    create_mock_context_model,
    create_mock_db_session,
    create_mock_redis_client,
)


@pytest.fixture
def mock_redis():
    """Mock Redis client with proper spec."""
    return create_mock_redis_client()


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    return create_mock_db_session()


class TestGeneralContextExtractor:
    """Test General mode context extractor."""

    @pytest.mark.asyncio
    async def test_extract_topics_discussed(self):
        """Topics extracted from general conversation messages. [11.1-EXT-006]"""
        # Given: A general context extractor
        extractor = GeneralContextExtractor()

        # When: Message mentions login problems
        updates = await extractor.extract("I'm having login problems", {})
        # Then: Login topic is tracked
        assert "topics_discussed" in updates
        assert "login" in updates["topics_discussed"]

    @pytest.mark.asyncio
    async def test_extract_support_issues(self):
        """Support issues detected and classified by type. [11.1-EXT-007]"""
        # Given: A general context extractor
        extractor = GeneralContextExtractor()

        # When: Message mentions billing issue
        updates = await extractor.extract("I was charged incorrectly", {})
        # Then: Billing support issue classified
        assert "support_issues" in updates
        assert any(issue["type"] == "billing" for issue in updates["support_issues"])

    @pytest.mark.asyncio
    async def test_detect_escalation_keywords(self):
        """Escalation status set based on keyword detection. [11.1-EXT-008]"""
        # Given: A general context extractor
        extractor = GeneralContextExtractor()

        # When: Message contains "speak to a human"
        updates = await extractor.extract("I need to speak to a human", {})
        # Then: Escalation is high
        assert updates.get("escalation_status") == "high"

        # When: Message contains frustration
        updates = await extractor.extract("I'm frustrated with this", {})
        # Then: Escalation is medium
        assert updates.get("escalation_status") == "medium"

    @pytest.mark.asyncio
    async def test_merge_with_existing_context(self):
        """Merge preserves existing topics while adding new ones. [11.1-EXT-009]"""
        # Given: Existing context with login topic
        extractor = GeneralContextExtractor()
        existing = {
            "topics_discussed": ["login"],
            "support_issues": [{"type": "login", "status": "pending"}],
        }

        # When: Extracting delta for billing issue
        updates = await extractor.extract("Now I have billing issues", existing)
        # Then: Billing is in the delta
        assert "billing" in updates["topics_discussed"]

        # When: Merging delta with existing
        merged = extractor._merge_context(existing, updates)
        # Then: Both old and new topics preserved
        assert "login" in merged["topics_discussed"]
        assert "billing" in merged["topics_discussed"]


class TestContextExpiry:
    """Test 24-hour expiration behavior."""

    @pytest.mark.asyncio
    async def test_context_expires_after_24h(self, mock_redis, mock_db_session):
        """Contexts with past expiry date return None. [11.1-EXT-010]"""
        # Given: An expired context in DB
        mock_context_model = create_mock_context_model(
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_context_model

        async def mock_execute(stmt):
            return mock_result

        mock_db_session.execute = mock_execute

        # When: Retrieving expired context
        service = ConversationContextService(db=mock_db_session, redis_client=mock_redis)
        result = await service.get_context(123)

        # Then: Returns None
        assert result is None

    @pytest.mark.asyncio
    async def test_cross_session_context_restoration(self, mock_redis, mock_db_session):
        """Context restores correctly within the 24-hour window. [11.1-EXT-011]"""
        # Given: Context from 1 hour ago (still valid)
        hour_ago_context = create_mock_context(
            mode="ecommerce",
            turn_count=5,
            viewed_products=[123, 456],
            constraints={"budget_max": 100},
        )
        mock_redis.get.return_value = json.dumps(hour_ago_context)

        # When: User returns after 1 hour
        service = ConversationContextService(db=mock_db_session, redis_client=mock_redis)
        result = await service.get_context(123)

        # Then: Context is restored
        assert result is not None
        assert result["turn_count"] == 5
        assert result["viewed_products"] == [123, 456]
