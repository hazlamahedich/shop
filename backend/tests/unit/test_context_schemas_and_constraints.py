"""Unit tests for Story 11.1 schema serialization and constraint contradiction logging."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from app.schemas.conversation_context import (
    ContextSummary,
    ConversationContextResponse,
    ConversationContextUpdate,
)


NOW = datetime.now(timezone.utc)


def _make_response_data(**overrides):
    base = {
        "id": 1,
        "conversation_id": 42,
        "merchant_id": 10,
        "mode": "ecommerce",
        "turn_count": 5,
        "expires_at": NOW,
        "created_at": NOW,
        "updated_at": NOW,
    }
    base.update(overrides)
    return base


class TestConversationContextResponse:
    def test_serializes_snake_case_to_camel_case(self):
        # Given
        data = _make_response_data()
        # When
        resp = ConversationContextResponse(**data)
        dumped = resp.model_dump(by_alias=True)
        # Then
        assert "conversationId" in dumped
        assert "merchantId" in dumped
        assert "turnCount" in dumped
        assert "expiresAt" in dumped
        assert "createdAt" in dumped
        assert "updatedAt" in dumped
        assert "viewedProducts" in dumped
        assert "cartItems" in dumped
        assert dumped["conversationId"] == 42
        assert dumped["mode"] == "ecommerce"

    def test_handles_none_optional_fields(self):
        # Given
        data = _make_response_data(
            viewed_products=None,
            cart_items=None,
            constraints=None,
            search_history=None,
            topics_discussed=None,
            documents_referenced=None,
            support_issues=None,
            escalation_status=None,
            preferences=None,
            last_summarized_at=None,
        )
        # When
        resp = ConversationContextResponse(**data)
        dumped = resp.model_dump(by_alias=True)
        # Then
        assert dumped["viewedProducts"] is None
        assert dumped["cartItems"] is None
        assert dumped["constraints"] is None
        assert dumped["searchHistory"] is None
        assert dumped["topicsDiscussed"] is None
        assert dumped["documentsReferenced"] is None
        assert dumped["supportIssues"] is None
        assert dumped["escalationStatus"] is None
        assert dumped["preferences"] is None
        assert dumped["lastSummarizedAt"] is None

    def test_populates_optional_ecommerce_fields(self):
        # Given
        data = _make_response_data(
            viewed_products=[1, 2, 3],
            cart_items=[4, 5],
            constraints={"budget_max": 100},
            search_history=["shoes", "red"],
        )
        # When
        resp = ConversationContextResponse(**data)
        dumped = resp.model_dump(by_alias=True)
        # Then
        assert dumped["viewedProducts"] == [1, 2, 3]
        assert dumped["cartItems"] == [4, 5]
        assert dumped["constraints"] == {"budget_max": 100}
        assert dumped["searchHistory"] == ["shoes", "red"]


class TestConversationContextUpdate:
    def test_accepts_camel_case_input(self):
        # Given
        payload = {"message": "I want red shoes", "mode": "ecommerce"}
        # When
        update = ConversationContextUpdate(**payload)
        # Then
        assert update.message == "I want red shoes"
        assert update.mode == "ecommerce"

    def test_accepts_alias_camel_case(self):
        # Given
        payload = {"message": "hello", "mode": "general"}
        # When
        update = ConversationContextUpdate(**payload)
        # Then
        assert update.message == "hello"
        assert update.mode == "general"

    def test_rejects_invalid_mode(self):
        # Given
        payload = {"message": "hello", "mode": "invalid_mode"}
        # When / Then
        with pytest.raises(ValidationError) as exc_info:
            ConversationContextUpdate(**payload)
        assert "mode" in str(exc_info.value).lower() or "literal" in str(exc_info.value).lower()

    def test_rejects_missing_message(self):
        # Given
        payload = {"mode": "ecommerce"}
        # When / Then
        with pytest.raises(ValidationError):
            ConversationContextUpdate(**payload)


class TestContextSummary:
    def test_serializes_correctly(self):
        # Given
        data = {
            "summary": "User wants red shoes under $100",
            "key_points": ["budget_max: 100", "color: red"],
            "active_constraints": {"budget_max": 100, "color": "red"},
            "original_turns": 8,
            "summarized_at": NOW,
        }
        # When
        summary = ContextSummary(**data)
        dumped = summary.model_dump(by_alias=True)
        # Then
        assert dumped["summary"] == "User wants red shoes under $100"
        assert dumped["keyPoints"] == ["budget_max: 100", "color: red"]
        assert dumped["activeConstraints"] == {"budget_max": 100, "color": "red"}
        assert dumped["originalTurns"] == 8
        assert "summarizedAt" in dumped

    def test_handles_none_optional_fields(self):
        # Given
        data = {
            "summary": "Short summary",
            "key_points": [],
            "active_constraints": {},
        }
        # When
        summary = ContextSummary(**data)
        dumped = summary.model_dump(by_alias=True)
        # Then
        assert dumped["originalTurns"] is None
        assert dumped["summarizedAt"] is None


def _make_service():
    from app.services.conversation_context import ConversationContextService

    db_mock = MagicMock()
    service = ConversationContextService(db=db_mock, redis_client=None)
    service.logger = MagicMock()
    return service


class TestLogConstraintChanges:
    def test_logs_constraint_contradiction_when_budget_changes(self):
        # Given
        service = _make_service()
        old_ctx = {"constraints": {"budget_max": 50, "budget_min": 10}}
        new_ctx = {"constraints": {"budget_max": 100, "budget_min": 10}}
        # When
        service._log_constraint_changes(old_ctx, new_ctx, conversation_id=42)
        # Then
        service.logger.info.assert_called_once()
        call_args = service.logger.info.call_args
        assert call_args[0][0] == "Constraint contradiction detected"
        assert call_args[1]["constraint_key"] == "budget_max"
        assert call_args[1]["old_value"] == 50
        assert call_args[1]["new_value"] == 100
        assert call_args[1]["conversation_id"] == 42
        assert call_args[1]["resolution"] == "last_mentioned_wins"

    def test_logs_preference_change_when_color_changes(self):
        # Given
        service = _make_service()
        old_ctx = {"constraints": {"color": "red"}}
        new_ctx = {"constraints": {"color": "blue"}}
        # When
        service._log_constraint_changes(old_ctx, new_ctx, conversation_id=99)
        # Then
        service.logger.info.assert_called_once()
        call_args = service.logger.info.call_args
        assert call_args[0][0] == "Preference changed"
        assert call_args[1]["preference_key"] == "color"
        assert call_args[1]["old_value"] == "red"
        assert call_args[1]["new_value"] == "blue"
        assert call_args[1]["conversation_id"] == 99

    def test_does_not_log_when_values_are_same(self):
        # Given
        service = _make_service()
        old_ctx = {"constraints": {"budget_max": 100, "color": "red"}}
        new_ctx = {"constraints": {"budget_max": 100, "color": "red"}}
        # When
        service._log_constraint_changes(old_ctx, new_ctx, conversation_id=1)
        # Then
        service.logger.info.assert_not_called()

    def test_logs_multiple_constraint_changes_at_once(self):
        # Given
        service = _make_service()
        old_ctx = {
            "constraints": {"budget_max": 50, "budget_min": 10, "color": "red", "brand": "nike"}
        }
        new_ctx = {
            "constraints": {"budget_max": 100, "budget_min": 20, "color": "blue", "brand": "adidas"}
        }
        # When
        service._log_constraint_changes(old_ctx, new_ctx, conversation_id=7)
        # Then
        assert service.logger.info.call_count == 4
        messages = [call[0][0] for call in service.logger.info.call_args_list]
        assert messages.count("Constraint contradiction detected") == 2
        assert messages.count("Preference changed") == 2

    def test_handles_none_constraints_gracefully(self):
        # Given
        service = _make_service()
        old_ctx = {}
        new_ctx = {}
        # When
        service._log_constraint_changes(old_ctx, new_ctx, conversation_id=1)
        # Then
        service.logger.info.assert_not_called()

    def test_does_not_log_when_old_value_is_none(self):
        # Given
        service = _make_service()
        old_ctx = {"constraints": {}}
        new_ctx = {"constraints": {"budget_max": 100}}
        # When
        service._log_constraint_changes(old_ctx, new_ctx, conversation_id=1)
        # Then
        service.logger.info.assert_not_called()

    def test_does_not_log_when_new_value_is_none(self):
        # Given
        service = _make_service()
        old_ctx = {"constraints": {"budget_max": 100}}
        new_ctx = {"constraints": {}}
        # When
        service._log_constraint_changes(old_ctx, new_ctx, conversation_id=1)
        # Then
        service.logger.info.assert_not_called()


def _make_orm_model(**overrides):
    model = MagicMock()
    model.mode = overrides.get("mode", "ecommerce")
    model.turn_count = overrides.get("turn_count", 3)
    model.expires_at = overrides.get("expires_at", NOW)
    model.created_at = overrides.get("created_at", NOW)
    model.updated_at = overrides.get("updated_at", NOW)
    model.last_summarized_at = overrides.get("last_summarized_at", None)
    model.preferences = overrides.get("preferences", None)
    model.viewed_products = overrides.get("viewed_products", None)
    model.cart_items = overrides.get("cart_items", None)
    model.constraints = overrides.get("constraints", None)
    model.search_history = overrides.get("search_history", None)
    model.topics_discussed = overrides.get("topics_discussed", None)
    model.documents_referenced = overrides.get("documents_referenced", None)
    model.support_issues = overrides.get("support_issues", None)
    model.escalation_status = overrides.get("escalation_status", None)
    return model


class TestModelToDict:
    def test_converts_ecommerce_model_correctly(self):
        # Given
        service = _make_service()
        model = _make_orm_model(
            mode="ecommerce",
            turn_count=5,
            viewed_products=[1, 2],
            cart_items=[3],
            constraints={"budget_max": 100},
            search_history=["shoes"],
        )
        # When
        result = service._model_to_dict(model)
        # Then
        assert result["mode"] == "ecommerce"
        assert result["turn_count"] == 5
        assert result["viewed_products"] == [1, 2]
        assert result["cart_items"] == [3]
        assert result["constraints"] == {"budget_max": 100}
        assert result["search_history"] == ["shoes"]

    def test_converts_general_model_correctly(self):
        # Given
        service = _make_service()
        model = _make_orm_model(
            mode="general",
            topics_discussed=["login", "billing"],
            documents_referenced=[10, 20],
            support_issues=[{"issue": "password reset"}],
            escalation_status="pending",
        )
        # When
        result = service._model_to_dict(model)
        # Then
        assert result["mode"] == "general"
        assert result["topics_discussed"] == ["login", "billing"]
        assert result["documents_referenced"] == [10, 20]
        assert result["support_issues"] == [{"issue": "password reset"}]
        assert result["escalation_status"] == "pending"
        assert "viewed_products" not in result
        assert "cart_items" not in result

    def test_handles_none_optional_fields(self):
        # Given
        service = _make_service()
        model = _make_orm_model(
            mode="ecommerce",
            viewed_products=None,
            cart_items=None,
            constraints=None,
            search_history=None,
            preferences=None,
            last_summarized_at=None,
        )
        # When
        result = service._model_to_dict(model)
        # Then
        assert "viewed_products" not in result
        assert "cart_items" not in result
        assert "constraints" not in result
        assert "search_history" not in result
        assert result["preferences"] is None
        assert result["last_summarized_at"] is None

    def test_includes_timestamps_in_iso_format(self):
        # Given
        service = _make_service()
        ts = datetime(2026, 3, 31, 12, 0, 0, tzinfo=timezone.utc)
        model = _make_orm_model(expires_at=ts, created_at=ts, updated_at=ts)
        # When
        result = service._model_to_dict(model)
        # Then
        assert result["expires_at"] == ts.isoformat()
        assert result["created_at"] == ts.isoformat()
        assert result["updated_at"] == ts.isoformat()

    def test_handles_none_created_at_and_updated_at(self):
        # Given
        service = _make_service()
        model = _make_orm_model(created_at=None, updated_at=None)
        # When
        result = service._model_to_dict(model)
        # Then
        assert result["created_at"] is None
        assert result["updated_at"] is None
