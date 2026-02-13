"""Test configuration for e-commerce provider tests.

Sprint Change 2026-02-13: Make Shopify Optional Integration

These tests run in isolation WITHOUT database dependencies.
The e-commerce providers (Null, Mock, Factory) are tested independently
of the database layer.
"""

import os
import sys
from pathlib import Path

# Prevent parent conftest from being loaded
# This ensures we don't inherit the session-scoped database fixture
# which causes pytest-asyncio scope mismatch errors
_collect_ignore = ["../../../conftest.py"]

# Set environment BEFORE any imports
os.environ["IS_TESTING"] = "false"
os.environ["MOCK_STORE_ENABLED"] = "false"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["DEBUG"] = "true"

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
