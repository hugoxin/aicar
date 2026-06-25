"""Result export placeholders."""

import json
from pathlib import Path
from typing import Any


def export_result(result: dict[str, Any], output_path: str | Path) -> None:
    """Write a future-compatible JSON result."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

