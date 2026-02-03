#!/usr/bin/env python3
"""Validate test co-location for Python files.

Ensures every source file has a co-located test file following the pattern:
    module.py -> test_module.py

Usage:
    python scripts/validate_test_colocation.py
"""

import sys
from pathlib import Path


def validate_colocation(project_root: Path) -> bool:
    """Check each Python module has corresponding test file.

    Args:
        project_root: Root directory of the project

    Returns:
        True if all files have tests, False otherwise
    """
    backend = project_root / "backend" / "app"
    missing = []

    if not backend.exists():
        print("⚠️  Backend app directory not found, skipping test colocation check")
        return True

    for py_file in backend.rglob("*.py"):
        # Skip test files, __init__, and test directories
        if py_file.name.startswith("__init__") or py_file.name.startswith("test_"):
            continue
        if "tests" in py_file.parts or "__pycache__" in py_file.parts:
            continue

        # Check for co-located test file
        test_file = py_file.parent / f"test_{py_file.name}"
        if not test_file.exists():
            missing.append(test_file.relative_to(project_root))

    if missing:
        print("❌ Missing test files:")
        for f in sorted(missing):
            print(f"  - {f}")
        print("\n💡 Create test files alongside source files:")
        print("   Example: user_service.py → test_user_service.py")
        return False

    print("✅ All source files have co-located tests")
    return True


if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.exit(0 if validate_colocation(project_root) else 1)
