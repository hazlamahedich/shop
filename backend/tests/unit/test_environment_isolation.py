"""Environment isolation test — verifies IS_TESTING stays true throughout a test run.

Prevents regression of the load_dotenv(override=True) bug that caused 171+
cascading test failures in Story 11-2.

Action item from Epic 11 retrospective.
"""

from __future__ import annotations

import importlib
import os

import pytest


class TestEnvironmentIsolation:
    """Ensure test environment variables are never silently overwritten."""

    def test_is_testing_remains_true_after_config_import(self) -> None:
        """Re-importing config must not reset IS_TESTING to False."""
        os.environ["IS_TESTING"] = "true"

        from app.core.config import settings

        result = settings()
        assert result["IS_TESTING"] is True, (
            "IS_TESTING was reset to False after config import. "
            "Check load_dotenv() override setting in app/core/config.py."
        )

    def test_is_testing_survives_dotenv_load(self) -> None:
        """load_dotenv with override=False must not overwrite IS_TESTING."""
        os.environ["IS_TESTING"] = "true"

        from dotenv import load_dotenv
        from pathlib import Path

        env_file = Path(__file__).parent.parent.parent / ".env"
        if env_file.exists():
            load_dotenv(env_file, override=False)

        assert os.getenv("IS_TESTING", "false").lower() == "true", (
            "load_dotenv reset IS_TESTING. Ensure override=False is used."
        )

    def test_settings_cache_does_not_stale_is_testing(self) -> None:
        """Cached settings must reflect IS_TESTING=true in test environment."""
        os.environ["IS_TESTING"] = "true"

        from app.core.config import is_testing

        assert is_testing() is True

    def test_no_module_import_resets_is_testing(self) -> None:
        """Importing key service modules must not reset IS_TESTING."""
        os.environ["IS_TESTING"] = "true"

        modules_to_test = [
            "app.core.config",
            "app.services.conversation.unified_conversation_service",
            "app.services.intent.intent_classifier",
        ]

        for module_name in modules_to_test:
            importlib.import_module(module_name)
            assert os.getenv("IS_TESTING", "false").lower() == "true", (
                f"IS_TESTING was reset after importing {module_name}"
            )
