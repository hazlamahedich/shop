"""Pytest configuration for service-level tests."""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import the make_cost_records fixture from tests/conftest
# This makes it available to all tests in this directory
pytest_plugins = ["tests.conftest"]
