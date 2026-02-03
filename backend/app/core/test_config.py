"""Tests for application configuration."""

import os

import pytest

from app.core.config import settings, is_testing, is_debug


class TestConfig:
    """Test application configuration."""

    def test_settings_returns_dict(self):
        """Test that settings returns a dictionary."""
        cfg = settings()
        assert isinstance(cfg, dict)

    def test_default_values(self):
        """Test default configuration values."""
        cfg = settings()

        # Application defaults
        assert cfg["APP_NAME"] == "shop-backend"
        assert cfg["API_PREFIX"] == "/api/v1"

        # Database defaults
        assert "shop_dev" in cfg["DATABASE_URL"]
        assert "postgresql" in cfg["DATABASE_URL"]

        # Redis defaults
        assert cfg["REDIS_URL"] == "redis://localhost:6379/0"

        # LLM defaults
        assert cfg["LLM_PROVIDER"] == "ollama"
        assert cfg["LLM_TEMPERATURE"] == 0.7
        assert cfg["LLM_MAX_TOKENS"] == 1000

    def test_is_testing_default(self):
        """Test default IS_TESTING value."""
        # Reset cache
        settings.cache_clear()

        # Ensure no environment variable
        os.environ.pop("IS_TESTING", None)

        assert is_testing() is False

    def test_is_testing_from_env(self, monkeypatch):
        """Test IS_TESTING from environment variable."""
        # Reset cache
        settings.cache_clear()

        monkeypatch.setenv("IS_TESTING", "true")
        assert is_testing() is True

        # Reset cache for next test
        settings.cache_clear()

        monkeypatch.setenv("IS_TESTING", "false")
        assert is_testing() is False

    def test_is_debug_default(self, monkeypatch):
        """Test default DEBUG value."""
        settings.cache_clear()
        monkeypatch.delenv("DEBUG", raising=False)

        assert is_debug() is False

    def test_is_debug_from_env(self, monkeypatch):
        """Test DEBUG from environment variable."""
        settings.cache_clear()
        monkeypatch.setenv("DEBUG", "true")

        assert is_debug() is True

    def test_settings_cached(self, monkeypatch):
        """Test that settings are cached."""
        settings.cache_clear()

        # First call
        cfg1 = settings()

        # Change environment
        monkeypatch.setenv("APP_NAME", "changed")

        # Second call should return cached value
        cfg2 = settings()

        assert cfg1["APP_NAME"] == cfg2["APP_NAME"]
        assert cfg2["APP_NAME"] != "changed"

    def test_cors_origins_parsing(self, monkeypatch):
        """Test CORS origins are parsed correctly."""
        settings.cache_clear()
        monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,https://example.com")

        cfg = settings()
        assert len(cfg["CORS_ORIGINS"]) == 3
        assert "http://localhost:3000" in cfg["CORS_ORIGINS"]
        assert "https://example.com" in cfg["CORS_ORIGINS"]

    def test_database_url_from_env(self, monkeypatch):
        """Test DATABASE_URL from environment."""
        settings.cache_clear()
        custom_url = "postgresql+asyncpg://user:pass@localhost:5432/custom"
        monkeypatch.setenv("DATABASE_URL", custom_url)

        cfg = settings()
        assert cfg["DATABASE_URL"] == custom_url
