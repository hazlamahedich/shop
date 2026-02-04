"""Tests for messaging schemas.

Unit tests for Pydantic validation and webhook payload parsing.
"""

from __future__ import annotations

import pytest

from app.schemas.messaging import (
    FacebookEntry,
    FacebookMessaging,
    FacebookWebhookPayload,
    MessengerResponse,
    ConversationContext,
)


def test_facebook_messaging_schema():
    """Test Facebook messaging schema validation."""
    messaging = FacebookMessaging(
        id="123456",
        text="Hello world",
    )

    assert messaging.sender_id == "123456"
    assert messaging.message_text == "Hello world"


def test_facebook_entry_schema():
    """Test Facebook entry schema validation."""
    entry = FacebookEntry(
        id="123456789",
        time=1234567890,
        messaging=[{
            "sender": {"id": "123456"},
            "message": {"text": "test"},
        }],
    )

    assert entry.id == "123456789"
    assert entry.time == 1234567890
    assert len(entry.messaging) == 1


def test_facebook_webhook_payload_schema():
    """Test Facebook webhook payload schema validation."""
    payload = FacebookWebhookPayload(
        object="page",
        entry=[{
            "id": "123456789",
            "time": 1234567890,
            "messaging": [{
                "sender": {"id": "123456"},
                "message": {"text": "test message"},
            }],
        }],
    )

    assert payload.object == "page"
    assert payload.sender_id == "123456"
    assert payload.message_text == "test message"


def test_facebook_webhook_payload_properties():
    """Test Facebook webhook payload convenience properties."""
    payload = FacebookWebhookPayload(
        object="page",
        entry=[{
            "id": "123456789",
            "time": 1234567890,
            "messaging": [{
                "sender": {"id": "987654"},
                "message": {"text": "hello"},
            }],
        }],
    )

    assert payload.sender_id == "987654"
    assert payload.message_text == "hello"


def test_facebook_webhook_payload_empty_message():
    """Test webhook payload with missing message text."""
    payload = FacebookWebhookPayload(
        object="page",
        entry=[{
            "id": "123456789",
            "time": 1234567890,
            "messaging": [{
                "sender": {"id": "123456"},
                "message": {},  # No text field
            }],
        }],
    )

    assert payload.message_text is None


def test_messenger_response_schema():
    """Test Messenger response schema validation."""
    response = MessengerResponse(
        text="Hello! How can I help?",
        recipient_id="123456",
    )

    assert response.text == "Hello! How can I help?"
    assert response.recipient_id == "123456"


def test_conversation_context_schema():
    """Test conversation context schema validation."""
    context = ConversationContext(
        psid="123456",
        created_at="2024-01-01T00:00:00",
        last_message_at="test message",
        message_count=5,
        previous_intents=["product_search", "greeting"],
        extracted_entities={"category": "shoes", "budget": 100.0},
        conversation_state="active",
    )

    assert context.psid == "123456"
    assert context.created_at == "2024-01-01T00:00:00"
    assert context.message_count == 5
    assert "product_search" in context.previous_intents
    assert context.extracted_entities["category"] == "shoes"
    assert context.conversation_state == "active"


def test_conversation_context_defaults():
    """Test conversation context default values."""
    context = ConversationContext(
        psid="123456",
    )

    assert context.psid == "123456"
    assert context.created_at is None
    assert context.message_count == 0
    assert context.previous_intents == []
    assert context.extracted_entities == {}
    assert context.conversation_state == "active"


def test_messenger_response_camel_case_alias():
    """Test Messenger response camelCase API alias."""
    response = MessengerResponse(
        text="Test",
        recipient_id="123456",
    )

    data = response.model_dump(by_alias=True)
    assert "recipientId" in data
    assert data["recipientId"] == "123456"


def test_facebook_payload_camel_case_alias():
    """Test Facebook payload handles camelCase input."""
    # Test with camelCase input
    payload_data = {
        "object": "page",
        "entry": [{
            "id": "123456789",
            "time": 1234567890,
            "messaging": [{
                "sender": {"id": "123456"},
                "message": {"text": "test"},
            }],
        }],
    }

    payload = FacebookWebhookPayload(**payload_data)
    assert payload.sender_id == "123456"
    assert payload.message_text == "test"
