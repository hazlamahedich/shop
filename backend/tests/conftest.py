"""Pytest configuration and shared fixtures."""

import os
import sys
from pathlib import Path

import pytest


# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


# Set testing environment before any imports
os.environ["IS_TESTING"] = "true"


@pytest.fixture(autouse=True)
def set_testing_env(monkeypatch):
    """Ensure IS_TESTING is set for all tests."""
    monkeypatch.setenv("IS_TESTING", "true")
