"""Pytest configuration for contract tests.

Reuses database fixtures from parent conftest.
"""

import sys
from pathlib import Path

# Add parent directory to path to import conftest fixtures
sys.path.insert(0, str(Path(__file__).parent.parent))
