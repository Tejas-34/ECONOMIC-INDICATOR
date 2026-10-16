#!/usr/bin/env python3
"""Export FastAPI OpenAPI schema to JSON for frontend TypeScript type generation."""

import json
import sys
from pathlib import Path

# Ensure repo root is on sys.path
_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from backend.app.main import app


def export_openapi(output_path: Path | None = None) -> Path:
    target = output_path or (Path(__file__).resolve().parent.parent / "openapi.json")
    openapi_schema = app.openapi()
    with open(target, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2)
    print(f"[OpenAPI] Exported OpenAPI specification to {target}")
    return target


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    export_openapi(out)
