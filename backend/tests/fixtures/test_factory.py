"""Tests for test data factories."""

import pytest

from tests.fixtures.factory import (
    UserFactory,
    ProductFactory,
    CartFactory,
    OrderFactory,
    ConversationFactory,
    MessageFactory,
    SequenceFactory,
    random_string,
    random_email,
    random_phone,
)


class TestUserFactory:
    """Test User factory."""

    def test_create_user_with_defaults(self):
        """Test creating user with default values."""
        factory = UserFactory()
        user = factory.to_dict()

        assert "id" in user
        assert "@" in user["email"]
        assert user["name"] == "Test User"
        assert user["is_active"] is True
        assert "created_at" in user

    def test_create_user_with_custom_values(self):
        """Test creating user with custom values."""
        factory = UserFactory(
            email="custom@example.com",
            name="Custom User",
            is_active=False
        )
        user = factory.to_dict()

        assert user["email"] == "custom@example.com"
        assert user["name"] == "Custom User"
        assert user["is_active"] is False


class TestProductFactory:
    """Test Product factory."""

    def test_create_product_with_defaults(self):
        """Test creating product with default values."""
        factory = ProductFactory()
        product = factory.to_dict()

        assert "id" in product
        assert product["title"] is not None
        assert product["price"] > 0
        assert product["currency"] == "USD"
        assert product["available"] is True
        assert product["inventory"] > 0

    def test_create_product_with_custom_values(self):
        """Test creating product with custom values."""
        factory = ProductFactory(
            title="Custom Shoe",
            price=99.99,
            category="footwear"
        )
        product = factory.to_dict()

        assert product["title"] == "Custom Shoe"
        assert product["price"] == 99.99
        assert product["category"] == "footwear"


class TestCartFactory:
    """Test Cart factory."""

    def test_create_cart_with_defaults(self):
        """Test creating cart with default values."""
        factory = CartFactory()
        cart = factory.to_dict()

        assert "id" in cart
        assert "session_id" in cart
        assert cart["items"] == []
        assert "created_at" in cart
        assert "expires_at" in cart

    def test_create_cart_with_items(self):
        """Test creating cart with items."""
        factory = CartFactory(
            items=[
                {"product_id": "123", "quantity": 2},
                {"product_id": "456", "quantity": 1}
            ]
        )
        cart = factory.to_dict()

        assert len(cart["items"]) == 2


class TestOrderFactory:
    """Test Order factory."""

    def test_create_order_with_defaults(self):
        """Test creating order with default values."""
        factory = OrderFactory()
        order = factory.to_dict()

        assert "id" in order
        assert "cart_id" in order
        assert "checkout_url" in order
        assert order["status"] == "pending"
        assert "created_at" in order


class TestConversationFactory:
    """Test Conversation factory."""

    def test_create_conversation_with_defaults(self):
        """Test creating conversation with default values."""
        factory = ConversationFactory()
        conv = factory.to_dict()

        assert "id" in conv
        assert "platform_customer_id" in conv
        assert conv["platform"] == "messenger"
        assert conv["status"] == "active"
        assert conv["messages"] == []


class TestMessageFactory:
    """Test Message factory."""

    def test_create_message_with_defaults(self):
        """Test creating message with default values."""
        factory = MessageFactory()
        message = factory.to_dict()

        assert "id" in message
        assert "conversation_id" in message
        assert message["content"] is not None
        assert message["sender"] == "user"
        assert message["direction"] == "inbound"


class TestSequenceFactory:
    """Test sequence factory for sequential data."""

    def test_sequence_starts_at_zero(self):
        """Test that sequence starts at zero."""
        factory = SequenceFactory()
        assert factory.counter == 0

    def test_next_increments_counter(self):
        """Test that next() increments counter."""
        factory = SequenceFactory()
        assert factory.next() == 1
        assert factory.next() == 2
        assert factory.next() == 3

    def test_email_generates_sequential_emails(self):
        """Test email generation is sequential."""
        factory = SequenceFactory()
        email1 = factory.email()
        email2 = factory.email()

        assert "user1@" in email1
        assert "user2@" in email2

    def test_reset_clears_counter(self):
        """Test that reset clears counter."""
        factory = SequenceFactory()
        factory.next()
        factory.next()
        assert factory.counter == 2

        factory.reset()
        assert factory.counter == 0


class TestUtilityFunctions:
    """Test utility functions."""

    def test_random_string_generates_string(self):
        """Test random string generation."""
        s = random_string(10)
        assert len(s) == 10
        assert s.isalnum()

    def test_random_string_different_each_time(self):
        """Test random strings are different."""
        s1 = random_string(20)
        s2 = random_string(20)
        assert s1 != s2

    def test_random_email_format(self):
        """Test random email has correct format."""
        email = random_email()
        assert "@" in email
        assert email.endswith("@example.com")

    def test_random_phone_format(self):
        """Test random phone has correct format."""
        phone = random_phone()
        assert phone.startswith("+1")
        assert len(phone) == 12  # +1 + 10 digits
