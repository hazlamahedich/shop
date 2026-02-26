"""Tests for ConversationConsentService.

Story 6-1: Opt-In Consent Flow

Tests for conversation consent with PostgreSQL persistence.
"""

from __future__ import annotations
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.consent.extended_consent_service import ConversationConsentService
from app.models.consent import Consent, ConsentType, ConsentSource
from app.schemas.consent import ConsentStatus


@pytest.fixture
def mock_redis() -> redis.Redis:
    """Create mock Redis client for testing."""
    return AsyncMock(spec=redis.Redis)


@pytest.fixture
def mock_db() -> AsyncMock:
    """Create mock database session."""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    return mock_session


@pytest.fixture
def service(mock_redis: redis.Redis, mock_db: AsyncMock) -> ConversationConsentService:
    """Create service instance with mocked dependencies."""
    return ConversationConsentService(redis_client=mock_redis, db=mock_db)


class TestGetConsentForConversation:
    """Tests for get_consent_for_conversation method."""

    @pytest.mark.asyncio
    async def test_returns_none_when_db_is_none(self, mock_redis: redis.Redis) -> None:
        """Test returns None when no database session provided."""
        service = ConversationConsentService(redis_client=mock_redis, db=None)
        result = await service.get_consent_for_conversation("session_1", 1)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_consent_when_found(
        self, service: ConversationConsentService, mock_db: AsyncMock
    ) -> None:
        """Test returns consent record when found in database."""
        existing_consent = Consent(
            session_id="session_1",
            merchant_id=1,
            consent_type=ConsentType.CONVERSATION,
        )
        existing_consent.granted = True

        mock_result = MagicMock()
        mock_result.scalars().first.return_value = existing_consent
        mock_db.execute.return_value = mock_result

        result = await service.get_consent_for_conversation("session_1", 1)

        assert result == existing_consent
        assert result.granted is True

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(
        self, service: ConversationConsentService, mock_db: AsyncMock
    ) -> None:
        """Test returns None when consent not found."""
        mock_result = MagicMock()
        mock_result.scalars().first.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.get_consent_for_conversation("session_1", 1)

        assert result is None


class TestGetOrCreateConsent:
    """Tests for get_or_create_consent method."""

    @pytest.mark.asyncio
    async def test_raises_when_db_is_none(self, mock_redis: redis.Redis) -> None:
        """Test raises ValueError when no database session."""
        service = ConversationConsentService(redis_client=mock_redis, db=None)

        with pytest.raises(ValueError, match="Database session required"):
            await service.get_or_create_consent("session_1", 1)

    @pytest.mark.asyncio
    async def test_creates_new_consent_when_not_found(
        self, service: ConversationConsentService, mock_db: AsyncMock
    ) -> None:
        """Test creates new consent when not found."""
        mock_result = MagicMock()
        mock_result.scalars().first.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.get_or_create_consent("session_1", 1)

        assert result.session_id == "session_1"
        assert result.merchant_id == 1
        assert result.consent_type == ConsentType.CONVERSATION
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_existing_consent_when_found(
        self, service: ConversationConsentService, mock_db: AsyncMock
    ) -> None:
        """Test returns existing consent when found."""
        existing_consent = Consent(
            session_id="session_1",
            merchant_id=1,
            consent_type=ConsentType.CONVERSATION,
        )

        mock_result = MagicMock()
        mock_result.scalars().first.return_value = existing_consent
        mock_db.execute.return_value = mock_result

        result = await service.get_or_create_consent("session_1", 1)

        assert result == existing_consent
        mock_db.add.assert_not_called()


class TestRecordConversationConsent:
    """Tests for record_conversation_consent method."""

    @pytest.mark.asyncio
    async def test_raises_when_db_is_none(self, mock_redis: redis.Redis) -> None:
        """Test raises ValueError when no database session."""
        service = ConversationConsentService(redis_client=mock_redis, db=None)

        with pytest.raises(ValueError, match="Database session required"):
            await service.record_conversation_consent("session_1", 1, consent_granted=True)

    @pytest.mark.asyncio
    async def test_records_opt_in(
        self, service: ConversationConsentService, mock_db: AsyncMock
    ) -> None:
        """Test recording opt-in consent."""
        mock_result = MagicMock()
        mock_result.scalars().first.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.record_conversation_consent(
            session_id="session_1",
            merchant_id=1,
            consent_granted=True,
            source=ConsentSource.WIDGET.value,
        )

        assert result["status"] == ConsentStatus.OPTED_IN
        assert result["source"] == ConsentSource.WIDGET.value
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_records_opt_out(
        self, service: ConversationConsentService, mock_db: AsyncMock
    ) -> None:
        """Test recording opt-out consent."""
        mock_result = MagicMock()
        mock_result.scalars().first.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.record_conversation_consent(
            session_id="session_1",
            merchant_id=1,
            consent_granted=False,
            source=ConsentSource.MESSENGER.value,
        )

        assert result["status"] == ConsentStatus.OPTED_OUT
        mock_db.commit.assert_called()


class TestShouldPromptForConsent:
    """Tests for should_prompt_for_consent method."""

    @pytest.mark.asyncio
    async def test_returns_true_when_db_is_none(self, mock_redis: redis.Redis) -> None:
        """Test returns True when no database session (prompt by default)."""
        service = ConversationConsentService(redis_client=mock_redis, db=None)
        result = await service.should_prompt_for_consent("session_1", 1)
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_true_when_message_not_shown(
        self, service: ConversationConsentService, mock_db: AsyncMock
    ) -> None:
        """Test returns True when consent message not yet shown."""
        existing_consent = Consent(
            session_id="session_1",
            merchant_id=1,
            consent_type=ConsentType.CONVERSATION,
        )
        existing_consent.consent_message_shown = False

        mock_result = MagicMock()
        mock_result.scalars().first.return_value = existing_consent
        mock_db.execute.return_value = mock_result

        result = await service.should_prompt_for_consent("session_1", 1)

        assert result is True
        assert existing_consent.consent_message_shown is True
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_false_when_message_already_shown(
        self, service: ConversationConsentService, mock_db: AsyncMock
    ) -> None:
        """Test returns False when consent message already shown."""
        existing_consent = Consent(
            session_id="session_1",
            merchant_id=1,
            consent_type=ConsentType.CONVERSATION,
        )
        existing_consent.consent_message_shown = True

        mock_result = MagicMock()
        mock_result.scalars().first.return_value = existing_consent
        mock_db.execute.return_value = mock_result

        result = await service.should_prompt_for_consent("session_1", 1)

        assert result is False


class TestHandleForgetPreferences:
    """Tests for handle_forget_preferences method."""

    @pytest.mark.asyncio
    async def test_returns_pending_when_db_is_none(self, mock_redis: redis.Redis) -> None:
        """Test returns PENDING status when no database session."""
        service = ConversationConsentService(redis_client=mock_redis, db=None)
        result = await service.handle_forget_preferences("session_1", 1)

        assert result["status"] == ConsentStatus.PENDING
        assert "No database connection" in result["message"]

    @pytest.mark.asyncio
    async def test_revokes_existing_consent(
        self, service: ConversationConsentService, mock_db: AsyncMock
    ) -> None:
        """Test revokes consent when it exists."""
        existing_consent = Consent(
            session_id="session_1",
            merchant_id=1,
            consent_type=ConsentType.CONVERSATION,
        )
        existing_consent.grant()
        existing_consent.consent_message_shown = True

        mock_result = MagicMock()
        mock_result.scalars().first.return_value = existing_consent
        mock_db.execute.return_value = mock_result

        result = await service.handle_forget_preferences("session_1", 1)
        assert result["status"] == ConsentStatus.PENDING
        assert "deleted" in result["message"].lower()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_pending_when_no_consent(
        self, service: ConversationConsentService, mock_db: AsyncMock
    ) -> None:
        """Test returns PENDING when no consent exists."""
        mock_result = MagicMock()
        mock_result.scalars().first.return_value = None
        mock_db.execute.return_value = mock_result
        result = await service.handle_forget_preferences("session_1", 1)
        assert result["status"] == ConsentStatus.PENDING
        assert "deleted" in result["message"].lower()


class TestDeleteVoluntaryData:
    """Tests for delete_voluntary_data method (Story 6-2)."""

    @pytest.mark.asyncio
    async def test_raises_when_db_is_none(self, mock_redis: redis.Redis) -> None:
        """Test raises APIError when no database session."""
        from app.core.errors import APIError

        service = ConversationConsentService(redis_client=mock_redis, db=None)

        with pytest.raises(APIError, match="Database connection required"):
            await service.delete_voluntary_data("session_1", 1)

    @pytest.mark.asyncio
    async def test_rate_limit_blocks_rapid_requests(
        self, service: ConversationConsentService, mock_db: AsyncMock, mock_redis: redis.Redis
    ) -> None:
        """Test rate limiting blocks rapid deletion requests."""
        from app.core.errors import APIError

        mock_redis.exists = AsyncMock(return_value=1)

        with pytest.raises(APIError, match="Rate limit exceeded"):
            await service.delete_voluntary_data("session_1", 1)

    @pytest.mark.asyncio
    async def test_concurrent_deletion_blocked_by_lock(
        self, service: ConversationConsentService, mock_db: AsyncMock, mock_redis: redis.Redis
    ) -> None:
        """Test concurrent deletion blocked by Redis lock."""
        from app.core.errors import APIError

        mock_redis.exists = AsyncMock(return_value=0)
        mock_redis.set = AsyncMock(return_value=False)

        with pytest.raises(APIError, match="Deletion already in progress"):
            await service.delete_voluntary_data("session_1", 1)

    @pytest.mark.asyncio
    async def test_deletes_conversations_and_messages(
        self, service: ConversationConsentService, mock_db: AsyncMock, mock_redis: redis.Redis
    ) -> None:
        """Test deletion of conversations and messages."""
        mock_redis.exists = AsyncMock(return_value=0)
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.delete = AsyncMock(return_value=1)
        mock_redis.setex = AsyncMock()

        mock_conv_result = MagicMock()
        mock_conv_result.all.return_value = [(1,), (2,)]
        mock_msg_result = MagicMock()
        mock_msg_result.rowcount = 5
        mock_conv_delete_result = MagicMock()
        mock_conv_delete_result.rowcount = 2

        mock_db.execute = AsyncMock(
            side_effect=[
                mock_conv_result,
                mock_msg_result,
                mock_conv_delete_result,
            ]
        )
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()

        result = await service.delete_voluntary_data("session_1", 1)

        assert result["status"] == "success"
        assert result["conversations_deleted"] == 2
        assert result["messages_deleted"] == 5
        assert "audit_log_id" in result

    @pytest.mark.asyncio
    async def test_clears_redis_cart_data(
        self, service: ConversationConsentService, mock_db: AsyncMock, mock_redis: redis.Redis
    ) -> None:
        """Test Redis cart and preferences data is cleared."""
        mock_redis.exists = AsyncMock(return_value=0)
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.delete = AsyncMock(return_value=1)
        mock_redis.setex = AsyncMock()

        mock_conv_result = MagicMock()
        mock_conv_result.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_conv_result)
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()

        result = await service.delete_voluntary_data("session_1", 1)

        assert result["status"] == "success"
        assert mock_redis.delete.call_count >= 1

    @pytest.mark.asyncio
    async def test_handles_redis_failure_gracefully(
        self, service: ConversationConsentService, mock_db: AsyncMock, mock_redis: redis.Redis
    ) -> None:
        """Test Redis failures are handled gracefully and logged."""
        mock_redis.exists = AsyncMock(return_value=0)
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.delete = AsyncMock(side_effect=Exception("Redis connection error"))
        mock_redis.setex = AsyncMock()

        mock_conv_result = MagicMock()
        mock_conv_result.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_conv_result)
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()

        result = await service.delete_voluntary_data("session_1", 1)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_cross_platform_deletion_by_visitor_id(
        self, service: ConversationConsentService, mock_db: AsyncMock, mock_redis: redis.Redis
    ) -> None:
        """Test cross-platform deletion when visitor_id provided."""
        mock_redis.exists = AsyncMock(return_value=0)
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.delete = AsyncMock(return_value=1)
        mock_redis.setex = AsyncMock()

        mock_sessions_result = MagicMock()
        mock_sessions_result.all.return_value = [("session_1", "widget"), ("psid_2", "messenger")]

        mock_conv_result = MagicMock()
        mock_conv_result.all.return_value = [(1,)]

        mock_msg_result = MagicMock()
        mock_msg_result.rowcount = 3

        mock_conv_delete_result = MagicMock()
        mock_conv_delete_result.rowcount = 1

        mock_db.execute = AsyncMock(
            side_effect=[
                mock_sessions_result,
                mock_conv_result,
                mock_msg_result,
                mock_conv_delete_result,
                mock_conv_result,
                mock_msg_result,
                mock_conv_delete_result,
            ]
        )
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()

        result = await service.delete_voluntary_data("session_1", 1, visitor_id="visitor_123")

        assert result["status"] == "success"


class TestHandleForgetPreferencesWithDeletion:
    """Tests for handle_forget_preferences_with_deletion method (Story 6-2)."""

    @pytest.mark.asyncio
    async def test_calls_delete_voluntary_data(
        self, service: ConversationConsentService, mock_db: AsyncMock, mock_redis: redis.Redis
    ) -> None:
        """Test that actual deletion is performed."""
        mock_redis.exists = AsyncMock(return_value=0)
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.delete = AsyncMock(return_value=1)
        mock_redis.setex = AsyncMock()

        mock_conv_result = MagicMock()
        mock_conv_result.all.return_value = []
        mock_consent_result = MagicMock()
        mock_consent_result.scalars().first.return_value = None

        mock_db.execute = AsyncMock(side_effect=[mock_conv_result, mock_consent_result])
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()

        result = await service.handle_forget_preferences_with_deletion("session_1", 1)

        assert result["status"] == ConsentStatus.PENDING
        assert result["clear_visitor_id"] is True
        assert "deletion_summary" in result

    @pytest.mark.asyncio
    async def test_returns_deletion_summary(
        self, service: ConversationConsentService, mock_db: AsyncMock, mock_redis: redis.Redis
    ) -> None:
        """Test that deletion summary is returned."""
        mock_redis.exists = AsyncMock(return_value=0)
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.delete = AsyncMock(return_value=1)
        mock_redis.setex = AsyncMock()

        mock_conv_result = MagicMock()
        mock_conv_result.all.return_value = [(1,)]
        mock_msg_result = MagicMock()
        mock_msg_result.rowcount = 5
        mock_conv_delete_result = MagicMock()
        mock_conv_delete_result.rowcount = 1
        mock_consent_result = MagicMock()
        mock_consent_result.scalars().first.return_value = None

        mock_db.execute = AsyncMock(
            side_effect=[
                mock_conv_result,
                mock_msg_result,
                mock_conv_delete_result,
                mock_consent_result,
            ]
        )
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()

        result = await service.handle_forget_preferences_with_deletion("session_1", 1)

        assert result["deletion_summary"]["conversations_deleted"] == 1
        assert result["deletion_summary"]["messages_deleted"] == 5
