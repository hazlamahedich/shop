"""Tests for E-Commerce Provider Factory.

Sprint Change 2026-02-13: Make Shopify Optional Integration

Tests the factory functions for getting the appropriate e-commerce provider
based on merchant configuration and environment settings.

Note: These tests do NOT use database fixtures - they test the provider factory
in isolation without database dependencies.
"""

import os
import pytest
from unittest.mock import MagicMock

# Set environment variables BEFORE importing the module
os.environ["IS_TESTING"] = "false"
os.environ["MOCK_STORE_ENABLED"] = "false"

from app.services.ecommerce.provider_factory import (
    StoreProvider,
    get_provider,
    get_provider_for_merchant,
    get_null_provider,
    get_mock_provider,
    has_store_connected,
    get_store_provider_type,
)
from app.services.ecommerce.null_provider import NullStoreProvider
from app.services.ecommerce.mock_provider import MockStoreProvider


# Mark all tests in this file as not needing database
pytestmark = pytest.mark.skipif(
    False,  # Never skip, but don't use async fixtures
    reason="These tests don't need database"
)


class TestStoreProviderEnum:
    """Tests for StoreProvider enum."""

    def test_store_provider_values(self):
        """Test that StoreProvider has expected values."""
        assert StoreProvider.NONE.value == "none"
        assert StoreProvider.SHOPIFY.value == "shopify"
        assert StoreProvider.WOOCOMMERCE.value == "woocommerce"
        assert StoreProvider.BIGCOMMERCE.value == "bigcommerce"
        assert StoreProvider.MOCK.value == "mock"

    def test_store_provider_from_string(self):
        """Test creating StoreProvider from string."""
        assert StoreProvider("none") == StoreProvider.NONE
        assert StoreProvider("shopify") == StoreProvider.SHOPIFY


class TestGetNullProvider:
    """Tests for get_null_provider function."""

    def test_returns_null_store_provider(self):
        """Test that get_null_provider returns NullStoreProvider."""
        provider = get_null_provider()
        assert isinstance(provider, NullStoreProvider)

    def test_returns_singleton(self):
        """Test that get_null_provider returns the same instance."""
        provider1 = get_null_provider()
        provider2 = get_null_provider()
        assert provider1 is provider2

    def test_provider_name_is_none(self):
        """Test that null provider has provider_name 'none'."""
        provider = get_null_provider()
        assert provider.provider_name == "none"

    def test_is_connected_returns_false(self):
        """Test that null provider is_connected returns False."""
        provider = get_null_provider()
        assert provider.is_connected() is False


class TestGetMockProvider:
    """Tests for get_mock_provider function."""

    def test_returns_mock_store_provider(self):
        """Test that get_mock_provider returns MockStoreProvider."""
        provider = get_mock_provider()
        assert isinstance(provider, MockStoreProvider)

    def test_returns_singleton(self):
        """Test that get_mock_provider returns the same instance."""
        provider1 = get_mock_provider()
        provider2 = get_mock_provider()
        assert provider1 is provider2


class TestGetProvider:
    """Tests for get_provider function."""

    def test_get_provider_returns_null_for_none(self):
        """Test get_provider returns NullStoreProvider for NONE type."""
        provider = get_provider(StoreProvider.NONE)
        assert isinstance(provider, NullStoreProvider)

    def test_get_provider_returns_mock_for_mock(self):
        """Test get_provider returns MockStoreProvider for MOCK type."""
        provider = get_provider(StoreProvider.MOCK)
        assert isinstance(provider, MockStoreProvider)

    def test_get_provider_returns_null_for_unsupported(self):
        """Test get_provider returns NullStoreProvider for unsupported types."""
        # WooCommerce and BigCommerce are not yet implemented
        provider = get_provider(StoreProvider.WOOCOMMERCE)
        assert isinstance(provider, NullStoreProvider)


class TestGetProviderForMerchant:
    """Tests for get_provider_for_merchant function."""

    def test_returns_mock_in_testing_mode(self, monkeypatch):
        """Test that testing mode returns MockStoreProvider."""
        monkeypatch.setenv("IS_TESTING", "true")
        monkeypatch.setenv("MOCK_STORE_ENABLED", "false")

        # Re-import to pick up new env
        import importlib
        import app.services.ecommerce.provider_factory as pf
        importlib.reload(pf)

        provider = pf.get_provider_for_merchant(None)
        assert isinstance(provider, MockStoreProvider)

    def test_returns_mock_when_mock_store_enabled(self, monkeypatch):
        """Test that MOCK_STORE_ENABLED returns MockStoreProvider."""
        monkeypatch.setenv("IS_TESTING", "false")
        monkeypatch.setenv("MOCK_STORE_ENABLED", "true")

        # Re-import to pick up new env
        import importlib
        import app.services.ecommerce.provider_factory as pf
        importlib.reload(pf)

        provider = pf.get_provider_for_merchant(None)
        assert isinstance(provider, MockStoreProvider)

    def test_returns_null_for_no_merchant(self, monkeypatch):
        """Test that None merchant returns NullStoreProvider."""
        monkeypatch.setenv("IS_TESTING", "false")
        monkeypatch.setenv("MOCK_STORE_ENABLED", "false")

        # Re-import to pick up new env
        import importlib
        import app.services.ecommerce.provider_factory as pf
        importlib.reload(pf)

        provider = pf.get_provider_for_merchant(None)
        assert isinstance(provider, NullStoreProvider)

    def test_returns_null_for_merchant_with_none_provider(self, monkeypatch):
        """Test that merchant with store_provider='none' returns NullStoreProvider."""
        monkeypatch.setenv("IS_TESTING", "false")
        monkeypatch.setenv("MOCK_STORE_ENABLED", "false")

        # Re-import to pick up new env
        import importlib
        import app.services.ecommerce.provider_factory as pf
        importlib.reload(pf)

        mock_merchant = MagicMock()
        mock_merchant.store_provider = "none"
        mock_merchant.config = {}

        provider = pf.get_provider_for_merchant(mock_merchant)
        assert isinstance(provider, NullStoreProvider)


class TestHasStoreConnected:
    """Tests for has_store_connected helper function."""

    def test_returns_false_for_null_provider(self):
        """Test has_store_connected returns False for null provider."""
        original_testing = os.environ.get("IS_TESTING")
        original_mock = os.environ.get("MOCK_STORE_ENABLED")
        os.environ["IS_TESTING"] = "false"
        os.environ["MOCK_STORE_ENABLED"] = "false"

        try:
            mock_merchant = MagicMock()
            mock_merchant.store_provider = "none"
            mock_merchant.config = {}

            result = has_store_connected(mock_merchant)
            assert result is False
        finally:
            if original_testing is None:
                os.environ.pop("IS_TESTING", None)
            else:
                os.environ["IS_TESTING"] = original_testing
            if original_mock is None:
                os.environ.pop("MOCK_STORE_ENABLED", None)
            else:
                os.environ["MOCK_STORE_ENABLED"] = original_mock

    def test_returns_true_for_mock_provider(self):
        """Test has_store_connected returns True for mock provider."""
        original = os.environ.get("IS_TESTING")
        os.environ["IS_TESTING"] = "true"

        try:
            result = has_store_connected(None)
            assert result is True
        finally:
            if original is None:
                os.environ.pop("IS_TESTING", None)
            else:
                os.environ["IS_TESTING"] = original


class TestGetStoreProviderType:
    """Tests for get_store_provider_type helper function."""

    def test_returns_none_for_null_provider(self):
        """Test get_store_provider_type returns 'none' for null provider."""
        original_testing = os.environ.get("IS_TESTING")
        original_mock = os.environ.get("MOCK_STORE_ENABLED")
        os.environ["IS_TESTING"] = "false"
        os.environ["MOCK_STORE_ENABLED"] = "false"

        try:
            mock_merchant = MagicMock()
            mock_merchant.store_provider = "none"
            mock_merchant.config = {}

            result = get_store_provider_type(mock_merchant)
            assert result == "none"
        finally:
            if original_testing is None:
                os.environ.pop("IS_TESTING", None)
            else:
                os.environ["IS_TESTING"] = original_testing
            if original_mock is None:
                os.environ.pop("MOCK_STORE_ENABLED", None)
            else:
                os.environ["MOCK_STORE_ENABLED"] = original_mock

    def test_returns_mock_for_testing_mode(self):
        """Test get_store_provider_type returns 'mock' in testing mode."""
        original = os.environ.get("IS_TESTING")
        os.environ["IS_TESTING"] = "true"

        try:
            result = get_store_provider_type(None)
            assert result == "mock"
        finally:
            if original is None:
                os.environ.pop("IS_TESTING", None)
            else:
                os.environ["IS_TESTING"] = original
