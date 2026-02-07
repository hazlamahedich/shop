"""Tests for ConversationService.

Tests conversation listing, pagination, sorting, and merchant isolation.
"""

from datetime import datetime
import pytest

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.merchant import Merchant
from app.services.conversation import ConversationService


@pytest.mark.asyncio
class TestConversationService:
    """Test ConversationService conversation listing functionality."""

    async def test_get_conversations_empty_result(self, async_session):
        """Test getting conversations when merchant has none."""
        # Create a test merchant
        merchant = Merchant(
            merchant_key="test-shop-conversation",
            platform="facebook",
            status="active",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        service = ConversationService()

        conversations, total = await service.get_conversations(
            db=async_session,
            merchant_id=merchant.id,
            page=1,
            per_page=20,
        )

        assert conversations == []
        assert total == 0

    async def test_get_conversations_with_messages(self, async_session):
        """Test getting conversations with last message preview."""
        # Create test merchant
        merchant = Merchant(
            merchant_key="test-shop-conversation",
            platform="facebook",
            status="active",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        # Create conversation
        conversation = Conversation(
            merchant_id=merchant.id,
            platform="facebook",
            platform_sender_id="test_customer_123",
            status="active",
        )
        async_session.add(conversation)
        await async_session.commit()
        await async_session.refresh(conversation)

        # Create messages
        message1 = Message(
            conversation_id=conversation.id,
            sender="customer",
            content="I'm looking for running shoes under $100.",
            message_type="text",
        )
        message2 = Message(
            conversation_id=conversation.id,
            sender="bot",
            content="I found some great options for you!",
            message_type="text",
        )
        async_session.add(message1)
        async_session.add(message2)
        await async_session.commit()

        service = ConversationService()

        conversations, total = await service.get_conversations(
            db=async_session,
            merchant_id=merchant.id,
            page=1,
            per_page=20,
        )

        assert total == 1
        assert len(conversations) == 1
        assert conversations[0]["id"] == conversation.id
        assert conversations[0]["message_count"] == 2
        # Last message should be the most recent one (bot message)
        assert conversations[0]["last_message"] == "I found some great options for you!"
        assert conversations[0]["platform_sender_id_masked"] == "test****"

    async def test_get_conversations_pagination(self, async_session):
        """Test conversation pagination with multiple conversations."""
        # Create test merchant
        merchant = Merchant(
            merchant_key="test-shop-conversation",
            platform="facebook",
            status="active",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        # Create 25 conversations with messages
        for i in range(25):
            conversation = Conversation(
                merchant_id=merchant.id,
                platform="facebook",
                platform_sender_id=f"customer_{i:03d}",
                status="active",
            )
            async_session.add(conversation)
            await async_session.flush()

            message = Message(
                conversation_id=conversation.id,
                sender="customer",
                content=f"Message {i}",
                message_type="text",
            )
            async_session.add(message)

        await async_session.commit()

        service = ConversationService()

        # Page 1: 20 conversations
        convs_1, total = await service.get_conversations(
            db=async_session,
            merchant_id=merchant.id,
            page=1,
            per_page=20,
        )
        assert len(convs_1) == 20
        assert total == 25

        # Page 2: 5 conversations
        convs_2, total = await service.get_conversations(
            db=async_session,
            merchant_id=merchant.id,
            page=2,
            per_page=20,
        )
        assert len(convs_2) == 5
        assert total == 25

    async def test_get_conversations_sorting_by_updated_at_desc(self, async_session):
        """Test sorting by updated_at descending (default)."""
        # Create test merchant
        merchant = Merchant(
            merchant_key="test-shop-conversation",
            platform="facebook",
            status="active",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        # Create conversations with different timestamps
        # Use naive datetimes to match model's datetime.utcnow() default
        timestamps = [
            datetime(2026, 2, 7, 10, 0, 0),
            datetime(2026, 2, 7, 9, 0, 0),
            datetime(2026, 2, 7, 11, 0, 0),
        ]

        for i, ts in enumerate(timestamps):
            conversation = Conversation(
                merchant_id=merchant.id,
                platform="facebook",
                platform_sender_id=f"customer_{i}",
                status="active",
                updated_at=ts,
            )
            async_session.add(conversation)
        await async_session.commit()

        service = ConversationService()

        # Default: updated_at desc should show most recent first
        conversations, total = await service.get_conversations(
            db=async_session,
            merchant_id=merchant.id,
            page=1,
            per_page=20,
            sort_by="updated_at",
            sort_order="desc",
        )

        assert len(conversations) == 3
        assert total == 3
        # Most recent first
        assert conversations[0]["updated_at"] == timestamps[2]
        assert conversations[1]["updated_at"] == timestamps[0]
        assert conversations[2]["updated_at"] == timestamps[1]

    async def test_get_conversations_sorting_by_status_asc(self, async_session):
        """Test sorting by status ascending."""
        # Create test merchant
        merchant = Merchant(
            merchant_key="test-shop-conversation",
            platform="facebook",
            status="active",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        # Create conversations with different statuses
        statuses = ["active", "closed", "handoff"]
        conversations = []

        for status in statuses:
            conv = Conversation(
                merchant_id=merchant.id,
                platform="facebook",
                platform_sender_id=f"customer_{status}",
                status=status,
            )
            async_session.add(conv)
            conversations.append(conv)

        await async_session.commit()

        service = ConversationService()

        # Sort by status asc
        result, total = await service.get_conversations(
            db=async_session,
            merchant_id=merchant.id,
            page=1,
            per_page=20,
            sort_by="status",
            sort_order="asc",
        )

        assert len(result) == 3
        assert total == 3
        # Ascending order by enum definition order: active, handoff, closed
        assert result[0]["status"] == "active"
        assert result[1]["status"] == "handoff"
        assert result[2]["status"] == "closed"

    async def test_get_conversations_invalid_sort_column(self, async_session):
        """Test that invalid sort column defaults to updated_at."""
        # Create test merchant
        merchant = Merchant(
            merchant_key="test-shop-conversation",
            platform="facebook",
            status="active",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        service = ConversationService()

        # Use an invalid sort column - should default to updated_at
        conversations, total = await service.get_conversations(
            db=async_session,
            merchant_id=merchant.id,
            page=1,
            per_page=20,
            sort_by="invalid_column",  # Invalid
            sort_order="desc",
        )

        # Should return results without error (defaults to updated_at)
        assert isinstance(conversations, list)

    async def test_get_conversations_masks_sender_id(self, async_session):
        """Test that platform_sender_id is masked in response."""
        # Create test merchant
        merchant = Merchant(
            merchant_key="test-shop-conversation",
            platform="facebook",
            status="active",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        conversation = Conversation(
            merchant_id=merchant.id,
            platform="facebook",
            platform_sender_id="12345678901234567890",
            status="active",
        )
        async_session.add(conversation)
        await async_session.commit()

        service = ConversationService()

        conversations, total = await service.get_conversations(
            db=async_session,
            merchant_id=merchant.id,
            page=1,
            per_page=20,
        )

        assert len(conversations) == 1
        # Should be masked: first 4 chars + asterisks
        assert conversations[0]["platform_sender_id_masked"] == "1234****"
        assert conversations[0]["platform_sender_id"] == "12345678901234567890"

    async def test_get_conversations_message_count(self, async_session):
        """Test that message count is included."""
        # Create test merchant
        merchant = Merchant(
            merchant_key="test-shop-conversation",
            platform="facebook",
            status="active",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        # Create conversation with varying number of messages
        message_counts = [1, 5, 10]

        for count in message_counts:
            conversation = Conversation(
                merchant_id=merchant.id,
                platform="facebook",
                platform_sender_id=f"customer_{count}",
                status="active",
            )
            async_session.add(conversation)
            await async_session.flush()

            # Add messages
            for i in range(count):
                message = Message(
                    conversation_id=conversation.id,
                    sender="customer",
                    content=f"Message {i}",
                    message_type="text",
                )
                async_session.add(message)
        await async_session.commit()

        service = ConversationService()

        conversations, total = await service.get_conversations(
            db=async_session,
            merchant_id=merchant.id,
            page=1,
            per_page=20,
        )

        assert total == 3
        # Check that message counts are correct (order may vary)
        message_counts_result = {conv["message_count"] for conv in conversations}
        assert message_counts_result == {1, 5, 10}

    async def test_get_conversations_sentiment_placeholder(self, async_session):
        """Test that sentiment is included as placeholder (mock)."""
        # Create test merchant
        merchant = Merchant(
            merchant_key="test-shop-conversation",
            platform="facebook",
            status="active",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        conversation = Conversation(
            merchant_id=merchant.id,
            platform="facebook",
            platform_sender_id="test_customer",
            status="active",
        )
        async_session.add(conversation)
        await async_session.commit()

        service = ConversationService()

        conversations, total = await service.get_conversations(
            db=async_session,
            merchant_id=merchant.id,
            page=1,
            per_page=20,
        )

        assert len(conversations) == 1
        # Sentiment is mocked as "neutral" for now
        assert conversations[0]["sentiment"] == "neutral"

    async def test_merchant_isolation(self, async_session):
        """Test merchants can only see their own conversations."""
        # Create two merchants
        merchant_a = Merchant(
            merchant_key="test-shop-a",
            platform="facebook",
            status="active",
        )
        merchant_b = Merchant(
            merchant_key="test-shop-b",
            platform="facebook",
            status="active",
        )
        async_session.add(merchant_a)
        async_session.add(merchant_b)
        await async_session.commit()
        await async_session.refresh(merchant_a)
        await async_session.refresh(merchant_b)

        # Create conversation for merchant A
        conv_a = Conversation(
            merchant_id=merchant_a.id,
            platform="facebook",
            platform_sender_id="customer_a",
            status="active",
        )
        async_session.add(conv_a)

        # Create conversation for merchant B
        conv_b = Conversation(
            merchant_id=merchant_b.id,
            platform="facebook",
            platform_sender_id="customer_b",
            status="active",
        )
        async_session.add(conv_b)
        await async_session.commit()

        service = ConversationService()

        # Merchant A sees only their conversation
        convs_a, total_a = await service.get_conversations(
            db=async_session,
            merchant_id=merchant_a.id,
            page=1,
            per_page=20,
        )
        assert len(convs_a) == 1
        assert convs_a[0]["id"] == conv_a.id
        assert total_a == 1

        # Merchant B sees only their conversation
        convs_b, total_b = await service.get_conversations(
            db=async_session,
            merchant_id=merchant_b.id,
            page=1,
            per_page=20,
        )
        assert len(convs_b) == 1
        assert convs_b[0]["id"] == conv_b.id
        assert total_b == 1

    async def test_get_conversations_empty_page_beyond_data(self, async_session):
        """Test pagination beyond available data returns empty list."""
        # Create test merchant
        merchant = Merchant(
            merchant_key="test-shop-conversation",
            platform="facebook",
            status="active",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        # Create only 5 conversations
        for i in range(5):
            conversation = Conversation(
                merchant_id=merchant.id,
                platform="facebook",
                platform_sender_id=f"customer_{i}",
                status="active",
            )
            async_session.add(conversation)
        await async_session.commit()

        service = ConversationService()

        # Request page 2 (beyond available data)
        conversations, total = await service.get_conversations(
            db=async_session,
            merchant_id=merchant.id,
            page=2,
            per_page=20,
        )

        assert conversations == []
        assert total == 5

    async def test_get_conversations_per_page_limits(self, async_session):
        """Test per_page parameter limits results correctly."""
        # Create test merchant
        merchant = Merchant(
            merchant_key="test-shop-conversation",
            platform="facebook",
            status="active",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        # Create 50 conversations
        for i in range(50):
            conversation = Conversation(
                merchant_id=merchant.id,
                platform="facebook",
                platform_sender_id=f"customer_{i}",
                status="active",
            )
            async_session.add(conversation)
        await async_session.commit()

        service = ConversationService()

        # Request only 10 per page
        conversations, total = await service.get_conversations(
            db=async_session,
            merchant_id=merchant.id,
            page=1,
            per_page=10,
        )

        assert len(conversations) == 10
        assert total == 50

    async def test_get_conversations_last_message_content_decrypted(self, async_session):
        """Test that last message content is decrypted (not encrypted)."""
        # Create test merchant
        merchant = Merchant(
            merchant_key="test-shop-conversation",
            platform="facebook",
            status="active",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        conversation = Conversation(
            merchant_id=merchant.id,
            platform="facebook",
            platform_sender_id="test_customer",
            status="active",
        )
        async_session.add(conversation)
        await async_session.commit()
        await async_session.refresh(conversation)

        # Create a customer message - content will be stored encrypted
        message = Message(
            conversation_id=conversation.id,
            sender="customer",
            content="Customer wants red shoes",  # Will be encrypted
            message_type="text",
        )
        # Use set_encrypted_content to encrypt the message
        message.set_encrypted_content("Customer wants red shoes")
        async_session.add(message)
        await async_session.commit()

        service = ConversationService()

        conversations, total = await service.get_conversations(
            db=async_session,
            merchant_id=merchant.id,
            page=1,
            per_page=20,
        )

        assert len(conversations) == 1
        # Last message should be decrypted
        assert "Customer wants red shoes" in conversations[0]["last_message"] or conversations[0]["last_message"] == "Customer wants red shoes"

    async def test_get_conversations_multiple_messages_shows_latest(self, async_session):
        """Test that conversations with multiple messages show the most recent one."""
        # Create test merchant
        merchant = Merchant(
            merchant_key="test-shop-conversation",
            platform="facebook",
            status="active",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        conversation = Conversation(
            merchant_id=merchant.id,
            platform="facebook",
            platform_sender_id="test_customer",
            status="active",
        )
        async_session.add(conversation)
        await async_session.commit()
        await async_session.refresh(conversation)

        # Create multiple messages with different timestamps
        from datetime import timedelta

        base_time = datetime(2026, 2, 7, 10, 0, 0)

        message1 = Message(
            conversation_id=conversation.id,
            sender="customer",
            content="First message",
            message_type="text",
            created_at=base_time,
        )
        message1.set_encrypted_content("First message")

        message2 = Message(
            conversation_id=conversation.id,
            sender="bot",
            content="Second message (latest)",
            message_type="text",
            created_at=base_time + timedelta(minutes=1),
        )

        message3 = Message(
            conversation_id=conversation.id,
            sender="customer",
            content="Third message (even later)",
            message_type="text",
            created_at=base_time + timedelta(minutes=2),
        )
        message3.set_encrypted_content("Third message (even later)")

        async_session.add(message1)
        async_session.add(message2)
        async_session.add(message3)
        await async_session.commit()

        service = ConversationService()

        conversations, total = await service.get_conversations(
            db=async_session,
            merchant_id=merchant.id,
            page=1,
            per_page=20,
        )

        assert len(conversations) == 1
        # The latest message (message3) should be shown
        assert "Third message (even later)" in conversations[0]["last_message"] or conversations[0]["last_message"] == "Third message (even later)"
