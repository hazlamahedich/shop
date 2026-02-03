"""Tests for Message ORM model."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models.message import Message
from app.models.conversation import Conversation
from app.models.merchant import Merchant


class TestMessageModel:
    """Tests for Message ORM model."""

    @pytest.mark.asyncio
    async def test_create_message(self, db_session):
        """Test creating a message record."""
        # Create merchant
        merchant = Merchant(
            merchant_key="test_merchant_msg",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant)
        await db_session.flush()

        # Create conversation
        conversation = Conversation(
            merchant_id=merchant.id,
            platform="facebook",
            platform_sender_id="customer_id",
            status="active",
        )
        db_session.add(conversation)
        await db_session.flush()

        # Create message
        message = Message(
            conversation_id=conversation.id,
            sender="customer",
            content="Hello, I need help!",
            message_type="text",
        )
        db_session.add(message)
        await db_session.flush()

        # Verify message was created
        result = await db_session.execute(
            select(Message).where(Message.conversation_id == conversation.id)
        )
        found = result.scalars().first()

        assert found is not None
        assert found.sender == "customer"
        assert found.content == "Hello, I need help!"
        assert found.message_type == "text"

    @pytest.mark.asyncio
    async def test_message_defaults(self, db_session):
        """Test default values for message."""
        merchant = Merchant(
            merchant_key="test_merchant_msg2",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant)
        await db_session.flush()

        conversation = Conversation(
            merchant_id=merchant.id,
            platform="facebook",
            platform_sender_id="customer_id2",
        )
        db_session.add(conversation)
        await db_session.flush()

        message = Message(
            conversation_id=conversation.id,
            sender="bot",
            content="Hi! How can I help you?",
        )
        db_session.add(message)
        await db_session.flush()

        # Check defaults
        assert message.message_type == "text"
        assert message.message_metadata is None
        assert message.created_at is not None

    @pytest.mark.asyncio
    async def test_message_sender_enum(self, db_session):
        """Test that sender accepts valid enum values."""
        merchant = Merchant(
            merchant_key="test_merchant_sender",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant)
        await db_session.flush()

        conversation = Conversation(
            merchant_id=merchant.id,
            platform="facebook",
            platform_sender_id="customer_id3",
        )
        db_session.add(conversation)
        await db_session.flush()

        # Test both valid sender values
        for sender in ["customer", "bot"]:
            message = Message(
                conversation_id=conversation.id,
                sender=sender,
                content=f"Message from {sender}",
            )
            db_session.add(message)
            await db_session.flush()

            assert message.sender == sender

    @pytest.mark.asyncio
    async def test_message_type_enum(self, db_session):
        """Test that message_type accepts valid enum values."""
        merchant = Merchant(
            merchant_key="test_merchant_type",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant)
        await db_session.flush()

        conversation = Conversation(
            merchant_id=merchant.id,
            platform="facebook",
            platform_sender_id="customer_id4",
        )
        db_session.add(conversation)
        await db_session.flush()

        # Test each valid message type
        for msg_type in ["text", "attachment", "postback"]:
            message = Message(
                conversation_id=conversation.id,
                sender="customer",
                content=f"Message of type {msg_type}",
                message_type=msg_type,
            )
            db_session.add(message)
            await db_session.flush()

            assert message.message_type == msg_type

    @pytest.mark.asyncio
    async def test_message_with_metadata(self, db_session):
        """Test message with metadata field."""
        merchant = Merchant(
            merchant_key="test_merchant_meta",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant)
        await db_session.flush()

        conversation = Conversation(
            merchant_id=merchant.id,
            platform="facebook",
            platform_sender_id="customer_id5",
        )
        db_session.add(conversation)
        await db_session.flush()

        # Create message with metadata
        metadata = {
            "attachment_url": "https://example.com/image.jpg",
            "attachment_type": "image",
        }
        message = Message(
            conversation_id=conversation.id,
            sender="customer",
            content="Here's an image",
            message_type="attachment",
            message_metadata=metadata,
        )
        db_session.add(message)
        await db_session.flush()

        await db_session.refresh(message)
        assert message.message_metadata == metadata
        assert message.message_metadata["attachment_url"] == "https://example.com/image.jpg"

    @pytest.mark.asyncio
    async def test_messages_in_conversation(self, db_session):
        """Test retrieving all messages in a conversation."""
        merchant = Merchant(
            merchant_key="test_merchant_thread",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant)
        await db_session.flush()

        conversation = Conversation(
            merchant_id=merchant.id,
            platform="facebook",
            platform_sender_id="customer_thread",
        )
        db_session.add(conversation)
        await db_session.flush()

        # Create multiple messages
        messages_data = [
            ("customer", "Hello"),
            ("bot", "Hi there!"),
            ("customer", "I need help"),
            ("bot", "Sure, what do you need?"),
        ]

        for sender, content in messages_data:
            message = Message(
                conversation_id=conversation.id,
                sender=sender,
                content=content,
            )
            db_session.add(message)
        await db_session.flush()

        # Retrieve all messages
        result = await db_session.execute(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.created_at)
        )
        messages = result.scalars().all()

        assert len(messages) == len(messages_data)
        for i, message in enumerate(messages):
            assert message.sender == messages_data[i][0]
            assert message.content == messages_data[i][1]

    @pytest.mark.asyncio
    async def test_delete_cascade_conversation_to_messages(self, db_session):
        """Test that deleting conversation cascades to messages."""
        merchant = Merchant(
            merchant_key="test_merchant_del_cascade",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant)
        await db_session.flush()

        conversation = Conversation(
            merchant_id=merchant.id,
            platform="facebook",
            platform_sender_id="customer_del",
        )
        db_session.add(conversation)
        await db_session.flush()

        message = Message(
            conversation_id=conversation.id,
            sender="customer",
            content="Test message",
        )
        db_session.add(message)
        await db_session.flush()

        message_id = message.id

        # Delete conversation (should cascade to messages)
        await db_session.delete(conversation)
        await db_session.flush()

        # Verify message is also deleted
        result = await db_session.execute(
            select(Message).where(Message.id == message_id)
        )
        found = result.scalars().first()
        assert found is None
