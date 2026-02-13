"""Test configuration for e-commerce abstraction layer tests.

Provides fixtures and configuration for testing the e-commerce providers
without requiring database connections.
"""

import os
import pytest


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables.

    This fixture enables mock store for all tests in this module.
    """
    # Enable mock store for testing
    os.environ["IS_TESTING"] = "true"
    os.environ["MOCK_STORE_ENABLED"] = "true"

    yield

    # Cleanup
    os.environ.pop("IS_TESTING", None)
    os.environ.pop("MOCK_STORE_ENABLED", None)
