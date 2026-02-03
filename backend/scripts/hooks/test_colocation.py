"""Test colocation validation script for pre-commit hook."""
import sys
from pathlib import Path


def validate_colocation() -> int:
    backend_dir = Path(__file__).parent.parent.parent
    app_dir = backend_dir / "app"
    
    if not app_dir.exists():
        return 0
    
    missing = []
    for py_file in app_dir.rglob("*.py"):
        if py_file.name.startswith("__init__") or py_file.name.startswith("test_"):
            continue
        if "tests" in py_file.parts or "__pycache__" in py_file.parts:
            continue
        test_file = py_file.parent / f"test_{py_file.name}"
        if not test_file.exists():
            missing.append(str(test_file.relative_to(backend_dir)))
    
    if missing:
        print("Missing test files:")
        for f in sorted(missing):
            print(f"  - {f}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(validate_colocation())
