"""S12 report: render a compare report as Markdown and a self-contained HTML page."""

from __future__ import annotations

import html
from datetime import date

from lens.schemas.compare import CompareReport, Fix, MetricResult

STATUS = {"pass": "✅ pass", "fail": "❌ fail", "n/a": "· n/a"}
SECTIONS = (
    ("voice", "Voice"),
    ("sound", "Sound"),
    ("motion", "Motion"),
    ("rhythm", "Rhythm"),
)


def stamp(t: float) -> str:
    return f"{int(t // 60)}:{int(t % 60):02d}"


def _corpus_status(m: MetricResult) -> str:
    if m.status == "n/a":
        return "· n/a"
    if m.status == "pass":
        return "✅ in range"
    return f"❌ {m.note or 'outside'}"


def _fix_lines(i: int, f: Fix) -> list[str]:
    at = ", ".join(stamp(t) for t in f.timestamps_s)
    refs = ", ".join(f"`{r}`" for r in f.refs)
    out = [f"{i}. **{f.problem}** (effort {f.effort}, severity {f.severity:g})  "]
    if at:
        out.append(f"   At {at}. ")
    out.append(f"   {f.change}  ")
    if refs:
        out.append(f"   Recipe book: {refs}")
    out += [f"   - {e}" for e in f.evidence]
    return out


def corpus_markdown(r: CompareReport, fixes: list[Fix]) -> str:
    lines = [
        f"# Compare report: `{r.video_id}`",
        "",
        f"Against **{len(r.cohort)} premium videos of the same format** (weighted corpus) · destination "
        f"**{r.destination}** · lens {r.provenance.tool_version} · {r.provenance.created_at:%Y-%m-%d %H:%M} UTC",
        "",
        "The premium range is the 25th to 75th percentile of the cohort; the percentile says where this "
        "video sits among them.",
        "",
        "## Top fixes",
        "",
    ]
    if not fixes:
        lines.append("Fixes not written yet (A4: `lens status --fixes <video>`).")
    for i, f in enumerate(fixes, 1):
        lines += _fix_lines(i, f)
    loud = next((m for m in r.metrics if m.id == "loudness"), None)
    for key, title in SECTIONS:
        ms = [m for m in r.metrics if m.section == key]
        if not ms:
            continue
        off = sum(m.status == "fail" for m in ms)
        lines += [
            "",
            f"## {title} ({off} of {len(ms)} outside the premium range)",
            "",
            "| Measure | This video | Premium range | Percentile | Status |",
            "|---|---|---|---|---|",
        ]
        for m in ms:
            value = "-" if m.value is None else f"{m.value:g} {m.unit}"
            band = "-" if m.min is None or m.max is None else f"{m.min:g} to {m.max:g}"
            pct = "-" if m.percentile is None else f"{m.percentile:.0f}"
            lines.append(f"| {m.id.replace('_', ' ')} | {value} | {band} | {pct} | {_corpus_status(m)} |")
        if key == "sound" and loud is not None and loud.value is not None:
            lines += [
                "",
                f"Destination target ({r.destination}): {loud.value:g} LUFS against "
                f"{_range(loud.min, loud.max)} LUFS: {STATUS[loud.status]}.",
            ]
    lines += _baseline_lines(r)
    lines += ["", "## Cohort", "", ", ".join(f"`{v}`" for v in r.cohort)]
    return "\n".join(lines) + "\n"


def _baseline_lines(r: CompareReport) -> list[str]:
    if r.baseline is None:
        return []
    ok = sum(c.ok for c in r.baseline)
    lines = [
        "",
        f"## Tool check: known values of this render ({ok}/{len(r.baseline)} reproduced)",
        "",
        "| Value | Measured | Expected | Tolerance | OK |",
        "|---|---|---|---|---|",
    ]
    for c in r.baseline:
        got = "-" if c.measured is None else f"{c.measured:g}"
        lines.append(f"| {c.name} | {got} | {c.expected:g} | ±{c.tolerance:g} | {'✅' if c.ok else '❌'} |")
    return lines


def _range(lo: float | None, hi: float | None) -> str:
    if lo is not None and hi is not None:
        return f"{lo:g} to {hi:g}"
    return f"≥ {lo:g}" if lo is not None else f"≤ {hi:g}"


def markdown(r: CompareReport, fixes: list[Fix] | None = None) -> str:
    if r.mode == "corpus":
        return corpus_markdown(r, fixes if fixes is not None else r.fixes)
    lines = [
        f"# Compare report: `{r.video_id}`",
        "",
        f"Mode: **{r.mode}** · destination: **{r.destination}** · lens {r.provenance.tool_version} · "
        f"{r.provenance.created_at:%Y-%m-%d %H:%M} UTC",
        "",
        "Targets are house placeholders until the corpus (M8) replaces them with measured reference ranges.",
        "",
        "## Top fixes",
        "",
    ]
    if not r.fixes:
        lines.append("No measured gaps against the current targets.")
    for i, f in enumerate(r.fixes, 1):
        lines.append(f"{i}. **{f.problem}** (effort {f.effort}, severity {f.severity:g})  ")
        lines.append(f"   {f.change}")
        for e in f.evidence:
            lines.append(f"   - {e}")
    lines += ["", "## Metrics", "", "| Metric | Value | Target | Status | Source |", "|---|---|---|---|---|"]
    for m in r.metrics:
        value = "-" if m.value is None else f"{m.value:g} {m.unit}"
        note = f" ({m.note})" if m.note else ""
        lines.append(
            f"| {m.id} | {value} | {_range(m.min, m.max)} {m.unit} | {STATUS[m.status]}{note} | {m.source} |"
        )
    if r.baseline is not None:
        ok = sum(c.ok for c in r.baseline)
        lines += [
            "",
            f"## Tool check: known values of this render ({ok}/{len(r.baseline)} reproduced)",
            "",
            "| Value | Measured | Expected | Tolerance | OK |",
            "|---|---|---|---|---|",
        ]
        for c in r.baseline:
            got = "-" if c.measured is None else f"{c.measured:g}"
            lines.append(
                f"| {c.name} | {got} | {c.expected:g} | ±{c.tolerance:g} | {'✅' if c.ok else '❌'} |"
            )
    lines += ["", "## Not measured yet", ""] + [f"- {x}" for x in r.not_yet_measured]
    return "\n".join(lines) + "\n"


def html_page(r: CompareReport, fixes: list[Fix] | None = None) -> str:
    """A small self-contained page (light/dark aware); the Markdown is the source of truth."""
    if r.mode == "corpus":
        return corpus_html(r, fixes if fixes is not None else r.fixes)
    rows = []
    for m in r.metrics:
        value = "-" if m.value is None else f"{m.value:g} {html.escape(m.unit)}"
        rows.append(
            f"<tr class='{m.status.replace('/', '')}'><td>{html.escape(m.id)}</td><td>{value}</td>"
            f"<td>{html.escape(_range(m.min, m.max))}</td><td>{html.escape(STATUS[m.status])}</td>"
            f"<td>{html.escape(m.source)}</td></tr>"
        )
    items: list[str] = []
    for f in r.fixes:
        ev = "".join(f"<li>{html.escape(e)}</li>" for e in f.evidence)
        items.append(
            f"<li><strong>{html.escape(f.problem)}</strong> <span class='tag'>effort {f.effort}</span>"
            f"<p>{html.escape(f.change)}</p>{'<ul>' + ev + '</ul>' if ev else ''}</li>"
        )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Compare: {html.escape(r.video_id)}</title>
<style>
:root{{--bg:#fff;--fg:#1e2a3b;--muted:#5b6778;--line:#e3e7ee;--bad:#b42318;--ok:#067647}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0f141b;--fg:#e8edf4;--muted:#9aa6b3;--line:#253041;--bad:#f97066;--ok:#47cd89}}}}
body{{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;max-width:960px;margin:0 auto;padding:24px 16px}}
table{{width:100%;border-collapse:collapse}}td,th{{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left}}
tr.fail td:nth-child(4){{color:var(--bad)}}tr.pass td:nth-child(4){{color:var(--ok)}}.tag{{color:var(--muted);font-size:13px}}
p{{margin:4px 0}}small{{color:var(--muted)}}
</style></head><body>
<h1>Compare: {html.escape(r.video_id)}</h1>
<small>{r.mode} · destination {html.escape(r.destination)} · lens {r.provenance.tool_version} · {date.today():%Y-%m-%d}</small>
<h2>Top fixes</h2><ol>{"".join(items) or "<li>No measured gaps.</li>"}</ol>
<h2>Metrics</h2><table><tr><th>Metric</th><th>Value</th><th>Target</th><th>Status</th><th>Source</th></tr>{"".join(rows)}</table>
</body></html>
"""


def corpus_html(r: CompareReport, fixes: list[Fix]) -> str:
    e = html.escape
    fx = []
    for f in fixes:
        at = ", ".join(stamp(t) for t in f.timestamps_s)
        refs = " ".join(f"<code>{e(x)}</code>" for x in f.refs)
        ev = "".join(f"<li>{e(x)}</li>" for x in f.evidence)
        fx.append(
            f"<li><strong>{e(f.problem)}</strong> <span class='tag'>effort {f.effort} · at {e(at)}</span>"
            f"<p>{e(f.change)}</p><p class='tag'>Recipe book: {refs}</p><ul>{ev}</ul></li>"
        )
    sections = []
    for key, title in SECTIONS:
        ms = [m for m in r.metrics if m.section == key]
        if not ms:
            continue
        rows = []
        for m in ms:
            value = "-" if m.value is None else f"{m.value:g} {e(m.unit)}"
            band = "-" if m.min is None or m.max is None else f"{m.min:g} to {m.max:g}"
            pct = "-" if m.percentile is None else f"{m.percentile:.0f}"
            rows.append(
                f"<tr class='{m.status.replace('/', '')}'><td>{e(m.id.replace('_', ' '))}</td><td>{value}</td>"
                f"<td>{band}</td><td>{pct}</td><td>{e(_corpus_status(m))}</td></tr>"
            )
        sections.append(
            f"<h2>{title}</h2><div class='scroll'><table><tr><th>Measure</th><th>This video</th>"
            f"<th>Premium range</th><th>Percentile</th><th>Status</th></tr>{''.join(rows)}</table></div>"
        )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Compare: {e(r.video_id)}</title>
<style>
:root{{--bg:#fff;--fg:#1e2a3b;--muted:#5b6778;--line:#e3e7ee;--bad:#b42318;--ok:#067647}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0f141b;--fg:#e8edf4;--muted:#9aa6b3;--line:#253041;--bad:#f97066;--ok:#47cd89}}}}
body{{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;max-width:960px;margin:0 auto;padding:24px 16px}}
table{{width:100%;border-collapse:collapse}}td,th{{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left}}
.scroll{{overflow-x:auto}}tr.fail td:last-child{{color:var(--bad)}}tr.pass td:last-child{{color:var(--ok)}}
.tag{{color:var(--muted);font-size:13px}}p{{margin:4px 0}}small{{color:var(--muted)}}li{{margin-bottom:10px}}
</style></head><body>
<h1>Compare: {e(r.video_id)}</h1>
<small>against {len(r.cohort)} premium videos of the same format · destination
{e(r.destination)} · lens {r.provenance.tool_version} · {r.provenance.created_at:%Y-%m-%d}</small>
<h2>Top fixes</h2><ol>{"".join(fx) or "<li>Fixes not written yet.</li>"}</ol>
{"".join(sections)}
</body></html>
"""
