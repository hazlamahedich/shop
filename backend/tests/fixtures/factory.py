"""Test data factories for creating test entities.

Uses factory pattern for generating test data with sensible defaults.
"""

from __future__ import annotations

import random
import string
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4


@dataclass
class UserFactory:
    """Factory for creating test user data."""

    id: str = field(default_factory=lambda: str(uuid4()))
    email: str = field(default_factory=lambda: f"user_{uuid4()}@example.com")
    name: str = "Test User"
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class ProductFactory:
    """Factory for creating test product data."""

    id: str = field(default_factory=lambda: f"shopify_{uuid4().hex[:12]}")
    title: str = field(default_factory=lambda: f"Test Product {random.randint(1, 1000)}")
    description: str = "A test product for development"
    price: float = field(default_factory=lambda: round(random.uniform(10, 500), 2))
    currency: str = "USD"
    available: bool = True
    inventory: int = field(default_factory=lambda: random.randint(1, 100))
    category: str = "test-category"
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "price": self.price,
            "currency": self.currency,
            "available": self.available,
            "inventory": self.inventory,
            "category": self.category,
            "tags": self.tags,
        }


@dataclass
class CartFactory:
    """Factory for creating test cart data."""

    id: str = field(default_factory=lambda: str(uuid4()))
    session_id: str = field(default_factory=lambda: str(uuid4()))
    items: list[dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(hours=24))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "items": self.items,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
        }


@dataclass
class OrderFactory:
    """Factory for creating test order data."""

    id: str = field(default_factory=lambda: f"order_{uuid4().hex[:12]}")
    cart_id: str = field(default_factory=lambda: str(uuid4()))
    checkout_url: str = field(default_factory=lambda: f"https://checkout.example.com/{uuid4().hex}")
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "cart_id": self.cart_id,
            "checkout_url": self.checkout_url,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class ConversationFactory:
    """Factory for creating test conversation data."""

    id: str = field(default_factory=lambda: str(uuid4()))
    platform_customer_id: str = field(default_factory=lambda: str(uuid4()))
    platform: str = "messenger"
    status: str = "active"
    messages: list[dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "platform_customer_id": self.platform_customer_id,
            "platform": self.platform,
            "status": self.status,
            "messages": self.messages,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class MessageFactory:
    """Factory for creating test message data."""

    id: str = field(default_factory=lambda: str(uuid4()))
    conversation_id: str = field(default_factory=lambda: str(uuid4()))
    content: str = field(default_factory=lambda: f"Test message {random.randint(1, 100)}")
    sender: str = "user"  # user, bot, human_agent
    direction: str = "inbound"  # inbound, outbound
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "content": self.content,
            "sender": self.sender,
            "direction": self.direction,
            "created_at": self.created_at.isoformat(),
        }


class SequenceFactory:
    """Factory for generating sequential test data."""

    def __init__(self) -> None:
        self.counter = 0

    def next(self) -> int:
        """Get next value in sequence."""
        self.counter += 1
        return self.counter

    def email(self) -> str:
        """Generate sequential email."""
        self.counter += 1
        return f"user{self.counter}@example.com"

    def reset(self) -> None:
        """Reset counter."""
        self.counter = 0


def random_string(length: int = 10) -> str:
    """Generate random string for testing."""
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def random_email() -> str:
    """Generate random email address."""
    return f"{random_string(8)}@example.com"


def random_phone() -> str:
    """Generate random phone number (US format)."""
    return f"+1{random.randint(200, 999)}{random.randint(200, 999)}{random.randint(1000, 9999)}"
