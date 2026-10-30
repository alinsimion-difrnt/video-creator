"""create take (skill process-take, ADR 0035): a presenter take from the chat to the cut page in one call.

A provisional brief (acme unless --brand; the language detected from the take) when the project has
none, the take at footage/raw/01-take<ext>, then F1 ingest, F2 transcript, C3 tokens (if none), F3 cuts and
the phone page, each the same as its own command. It prints what he says as plain text, so the brief is
written from it: no second transcription, no reading transcript.json.
"""

from __future__ import annotations

import os
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path

from lens.schemas.config import LensConfig
from lens.schemas.create import CutProposal, TranscriptWord

KIT = Path(__file__).parent.parent / "kit"


# his own channel (ADR 0031); another brand's product comes from the brief edit (its slug: a speech hint)
ACME = """product: {name: acme., spoken: Acme, url: https://acme.example,
  one_liner: "Robert's own channel on AI, SEO and GEO for marketers; this reel is about TODO."}"""
OTHER = """product: {name: {{BRAND}}, spoken: {{BRAND}}, url: "https://example.com/TODO",
  one_liner: "TODO what {{BRAND}} is, one line."}"""


def provisional_brief(project: str, language: str, now: datetime, brand: str = "acme") -> str:
    text = (KIT / "presenter-brief.yaml").read_text()
    text = text.replace("{{PRODUCT}}", ACME if brand == "acme" else OTHER)
    for key, val in {"{{PROJECT}}": project, "{{LANGUAGE}}": language, "{{BRAND}}": brand,
                     "{{CREATED_AT}}": now.strftime("%Y-%m-%dT%H:%M:%SZ")}.items():  # fmt: skip
        text = text.replace(key, val)
    return text


def set_language(brief: str, language: str) -> str:
    return re.sub(r"^language: \S+$", f"language: {language}", brief, count=1, flags=re.M)


def place_take(video: Path, raw: Path) -> Path:
    """The take at raw/01-take<ext>: a hard link when the disk allows (no second copy of a big file)."""
    raw.mkdir(parents=True, exist_ok=True)
    target = raw / f"01-take{video.suffix.lower()}"
    others = [p for p in raw.iterdir() if p.is_file() and p.name != target.name]
    if others:  # ingest would take every file in raw/ as another take
        raise FileExistsError(f"{raw} already holds {others[0].name}: one take per project (another slug)")
    if target.exists():
        if target.samefile(video) or target.stat().st_size == video.stat().st_size:
            return target
        raise FileExistsError(f"{target} holds another take: remove it or use another project slug")
    try:
        os.link(video, target)
    except OSError:
        shutil.copy2(video, target)
    return target


def seconds(text: str) -> float:
    """A time as Robert writes it: '41', '41.5', '0:41' or '1:05'."""
    m, _, s = text.strip().rpartition(":")
    return float(m or 0) * 60 + float(s)


def kept_ids(proposals: list[CutProposal], times: list[float], pad: float) -> list[str]:
    """The proposed cuts he wants kept in: any that touches one of his times (within `pad`)."""
    return [c.id for c in proposals if any(c.start_s - pad <= t <= c.end_s + pad for t in times)]


def said(words: list[TranscriptWord]) -> str:
    """What he says, as plain text (sound events left out)."""
    return " ".join(w.text for w in words if w.kind != "event")


def run_take(
    root: Path,
    project: str,
    video: Path,
    cfg: LensConfig,
    terms: list[str],
    language: str | None = None,
    brand: str = "acme",
    approve: bool = False,
    keep: list[float] | None = None,
) -> list[str]:
    """`approve`: Robert decided the cuts in his message ("cuts: all", "all, keep 0:41"): record his decision
    and write no cut page. Otherwise the phone page for him to tap."""
    from create.footage.cutpage import run_cut_page
    from create.footage.run import run_cuts, run_ingest, run_transcript, write_approvals

    base = root / "projects" / project
    base.mkdir(parents=True, exist_ok=True)
    brief_p = base / "brief.yaml"
    provisional = not brief_p.exists()
    lines: list[str] = []
    if provisional:
        brief_p.write_text(provisional_brief(project, language or "en", datetime.now(UTC), brand))
    take = place_take(video, root / "data" / "create" / project / "footage" / "raw")
    _, footage = run_ingest(root, project, cfg)
    lines += [f"take: {take.relative_to(root)}"] + [
        f"  {t.id}: {t.width}x{t.height}, {t.duration_s:.1f} s{', HDR tone-mapped' if t.hdr else ''}"
        for t in footage.takes
    ]
    detect = provisional and language is None  # Scribe forces a language it is given: let it find his
    _, tr = run_transcript(root, project, cfg, terms, language="" if detect else None)
    if detect:
        brief_p.write_text(set_language(brief_p.read_text(), tr.language))
    if not (base / "tokens.json").exists():  # C3: prep (captions), the panel, the cover and review read it
        from create.project import brand_dir
        from create.tokens import run_tokens, token_errors

        _, toks = run_tokens(root, project, cfg)
        errors = token_errors(toks, cfg.create.design, brand_dir(root, project))
        lines.append(f"tokens: {toks.frame} frame" + (f"; ERRORS: {'; '.join(errors)}" if errors else ""))
    fillers = sum(w.kind == "filler" for w in tr.words)
    lines.append(f"transcript: {len(tr.words)} words ({tr.engine}, {tr.language}), {fillers} fillers")
    _, cuts = run_cuts(root, project, cfg)
    kept = sum(t.duration_s for t in footage.takes) - sum(c.end_s - c.start_s for c in cuts.proposals)
    lines.append(f"cuts: {len(cuts.proposals)} proposals, ~{kept:.0f} s if all are approved")
    lines += [
        f"  {c.id} {c.start_s:7.2f}-{c.end_s:7.2f}s {c.kind:<8} {c.reason[:70]}" for c in cuts.proposals
    ]
    if approve:
        pad = cfg.create.footage.keep_pad_s
        kept_in = kept_ids(cuts.proposals, keep or [], pad)
        missed = [t for t in keep or [] if not kept_ids(cuts.proposals, [t], pad)]
        write_approvals(root, project, "all", kept_in)
        note = f"approved: {len(cuts.proposals) - len(kept_in)} cuts, as Robert said"
        note += f"; kept in: {', '.join(kept_in)}" if kept_in else ""
        note += f"; no proposed cut near {', '.join(f'{t:g} s' for t in missed)}" if missed else ""
        lines.append(note)
    else:
        lines.append(f"phone page: {run_cut_page(root, project)} (publish it, send the link)")
    if provisional:
        lines.append(
            f"brief: {brief_p.relative_to(root)} is provisional: replace its TODO lines from this text"
        )
    lines.append(f"said: {said(tr.words)}")
    return lines
