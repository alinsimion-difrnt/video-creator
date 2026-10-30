"""Test-session setup.

Parallel workers (pytest-xdist, `-n auto`) each get their own numba cache: librosa compiles with
`cache=True`, and two workers writing the same cache files corrupted them (a segfault in librosa.pyin on the
next run). Set before anything imports numba.
"""

import os
import tempfile
from pathlib import Path

_worker = os.environ.get("PYTEST_XDIST_WORKER", "main")
os.environ.setdefault("NUMBA_CACHE_DIR", str(Path(tempfile.gettempdir()) / f"lens-numba-{_worker}"))
