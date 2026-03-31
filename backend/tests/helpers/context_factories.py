"""Data factory functions for conversation context tests.

Story 11-1: Conversation Context Memory
Provides reusable factory functions to reduce test data duplication.
All factories accept **overrides for flexible test-specific customization.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

from redis import Redis

from app.models.conversation_context import ConversationContext


def create_mock_context(**overrides):
    defaults = {
        "mode": "ecommerce",
        "turn_count": 1,
        "viewed_products": [],
        "cart_items": [],
        "constraints": {},
        "search_history": [],
        "topics_discussed": [],
        "documents_referenced": [],
        "support_issues": [],
        "preferences": {},
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    defaults.update(overrides)
    return defaults


def create_mock_ecommerce_context(**overrides):
    return create_mock_context(
        mode="ecommerce",
        turn_count=3,
        viewed_products=[101, 202],
        cart_items=[101],
        constraints={"budget_max": 50},
        search_history=["blue shoes"],
        preferences={"currency": "USD"},
        **overrides,
    )


def create_mock_general_context(**overrides):
    return create_mock_context(
        mode="general",
        turn_count=2,
        topics_discussed=["billing", "account"],
        documents_referenced=[123],
        support_issues=[{"type": "billing", "status": "pending"}],
        escalation_status="low",
        **overrides,
    )


def create_mock_summary(**overrides):
    defaults = {
        "summary": "Customer is looking for blue shoes under $50.",
        "key_points": ["Interested in blue shoes", "Budget under $50"],
        "active_constraints": {"budget_max": 50, "color": "blue"},
        "original_turns": 3,
        "summarized_at": datetime.now(timezone.utc).isoformat(),
    }
    defaults.update(overrides)
    return defaults


def create_mock_redis_client():
    return MagicMock(spec=Redis)


def create_mock_db_session(**overrides):
    db = AsyncMock()
    for key, value in overrides.items():
        setattr(db, key, value)
    return db


def create_mock_context_model(**overrides):
    now = datetime.now(timezone.utc)
    defaults = {
        "mode": "ecommerce",
        "turn_count": 1,
        "viewed_products": [],
        "cart_items": None,
        "constraints": None,
        "search_history": None,
        "topics_discussed": None,
        "documents_referenced": None,
        "support_issues": None,
        "escalation_status": None,
        "preferences": None,
        "last_summarized_at": None,
        "context_data": {},
        "expires_at": now + timedelta(hours=24),
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)

    model = MagicMock(spec=ConversationContext)
    for key, value in defaults.items():
        setattr(model, key, value)
    return model
