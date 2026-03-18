"""Schema integration tests for Story 10-3: Suggestion Response Schemas.

Tests Pydantic schema validation, API envelope integration
 and camelCase alias handling.

Story 10-3: Quick Reply Chips Widget
"""

from __future__ import annotations

import os
import pytest
from datetime import datetime, timezone

os.environ["IS_TESTING"] = "true"


class TestSuggestionSchemaIntegration:
    """Integration tests for suggestion field in API response schemas."""

    @pytest.fixture
    def sample_suggestions(self):
        """Create sample suggestions."""
        return [
            "Tell me more about Pricing Guide",
            "What about Basic tier?",
            "Can you tell me more?",
            "What else should I know?",
        ]

    @pytest.mark.asyncio
    async def test_conversation_response_includes_suggestions(self, sample_suggestions):
        """[P0] ConversationResponse should include suggested_replies field."""
        from app.services.conversation.schemas import ConversationResponse

        response = ConversationResponse(
            message="Based on our documentation...",
            suggested_replies=sample_suggestions,
        )

        assert response.suggested_replies is not None
        assert len(response.suggested_replies) == 4
        assert response.suggested_replies[0] == "Tell me more about Pricing Guide"

    @pytest.mark.asyncio
    async def test_conversation_response_without_suggestions(self):
        """[P1] ConversationResponse should work without suggestions."""
        from app.services.conversation.schemas import ConversationResponse

        response = ConversationResponse(
            message="Hello! How can I help?",
        )

        assert response.suggested_replies is None

    @pytest.mark.asyncio
    async def test_widget_message_response_includes_suggestions(self, sample_suggestions):
        """[P0] WidgetMessageResponse should include suggestedReplies with alias."""
        from app.schemas.widget import WidgetMessageResponse

        response = WidgetMessageResponse(
            messageId="msg-123",
            content="Based on our documentation...",
            sender="bot",
            createdAt=datetime.now(timezone.utc),
            suggested_replies=sample_suggestions,
        )

        assert response.suggested_replies is not None
        assert len(response.suggested_replies) == 4
        assert response.suggested_replies[0] == "Tell me more about Pricing Guide"

    @pytest.mark.asyncio
    async def test_widget_message_response_camel_case_alias(self, sample_suggestions):
        """[P0] WidgetMessageResponse should use camelCase alias for JSON."""
        from app.schemas.widget import WidgetMessageResponse

        response = WidgetMessageResponse(
            messageId="msg-456",
            content="Response content",
            sender="bot",
            createdAt=datetime.now(timezone.utc),
            suggested_replies=sample_suggestions,
        )

        json_data = response.model_dump(by_alias=True)

        assert "suggestedReplies" in json_data
        assert "suggested_replies" not in json_data

    @pytest.mark.asyncio
    async def test_widget_message_envelope_contains_suggestions(self, sample_suggestions):
        """[P0] Widget message envelope should include suggestions in response."""
        from app.schemas.widget import WidgetMessageResponse, WidgetMessageEnvelope, create_meta

        response = WidgetMessageResponse(
            messageId="msg-789",
            content="Here is the information...",
            sender="bot",
            createdAt=datetime.now(timezone.utc),
            suggested_replies=sample_suggestions,
        )

        envelope = WidgetMessageEnvelope(data=response, meta=create_meta())

        assert envelope.data.suggested_replies is not None
        assert len(envelope.data.suggested_replies) == 4
        assert envelope.meta.request_id is not None

    @pytest.mark.asyncio
    async def test_max_suggestions_in_schema(self):
        """[P1] Schema should accept exactly 4 suggestions."""
        from app.schemas.widget import WidgetMessageResponse

        four_suggestions = [f"Suggestion {i}" for i in range(4)]

        response = WidgetMessageResponse(
            messageId="msg-test",
            content="Content",
            sender="bot",
            createdAt=datetime.now(timezone.utc),
            suggested_replies=four_suggestions,
        )

        assert len(response.suggested_replies) == 4
