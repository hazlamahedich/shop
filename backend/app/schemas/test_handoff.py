"""Unit tests for handoff schemas."""

from datetime import datetime

from app.schemas.handoff import (
    DEFAULT_HANDOFF_MESSAGE,
    HandoffDetectionRequest,
    HandoffReason,
    HandoffResponse,
    HandoffResult,
    HandoffStatus,
)


class TestHandoffStatus:
    """Tests for HandoffStatus enum."""

    def test_status_values(self):
        """Test all status values are defined."""
        assert HandoffStatus.NONE == "none"
        assert HandoffStatus.PENDING == "pending"
        assert HandoffStatus.ACTIVE == "active"
        assert HandoffStatus.RESOLVED == "resolved"

    def test_status_is_string_enum(self):
        """Test HandoffStatus is string enum."""
        assert isinstance(HandoffStatus.PENDING.value, str)


class TestHandoffReason:
    """Tests for HandoffReason enum."""

    def test_reason_values(self):
        """Test all reason values are defined."""
        assert HandoffReason.KEYWORD == "keyword"
        assert HandoffReason.LOW_CONFIDENCE == "low_confidence"
        assert HandoffReason.CLARIFICATION_LOOP == "clarification_loop"

    def test_reason_is_string_enum(self):
        """Test HandoffReason is string enum."""
        assert isinstance(HandoffReason.KEYWORD.value, str)


class TestHandoffResult:
    """Tests for HandoffResult schema."""

    def test_default_values(self):
        """Test default values are set correctly."""
        result = HandoffResult()
        assert result.should_handoff is False
        assert result.reason is None
        assert result.confidence_count == 0
        assert result.matched_keyword is None
        assert result.loop_count == 0

    def test_with_keyword_trigger(self):
        """Test HandoffResult with keyword trigger."""
        result = HandoffResult(
            should_handoff=True,
            reason=HandoffReason.KEYWORD,
            matched_keyword="human",
        )
        assert result.should_handoff is True
        assert result.reason == HandoffReason.KEYWORD
        assert result.matched_keyword == "human"

    def test_with_confidence_trigger(self):
        """Test HandoffResult with confidence trigger."""
        result = HandoffResult(
            should_handoff=True,
            reason=HandoffReason.LOW_CONFIDENCE,
            confidence_count=3,
        )
        assert result.should_handoff is True
        assert result.reason == HandoffReason.LOW_CONFIDENCE
        assert result.confidence_count == 3

    def test_with_loop_trigger(self):
        """Test HandoffResult with loop trigger."""
        result = HandoffResult(
            should_handoff=True,
            reason=HandoffReason.CLARIFICATION_LOOP,
            loop_count=3,
        )
        assert result.should_handoff is True
        assert result.reason == HandoffReason.CLARIFICATION_LOOP
        assert result.loop_count == 3

    def test_camel_case_alias(self):
        """Test camelCase aliases work for JSON serialization."""
        result = HandoffResult(should_handoff=True)
        data = result.model_dump(by_alias=True)
        assert "shouldHandoff" in data


class TestHandoffResponse:
    """Tests for HandoffResponse schema."""

    def test_default_values(self):
        """Test default values are set correctly."""
        response = HandoffResponse(conversation_id=1, handoff_status=HandoffStatus.PENDING)
        assert response.conversation_id == 1
        assert response.handoff_status == HandoffStatus.PENDING
        assert response.handoff_reason is None
        assert response.handoff_triggered_at is None
        assert response.message is None

    def test_with_all_fields(self):
        """Test HandoffResponse with all fields."""
        now = datetime.utcnow()
        response = HandoffResponse(
            conversation_id=1,
            handoff_status=HandoffStatus.PENDING,
            handoff_reason=HandoffReason.KEYWORD,
            handoff_triggered_at=now,
            message="Handoff triggered",
        )
        assert response.conversation_id == 1
        assert response.handoff_status == HandoffStatus.PENDING
        assert response.handoff_reason == HandoffReason.KEYWORD
        assert response.handoff_triggered_at == now
        assert response.message == "Handoff triggered"

    def test_camel_case_alias(self):
        """Test camelCase aliases work for JSON serialization."""
        response = HandoffResponse(
            conversation_id=1,
            handoff_status=HandoffStatus.PENDING,
        )
        data = response.model_dump(by_alias=True)
        assert "conversationId" in data
        assert "handoffStatus" in data


class TestHandoffDetectionRequest:
    """Tests for HandoffDetectionRequest schema."""

    def test_required_fields(self):
        """Test required fields are enforced."""
        request = HandoffDetectionRequest(message="test", conversation_id=1)
        assert request.message == "test"
        assert request.conversation_id == 1
        assert request.confidence_score is None
        assert request.clarification_type is None

    def test_with_all_fields(self):
        """Test HandoffDetectionRequest with all fields."""
        request = HandoffDetectionRequest(
            message="I want to buy shoes",
            conversation_id=123,
            confidence_score=0.45,
            clarification_type="budget",
        )
        assert request.message == "I want to buy shoes"
        assert request.conversation_id == 123
        assert request.confidence_score == 0.45
        assert request.clarification_type == "budget"

    def test_camel_case_alias(self):
        """Test camelCase aliases work for JSON serialization."""
        request = HandoffDetectionRequest(
            message="test",
            conversation_id=1,
            confidence_score=0.5,
        )
        data = request.model_dump(by_alias=True)
        assert "conversationId" in data
        assert "confidenceScore" in data


class TestDefaultHandoffMessage:
    """Tests for default handoff message constant."""

    def test_message_content(self):
        """Test default handoff message is defined."""
        assert "trouble understanding" in DEFAULT_HANDOFF_MESSAGE
        assert "12 hours" in DEFAULT_HANDOFF_MESSAGE

    def test_message_is_string(self):
        """Test default handoff message is a string."""
        assert isinstance(DEFAULT_HANDOFF_MESSAGE, str)
