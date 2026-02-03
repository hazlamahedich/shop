#!/usr/bin/env python3
"""Generate TypeScript types from Pydantic schemas.

This script:
1. Exports OpenAPI schema from FastAPI application
2. Converts to TypeScript using openapi-typescript
3. Outputs to frontend/src/lib/types/generated.ts

Usage:
    python scripts/generate_types.py

Requirements:
    - FastAPI app must be running or importable
    - openapi-typescript installed globally or in node_modules
"""

import json
import subprocess
import sys
from pathlib import Path


def generate_openapi_spec(output_path: Path) -> bool:
    """Generate OpenAPI specification from FastAPI.

    Args:
        output_path: Path to write the OpenAPI JSON spec

    Returns:
        True if successful, False otherwise
    """
    try:
        script_dir = Path(__file__).parent
        backend_dir = script_dir.parent / "backend"

        # Add backend to path
        sys.path.insert(0, str(backend_dir))

        # Try importing the app
        try:
            from app.main import app
        except ImportError:
            print("⚠️  FastAPI app not found, skipping OpenAPI generation")
            return True

        # Generate spec
        spec = app.openapi()

        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(spec, indent=2))

        print(f"✅ Generated OpenAPI spec: {output_path}")
        return True

    except Exception as e:
        print(f"❌ Error generating OpenAPI spec: {e}")
        return False


def generate_typescript_types(openapi_path: Path, output_path: Path) -> bool:
    """Generate TypeScript types from OpenAPI spec.

    Args:
        openapi_path: Path to OpenAPI JSON spec
        output_path: Path to write TypeScript types

    Returns:
        True if successful, False otherwise
    """
    try:
        # Use npx to run openapi-typescript without installing globally
        # This works in CI/CD and local environments
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["npx", "openapi-typescript", str(openapi_path), "-o", str(output_path)],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"❌ Error generating TypeScript types: {result.stderr}")
            return False

        print(f"✅ Generated TypeScript types: {output_path}")
        return True

    except Exception as e:
        print(f"❌ Error generating TypeScript types: {e}")
        return False


def main() -> int:
    """Generate OpenAPI spec and TypeScript types."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    backend_dir = project_root / "backend"
    openapi_path = backend_dir / "openapi.json"
    typescript_output = project_root / "frontend" / "src" / "lib" / "types" / "generated.ts"

    # Generate OpenAPI spec
    if not generate_openapi_spec(openapi_path):
        print("\n❌ OpenAPI generation failed")
        return 1

    # Generate TypeScript types
    if not generate_typescript_types(openapi_path, typescript_output):
        print("\n❌ TypeScript type generation failed")
        return 1

    print("\n✅ Type generation complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
