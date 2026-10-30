"""One way to find and launch Chromium for the page checks (create audit, reel --check, reel --preview).

`CHROMIUM=<path>` wins; then a `chromium` on PATH; then the cloud image's /opt/pw-browsers/chromium; else
Playwright's own browser (`uv run --with playwright playwright install chromium` on a Mac).
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

CLOUD = "/opt/pw-browsers/chromium"
HINT = "needs playwright: uv run --with playwright create ... (and CHROMIUM=<path> if Chromium is elsewhere)"


def chromium_path() -> str | None:
    for p in (os.environ.get("CHROMIUM"), shutil.which("chromium"), CLOUD):
        if p and Path(p).is_file():
            return p
    return None


def available() -> bool:
    """Playwright is importable and a Chromium is known (tests skip cleanly otherwise)."""
    try:
        import playwright.sync_api  # noqa: F401
    except ImportError:
        return False
    return chromium_path() is not None


def launch(pw: Any) -> Any:
    """A headless Chromium from a running `sync_playwright()`."""
    exe = chromium_path()
    return pw.chromium.launch(**({"executable_path": exe} if exe else {}))
