"""Export JSON Schemas to exports/schemas/ (consumed by the Create phase)."""

from __future__ import annotations

import json
from pathlib import Path

from lens.schemas import SCHEMAS


def render_all() -> dict[str, str]:
    out: dict[str, str] = {}
    for name, model in SCHEMAS.items():
        schema = model.model_json_schema()
        out[f"{name}.schema.json"] = json.dumps(schema, indent=2, sort_keys=True) + "\n"
    return out


def export(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for filename, text in render_all().items():
        path = out_dir / filename
        path.write_text(text, encoding="utf-8")
        written.append(path)
    return written


def stale(out_dir: Path) -> list[str]:
    """File names whose committed schema differs from the code (or is missing)."""
    problems = []
    for filename, text in render_all().items():
        path = out_dir / filename
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            problems.append(filename)
    return problems
