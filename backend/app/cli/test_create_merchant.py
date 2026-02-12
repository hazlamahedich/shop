"""Unit tests for create_merchant CLI command.

Tests cover:
- Email validation
- Password validation
- Interactive mode prompts
- Non-interactive mode
- Merchant creation
- Error handling
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.cli.create_merchant import (
    validate_email,
    prompt_email,
    prompt_password,
    create_merchant,
)
from app.models.merchant import Merchant


@pytest.fixture
async def db_session():
    """Create a mock database session for testing."""
    # Create a mock session
    session = MagicMock(spec=AsyncSession)

    # Mock the scalars().first() chain
    mock_scalars = Mock()
    mock_scalars.first.return_value = None  # No existing merchant by default

    mock_result = Mock()
    mock_result.scalars.return_value = mock_scalars

    session.execute.return_value = mock_result

    # Mock add, commit, refresh
    session.add = Mock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()

    # Mock rollback for error cases
    session.rollback = AsyncMock()

    return session


class TestEmailValidation:
    """Tests for email validation."""

    def test_valid_email_passes(self):
        """Valid email should pass validation."""
        assert validate_email("test@example.com") is True
        assert validate_email("user.name@domain.co.uk") is True

    def test_invalid_email_fails(self):
        """Invalid email should fail validation."""
        assert validate_email("not-an-email") is False
        assert validate_email("missing@tld") is False
        assert validate_email("@missing-local.com") is False
        assert validate_email("no-at-sign.com") is False
        assert validate_email("") is False


class TestPromptEmail:
    """Tests for email prompt."""

    def test_prompt_email_returns_valid_email(self):
        """Should return valid email after prompting."""
        with patch("typer.prompt", return_value="test@example.com"):
            result = prompt_email()
            assert result == "test@example.com"

    def test_prompt_email_retries_invalid(self):
        """Should retry on invalid email."""
        with patch("typer.prompt", side_effect=["invalid", "test@example.com"]):
            with patch("typer.echo"):
                result = prompt_email()
                assert result == "test@example.com"


class TestPromptPassword:
    """Tests for password prompt."""

    def test_prompt_password_returns_valid(self):
        """Should return valid password after confirmation."""
        with patch("typer.prompt", side_effect=["SecurePass123", "SecurePass123"]):
            result = prompt_password()
            assert result == "SecurePass123"

    def test_prompt_password_mismatch_retries(self):
        """Should retry on password mismatch."""
        with patch(
            "typer.prompt",
            side_effect=["SecurePass123", "WrongPass", "SecurePass123", "SecurePass123"],
        ):
            with patch("typer.echo"):
                result = prompt_password()
                assert result == "SecurePass123"

    def test_prompt_password_invalid_retries(self):
        """Should retry on invalid password."""
        with patch(
            "typer.prompt",
            side_effect=["short", "SecurePass123", "SecurePass123"],
        ):
            with patch("typer.echo"):
                result = prompt_password()
                assert result == "SecurePass123"


class TestCreateMerchant:
    """Tests for merchant creation."""

    @pytest.mark.asyncio
    async def test_create_merchant_success(self, db_session):
        """Should create merchant with hashed password."""
        # Create a mock async context manager
        mock_session_manager = AsyncMock()
        mock_session_manager.__aenter__.return_value = db_session
        mock_session_manager.__aexit__.return_value = None

        with patch("app.cli.create_merchant.async_session", return_value=mock_session_manager):
            merchant = await create_merchant("test@example.com", "SecurePass123")

            assert merchant.email == "test@example.com"
            assert merchant.password_hash is not None
            assert merchant.merchant_key is not None
            assert merchant.platform == "shopify"
            assert merchant.status == "active"

    @pytest.mark.asyncio
    async def test_create_merchant_duplicate_email_raises_error(self, db_session):
        """Should raise error for duplicate email."""
        from app.core.auth import hash_password

        # Create existing merchant mock
        existing_merchant = Merchant(
            id=1,
            merchant_key="existing-merchant",
            platform="shopify",
            status="active",
            email="test@example.com",
            password_hash=hash_password("SecurePass123"),
        )

        # Update the mock to return existing merchant
        mock_scalars = Mock()
        mock_scalars.first.return_value = existing_merchant

        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars

        db_session.execute.return_value = mock_result

        # Create a mock async context manager
        mock_session_manager = AsyncMock()
        mock_session_manager.__aenter__.return_value = db_session
        mock_session_manager.__aexit__.return_value = None

        with patch("app.cli.create_merchant.async_session", return_value=mock_session_manager):
            with pytest.raises(ValueError, match="already exists"):
                await create_merchant("test@example.com", "SecurePass123")

    @pytest.mark.asyncio
    async def test_create_merchant_weak_password_raises_error(self):
        """Should raise error for weak password."""
        with pytest.raises(ValueError, match="Password requirements"):
            await create_merchant("test@example.com", "short")

    @pytest.mark.asyncio
    async def test_create_merchant_generates_merchant_key(self, db_session):
        """Should generate unique merchant key."""
        # Create a mock async context manager
        mock_session_manager = AsyncMock()
        mock_session_manager.__aenter__.return_value = db_session
        mock_session_manager.__aexit__.return_value = None

        with patch("app.cli.create_merchant.async_session", return_value=mock_session_manager):
            merchant = await create_merchant("test1@example.com", "SecurePass123")

            assert merchant.merchant_key is not None
            assert len(merchant.merchant_key) == 12
            assert merchant.merchant_key.isalnum()

    @pytest.mark.asyncio
    async def test_create_merchant_default_values(self, db_session):
        """Should set default platform and status."""
        # Create a mock async context manager
        mock_session_manager = AsyncMock()
        mock_session_manager.__aenter__.return_value = db_session
        mock_session_manager.__aexit__.return_value = None

        with patch("app.cli.create_merchant.async_session", return_value=mock_session_manager):
            merchant = await create_merchant("test@example.com", "SecurePass123")

            assert merchant.platform == "shopify"
            assert merchant.status == "active"

    @pytest.mark.asyncio
    async def test_create_merchant_hashes_password(self, db_session):
        """Should hash password before storing."""
        from app.core.auth import hash_password

        # Create a mock async context manager
        mock_session_manager = AsyncMock()
        mock_session_manager.__aenter__.return_value = db_session
        mock_session_manager.__aexit__.return_value = None

        password = "SecurePass123"
        with patch("app.cli.create_merchant.async_session", return_value=mock_session_manager):
            merchant = await create_merchant("test@example.com", password)

            # Password should be hashed, not stored in plain text
            assert merchant.password_hash != password
            assert merchant.password_hash.startswith("$2b$")  # bcrypt prefix
            assert len(merchant.password_hash) == 60  # bcrypt hash length
