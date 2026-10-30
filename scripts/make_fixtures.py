"""Generate synthetic fixture videos into tests/fixtures/synth/ (gitignored media).

Usage: uv run python scripts/make_fixtures.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.fixtures.synth import ALL  # noqa: E402


def main() -> None:
    out = ROOT / "tests" / "fixtures" / "synth"
    out.mkdir(parents=True, exist_ok=True)
    for name, make in ALL.items():
        path = make(out / f"{name}.mp4")
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
