"""Locate the repository and load `config/lens.yaml`."""

from __future__ import annotations

import os
from pathlib import Path

import yaml

from lens.schemas.config import LensConfig

_MARKER = Path("config") / "lens.yaml"


def find_repo_root(start: Path | None = None) -> Path:
    """`LENS_ROOT`, else the nearest ancestor of the cwd holding config/lens.yaml, else the source tree.

    The image installs `lens` under /app while the repo checkout is mounted elsewhere, so the
    package location alone is not enough.
    """
    env = os.environ.get("LENS_ROOT")
    if env:
        return Path(env).resolve()
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / _MARKER).is_file():
            return candidate
    return Path(__file__).resolve().parent.parent


REPO_ROOT = find_repo_root()
DEFAULT_CONFIG = REPO_ROOT / _MARKER


def load_config(path: Path = DEFAULT_CONFIG) -> LensConfig:
    with path.open(encoding="utf-8") as fh:
        return LensConfig.model_validate(yaml.safe_load(fh))
