"""Render bundle: scene files plus local copies of GSAP and the fonts, so renders need no CDN.

data/create/<project>/bundle/
  assets/gsap.min.js     from the npm tarball of gsap@<GSAP_VERSION> (GSAP licence: external-facts §9)
  assets/fonts.css       @font-face rules pointing at assets/fonts/*.woff2
  assets/fonts/*.woff2   the Google Fonts files for the tokens' families (OFL 1.1)
  <scene>/index.html     one HyperFrames project per scene, for snapshots and previews
  <scene>/assets         a link to ../assets (HyperFrames wants root-relative asset paths)
Downloads are cached in data/create/_cache/ and reused.
"""

from __future__ import annotations

import io
import json
import re
import shutil
import tarfile
import urllib.request
from pathlib import Path

from create.build import ASSETS, GSAP_VERSION
from create.tokens import UA
from lens.schemas.create import Tokens

NPM = "https://registry.npmjs.org/gsap/-/gsap-{v}.tgz"


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return bytes(resp.read())


def gsap(cache: Path) -> Path:
    out = cache / f"gsap-{GSAP_VERSION}.min.js"
    if not out.exists():
        with tarfile.open(fileobj=io.BytesIO(_get(NPM.format(v=GSAP_VERSION)))) as tar:
            member = tar.extractfile("package/dist/gsap.min.js")
            if member is None:
                raise RuntimeError("gsap.min.js missing from the npm package")
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(member.read())
    return out


def fonts(cache: Path, css_url: str) -> tuple[str, list[Path]]:
    """The Google Fonts CSS rewritten to local files (latin subsets plus the extra glyph ranges)."""
    css = _get(css_url).decode()
    files: list[Path] = []

    def local(m: re.Match[str]) -> str:
        url = m.group(1)
        name = re.sub(r"[^a-z0-9.]+", "-", url.split("/s/")[-1].lower())
        path = cache / "fonts" / name
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(_get(url))
        files.append(path)
        return f"url(fonts/{name})"

    return re.sub(r"url\((https://[^)]+)\)", local, css), files


def run_bundle(root: Path, project: str) -> Path:
    base = root / "projects" / project
    tokens = Tokens.model_validate(json.loads((base / "tokens.json").read_text()))
    cache = root / "data" / "create" / "_cache"
    out = root / "data" / "create" / project / "bundle"
    assets = out / ASSETS
    (assets / "fonts").mkdir(parents=True, exist_ok=True)
    shutil.copy(gsap(cache), assets / "gsap.min.js")
    css, files = fonts(cache, tokens.fonts_css)
    for f in files:
        shutil.copy(f, assets / "fonts" / f.name)
    (assets / "fonts.css").write_text(css)
    for scene in sorted((base / "scenes").glob("*.html")):
        d = out / scene.stem
        d.mkdir(exist_ok=True)
        (d / "index.html").write_text(scene.read_text())
        link = d / ASSETS  # HyperFrames resolves assets against each project root: link the shared folder in
        if not link.exists():
            link.symlink_to(Path("..") / ASSETS, target_is_directory=True)
    return out
