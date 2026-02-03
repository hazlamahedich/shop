"""OpenAPI schema generation script for pre-commit hook."""
import json
import sys
from pathlib import Path

current_dir = Path(__file__).parent
backend_dir = current_dir.parent.parent
sys.path.insert(0, str(backend_dir))


def generate_openapi() -> int:
    try:
        from app.main import app
        spec = app.openapi()
        output_path = backend_dir / "openapi.json"
        output_path.write_text(json.dumps(spec, indent=2))
        return 0
    except Exception as e:
        print(f"Could not import FastAPI app: {e}")
        return 0


if __name__ == "__main__":
    sys.exit(generate_openapi())
