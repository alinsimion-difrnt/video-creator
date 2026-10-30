"""`lens` command line. Everything works through this CLI and files; MCP is never required."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Annotated

import typer

from lens import __version__
from lens.config import REPO_ROOT
from lens.schemas import SourceEntry
from lens.stages import STAGES, check_dag

app = typer.Typer(
    help="explainer-video-creator, Phase 1: measure and name what makes explainers premium.",
    no_args_is_help=True,
)
schemas_app = typer.Typer(help="JSON Schema export.", no_args_is_help=True)
app.add_typer(schemas_app, name="schemas")


@app.callback()
def _main(
    version: Annotated[bool, typer.Option("--version", help="Print the version and exit.")] = False,
) -> None:
    if version:
        typer.echo(__version__)
        raise typer.Exit()


@app.command()
def validate(
    paths: Annotated[list[Path] | None, typer.Argument(help="Files to validate.")] = None,
    all_: Annotated[bool, typer.Option("--all", help="Validate every committed file with a schema.")] = False,
) -> None:
    """Validate files against their schemas. Exit code 1 if any file is invalid."""
    from lens.validate import validate_all, validate_file

    if not paths and not all_:
        raise typer.BadParameter("give one or more paths, or --all")
    results = validate_all() if all_ else [validate_file(p) for p in paths or []]
    if not results:
        typer.echo("nothing to validate: no files with a registered schema (is LENS_ROOT / cwd the repo?)")
        raise typer.Exit(1)
    failed = 0
    for r in results:
        if r.ok:
            typer.echo(f"ok      {r.path}")
        else:
            failed += 1
            typer.echo(f"INVALID {r.path}")
            for e in r.errors:
                typer.echo(f"        - {e}")
    typer.echo(f"{len(results) - failed}/{len(results)} valid")
    if failed:
        raise typer.Exit(1)


@app.command()
def dag(
    check: Annotated[
        bool, typer.Option("--check", help="Verify the stage registry is a strict DAG.")
    ] = False,
) -> None:
    """Show the stage registry, or check it (declared writes, no overlaps, no cycles)."""
    if check:
        errors = check_dag()
        for e in errors:
            typer.echo(f"ERROR {e}")
        if errors:
            raise typer.Exit(1)
        typer.echo(f"dag ok: {len(STAGES)} stages, no cycles, no overlapping or case-colliding writes")
        return
    for s in STAGES:
        after = ", ".join(s.after) or "-"
        typer.echo(f"{s.id:<20} {s.runner:<6} {s.milestone:<8} after: {after}")
        for w in s.writes:
            typer.echo(f"{'':<20} writes {w}")


@schemas_app.command("export")
def schemas_export(
    out: Annotated[Path, typer.Option(help="Output directory.")] = REPO_ROOT / "exports" / "schemas",
    check: Annotated[bool, typer.Option("--check", help="Fail if committed schemas are stale.")] = False,
) -> None:
    """Write JSON Schemas for every model (or check they are up to date)."""
    from lens.schemas.export import export, stale

    if check:
        problems = stale(out)
        for p in problems:
            typer.echo(f"STALE {p}  (run: uv run lens schemas export)")
        if problems:
            raise typer.Exit(1)
        typer.echo("schemas up to date")
        return
    for path in export(out):
        typer.echo(f"wrote {path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path}")


def _select(videos: list[str] | None) -> list[SourceEntry]:
    from lens.validate import load_sources

    entries = load_sources(REPO_ROOT)
    if videos:
        known = {e.id for e in entries}
        unknown = sorted(set(videos) - known)
        if unknown:
            raise typer.BadParameter(f"unknown video id(s): {', '.join(unknown)}")
        entries = [e for e in entries if e.id in videos]
    return entries


VideoOpt = Annotated[list[str] | None, typer.Option("--video", "-v", help="Only these source ids.")]
ForceOpt = Annotated[bool, typer.Option("--force", help="Ignore the cache and redo the work.")]


@app.command()
def ingest(video: VideoOpt = None, force: ForceOpt = False) -> None:
    """[S1] Fetch ready sources into data/media/<id>/ (https, r2://inbox/, file://)."""
    from lens.ingest import IngestError, ingest_one
    from lens.storage import StorageError

    failed = 0
    for entry in _select(video):
        try:
            r = ingest_one(entry, REPO_ROOT, force=force)
            typer.echo(f"{r.status:<10} {r.video} {r.detail}".rstrip())
        except (IngestError, StorageError, OSError) as exc:
            failed += 1
            typer.echo(f"FAILED     {entry.id}: {exc}")
    if failed:
        raise typer.Exit(1)


@app.command()
def frames(video: VideoOpt = None, force: ForceOpt = False) -> None:
    """[S2] Normalize: meta.json, CFR proxy at native fps, audio.wav, 2 fps base frames, palette."""
    from lens.config import load_config
    from lens.frames import NormalizeError, normalize_one
    from lens.media import MediaError

    cfg = load_config()
    failed = 0
    for entry in _select(video):
        try:
            r = normalize_one(entry, REPO_ROOT, cfg, force=force)
            typer.echo(f"{r.status:<10} {r.video} {r.detail}".rstrip())
        except (NormalizeError, MediaError, OSError) as exc:
            failed += 1
            typer.echo(f"FAILED     {entry.id}: {exc}")
    if failed:
        raise typer.Exit(1)


@app.command()
def signals(video: VideoOpt = None, force: ForceOpt = False) -> None:
    """[S3] Cuts, transitions, events, holds, pace; loudness, beats, SFX; words and prosody."""
    from lens.config import load_config
    from lens.media import MediaError
    from lens.signals import SignalsError, run_signals

    cfg = load_config()
    failed = 0
    for entry in _select(video):
        try:
            typer.echo(f"{run_signals(entry, REPO_ROOT, cfg, force=force):<10} {entry.id}")
        except (SignalsError, MediaError, OSError) as exc:
            failed += 1
            typer.echo(f"FAILED     {entry.id}: {exc}")
    if failed:
        raise typer.Exit(1)


@app.command()
def evidence(video: VideoOpt = None, force: ForceOpt = False) -> None:
    """[S4] Filmstrips, candidate boxes, set-of-marks, spectrograms, contact sheets per event/shot."""
    from lens.config import load_config
    from lens.evidence import EvidenceError, run_evidence
    from lens.media import MediaError

    cfg = load_config()
    failed = 0
    for entry in _select(video):
        try:
            typer.echo(f"{run_evidence(entry, REPO_ROOT, cfg, force=force):<10} {entry.id}")
        except (EvidenceError, MediaError, OSError) as exc:
            failed += 1
            typer.echo(f"FAILED     {entry.id}: {exc}")
    if failed:
        raise typer.Exit(1)


@app.command()
def packets(video: VideoOpt = None, force: ForceOpt = False) -> None:
    """[S5] Annotation packets within image budgets, event triage, packets/<id>/manifest.json."""
    from lens.config import load_config
    from lens.packets import PacketError, build_packets

    cfg = load_config()
    failed = 0
    for entry in _select(video):
        try:
            typer.echo(f"{build_packets(entry, REPO_ROOT, cfg, force=force):<10} {entry.id}")
        except (PacketError, OSError, KeyError) as exc:
            failed += 1
            typer.echo(f"FAILED     {entry.id}: {exc}")
    if failed:
        raise typer.Exit(1)


@app.command()
def preview(
    video: Annotated[str, typer.Option("--video", "-v")],
    embed: Annotated[bool, typer.Option(help="Inline downscaled images: one shareable file.")] = False,
    max_events: Annotated[int | None, typer.Option(help="Show at most this many event tasks.")] = None,
    out: Annotated[Path | None, typer.Option(help="Default: data/packets/<id>/preview.html")] = None,
    title: Annotated[str | None, typer.Option(help="Page name (default: '<id> packets').")] = None,
) -> None:
    """[S5] HTML preview of a video's packets: every task with its images, and triage."""
    from lens.packets.preview import render_preview

    dest = out or REPO_ROOT / "data" / "packets" / video / "preview.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        render_preview(REPO_ROOT, video, embed=embed, max_events=max_events, title=title), encoding="utf-8"
    )
    typer.echo(f"wrote {dest}")


@app.command()
def status(
    pending: Annotated[bool, typer.Option("--pending", help="Only videos with pending tasks (ids).")] = False,
    limit: Annotated[int | None, typer.Option(help="At most this many videos.")] = None,
    as_json: Annotated[bool, typer.Option("--json")] = False,
    task: Annotated[
        str | None, typer.Option(help="<video>/<task id>: the annotator's brief and provenance to copy.")
    ] = None,
    rerun: Annotated[
        str | None, typer.Option(help="With --task: a blind re-annotation for `lens eval`, run id.")
    ] = None,
    card: Annotated[str | None, typer.Option(help="<pattern id>: the A3 card writer's brief.")] = None,
    scenes: Annotated[str | None, typer.Option(help="<batch id>: the A3 scene sorter's brief.")] = None,
    archetype: Annotated[
        str | None, typer.Option(help="<archetype id>: the A3 archetype card brief.")
    ] = None,
    fixes: Annotated[str | None, typer.Option(help="<video>: the A4 compare-fixes brief.")] = None,
) -> None:
    """Annotation status from packet manifests and outputs on disk (nothing else is tracked)."""
    import json

    from lens.packets import status as packet_status
    from lens.packets import task_brief

    if fixes is not None:
        from lens.compare.fixes import fixes_brief

        typer.echo(json.dumps(fixes_brief(REPO_ROOT, fixes), indent=1))
        return
    if archetype is not None:
        from lens.config import load_config
        from lens.synth.cards import archetype_brief

        typer.echo(json.dumps(archetype_brief(REPO_ROOT, load_config(), archetype), indent=1))
        return
    if scenes is not None:
        from lens.config import load_config
        from lens.synth.scenes import scene_brief

        typer.echo(json.dumps(scene_brief(REPO_ROOT, load_config(), scenes), indent=1))
        return
    if card is not None:
        from lens.config import load_config
        from lens.synth.cards import card_brief

        typer.echo(json.dumps(card_brief(REPO_ROOT, load_config(), card), indent=1))
        return
    if rerun is not None and not re.fullmatch(r"[a-z0-9][a-z0-9-]*", rerun):
        raise typer.BadParameter("--rerun must be a lowercase id (a-z, 0-9, '-')")
    if task is not None:
        video, _, task_id = task.partition("/")
        try:
            typer.echo(json.dumps(task_brief(REPO_ROOT, video, task_id, rerun), indent=1))
        except (FileNotFoundError, KeyError) as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(1) from exc
        return
    rows = packet_status(REPO_ROOT)
    if pending:
        rows = [r for r in rows if r["pending"]]
    rows = rows[:limit] if limit is not None else rows
    if as_json:
        typer.echo(json.dumps(rows, indent=1))
    elif pending:
        typer.echo("\n".join(r["video"] for r in rows))
    else:
        for r in rows:
            typer.echo(
                f"{r['video']:<40} {r['done']}/{r['tasks']} done, {len(r['pending'])} pending "
                f"({r['pending_images']} images), {r['skipped']} events skipped"
            )


@app.command()
def measure(
    video: Annotated[str, typer.Option("--video", "-v")],
    event: Annotated[
        str | None, typer.Option("--event", "-e", help="One event, e.g. e012 (needs --box).")
    ] = None,
    box: Annotated[
        list[str] | None, typer.Option("--box", "-b", help="Candidate box id(s) from candidates.json.")
    ] = None,
    force: ForceOpt = False,
) -> None:
    """[S7] Track boxes; fit eases, springs, beziers; text stagger; SFX offset.

    Without --event: every A2-annotated event, the boxes A2 chose (candidate or manual), one decode of
    the proxy. With --event and --box: hand-picked candidate boxes. Writes videos/<id>/measure/<eid>.json."""
    from lens.config import load_config
    from lens.measure.run import MeasureError, measure_event, measure_video

    (entry,) = _select([video])
    cfg = load_config()
    try:
        if event is None:
            paths = measure_video(entry, REPO_ROOT, cfg, force)
        elif not box:
            raise typer.BadParameter("--event needs --box")
        else:
            paths = [measure_event(entry, REPO_ROOT, cfg, event, box)]
    except (MeasureError, OSError) as exc:
        typer.echo(f"FAILED     {video} {event or ''}: {exc}")
        raise typer.Exit(1) from exc
    for p in paths:
        typer.echo(f"wrote {p.relative_to(REPO_ROOT)}")
    if not paths:
        typer.echo(f"cached     {video} (nothing to measure)")


@app.command()
def reconcile(video: VideoOpt = None, force: ForceOpt = False) -> None:
    """[S8] Merge signals, A1/A2 annotations and S7 measurements into videos/<id>/record.json."""
    from lens.config import load_config
    from lens.reconcile import ReconcileError, reconcile_video

    cfg = load_config()
    failed = 0
    for entry in _select(video):
        if not (REPO_ROOT / "videos" / entry.id / "signals.summary.json").exists():
            if video:
                typer.echo(f"skip       {entry.id} (no signals.summary.json)")
            continue
        try:
            typer.echo(f"{reconcile_video(entry, REPO_ROOT, cfg, force):<10} {entry.id}")
        except (ReconcileError, OSError, ValueError) as exc:
            failed += 1
            typer.echo(f"FAILED     {entry.id}: {exc}")
    if failed:
        raise typer.Exit(1)


@app.command()
def queue(
    limit: Annotated[int | None, typer.Option(help="At most this many (default: batch.per_run).")] = None,
    as_json: Annotated[bool, typer.Option("--json", help="Print a JSON list (for a CI matrix).")] = False,
    retry_failed: Annotated[bool, typer.Option(help="Include videos a previous run failed on.")] = False,
) -> None:
    """Ready sources still to analyse whose media has arrived (S3 not done per storage markers)."""
    import json

    from lens.config import load_config
    from lens.storage import get_storage
    from lens.storage import queue as pending

    n = limit if limit is not None else load_config().batch.per_run
    ids = pending(_select(None), get_storage(), n, retry_failed)
    typer.echo(json.dumps(ids) if as_json else "\n".join(ids))


@app.command()
def compare(
    video: Annotated[str, typer.Option("--video", "-v", help="Source id (after `lens signals`).")],
    targets_only: Annotated[
        bool, typer.Option("--targets-only", help="Absolute house targets, no corpus (default: corpus).")
    ] = False,
    destination: Annotated[str | None, typer.Option(help="Loudness target, e.g. linkedin, youtube.")] = None,
) -> None:
    """[S11+S12] Place a video against targets and write reports/compare/<id>/ (metrics, md, html)."""
    from lens.compare import compare_targets
    from lens.config import load_config
    from lens.schemas.signals import SignalsSummary
    from lens.schemas.video import VideoMeta

    base = REPO_ROOT / "videos" / video
    summary_path = base / "signals.summary.json"
    if not summary_path.exists():
        typer.echo(f"no signals for {video}; run `lens signals --video {video}` first", err=True)
        raise typer.Exit(1)
    meta = VideoMeta.model_validate_json((base / "meta.json").read_text(encoding="utf-8"))
    summary = SignalsSummary.model_validate_json(summary_path.read_text(encoding="utf-8"))
    if targets_only:
        report = compare_targets(meta, summary, load_config(), destination)
    else:
        from lens.compare.corpus import compare_corpus

        try:
            report = compare_corpus(REPO_ROOT, video, load_config(), destination)
        except (ValueError, OSError) as exc:
            typer.echo(f"FAILED     {exc}", err=True)
            raise typer.Exit(1) from exc
    out = REPO_ROOT / "reports" / "compare" / video
    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    _render(out, report)
    fails = sum(m.status == "fail" for m in report.metrics)
    where = out.relative_to(REPO_ROOT)
    typer.echo(f"{video}: {fails} metric(s) outside targets, {len(report.fixes)} fix(es) -> {where}")


@app.command()
def report(video: Annotated[str, typer.Option("--video", "-v")]) -> None:
    """[S12] Re-render reports/compare/<id>/ Markdown and HTML from metrics.json."""
    from lens.schemas.compare import CompareReport

    out = REPO_ROOT / "reports" / "compare" / video
    data = CompareReport.model_validate_json((out / "metrics.json").read_text(encoding="utf-8"))
    for path in _render(out, data):
        typer.echo(f"wrote {path.relative_to(REPO_ROOT)}")


def _render(out: Path, data: object) -> list[Path]:
    from lens.report import html_page, markdown
    from lens.schemas.compare import CompareReport

    assert isinstance(data, CompareReport)
    day = f"{data.provenance.created_at:%Y-%m-%d}"
    md, page = out / f"{day}.md", out / f"{day}.html"
    fixes = None
    if (out / "fixes.json").exists():
        from lens.schemas.compare import FixesFile

        fixes = FixesFile.model_validate_json((out / "fixes.json").read_text("utf-8")).fixes
    md.write_text(markdown(data, fixes), encoding="utf-8")
    page.write_text(html_page(data, fixes), encoding="utf-8")
    return [md, page]


gold_app = typer.Typer(help="G2 gold set: seed, review page, import reviews.", no_args_is_help=True)
app.add_typer(gold_app, name="gold")


def _gold_videos(video: list[str] | None) -> list[SourceEntry]:
    from lens.config import load_config

    return _select(video or load_config().gold.videos)


@gold_app.command("seed")
def gold_seed(video: VideoOpt = None, force: ForceOpt = False) -> None:
    """Write gold/<id>/gold.yaml from the annotations (default: the config's gold videos). A file that
    holds reviewed items is kept unless --force."""
    from lens.config import load_config
    from lens.gold import GoldError, seed_file

    cfg = load_config()
    for entry in _gold_videos(video):
        try:
            typer.echo(f"{seed_file(entry, REPO_ROOT, cfg, force):<10} {entry.id}")
        except (GoldError, OSError) as exc:
            typer.echo(f"FAILED     {entry.id}: {exc}")
            raise typer.Exit(1) from exc


@gold_app.command("page")
def gold_page(
    out: Annotated[Path, typer.Option(help="HTML file to write (keep it out of the repo).")],
    video: VideoOpt = None,
) -> None:
    """Render the review page for the gold files (images inlined; never commit it)."""
    from lens.gold import gold_path, load_gold
    from lens.gold.page import render_page

    golds = [load_gold(gold_path(REPO_ROOT, e.id)) for e in _gold_videos(video)]
    out.write_text(render_page(REPO_ROOT, golds), "utf-8")
    typer.echo(f"wrote      {out} ({out.stat().st_size / 1e6:.1f} MB)")


@gold_app.command("import")
def gold_import(
    reviews: Annotated[Path, typer.Argument(help="JSON: review documents, as {id: body} or [{id, data}].")],
) -> None:
    """Merge the review page's documents into the gold files."""
    from lens.gold import apply_reviews, gold_path, load_gold, write_gold
    from lens.validate import validate_file

    raw = json.loads(reviews.read_text("utf-8"))
    docs = raw if isinstance(raw, dict) else {d["id"]: d["data"] for d in raw}
    videos = sorted({k.split("~")[0] for k in docs})
    for v in videos:
        path = gold_path(REPO_ROOT, v)
        gold, n = apply_reviews(load_gold(path), docs)
        write_gold(path, gold)
        result = validate_file(path, REPO_ROOT)
        if not result.ok:
            typer.echo(f"INVALID    {path}: " + "; ".join(result.errors))
            raise typer.Exit(1)
        typer.echo(f"imported   {v}: {n} item(s)")


storage_app = typer.Typer(help="R2 / local object storage.", no_args_is_help=True)
app.add_typer(storage_app, name="storage")


@storage_app.command("push")
def storage_push(video: VideoOpt = None) -> None:
    """Upload normalized media (and, once the proxy is verified, the original) to storage."""
    from lens.config import load_config
    from lens.storage import get_storage, push_state, push_video

    cfg, storage = load_config(), get_storage()
    for entry in _select(video):
        n = push_video(entry.id, entry, cfg, REPO_ROOT, storage)
        m = push_state(entry.id, REPO_ROOT, storage)
        typer.echo(f"pushed     {entry.id}: {n} object(s), {m} marker(s)")


@storage_app.command("pull-outputs")
def storage_pull_outputs(video: VideoOpt = None) -> None:
    """Download committed outputs (meta, palette, signals summary, packet manifest) kept in R2."""
    from lens.storage import get_storage, pull_outputs

    storage = get_storage()
    total = 0
    for entry in _select(video):
        n = pull_outputs(entry.id, REPO_ROOT, storage)
        total += n
        if n:
            typer.echo(f"pulled     {entry.id}: {n} file(s)")
    typer.echo(f"{total} file(s) pulled")


@storage_app.command("pull-packets")
def storage_pull_packets(video: VideoOpt = None) -> None:
    """Download annotation packets (images and JSON) from storage into data/packets/."""
    from lens.storage import get_storage, pull_packets

    storage = get_storage()
    for entry in _select(video):
        typer.echo(f"pulled     {entry.id}: {pull_packets(entry.id, REPO_ROOT, storage)} file(s)")


@storage_app.command("pull-media")
def storage_pull_media(
    kind: Annotated[list[str], typer.Option("--kind", help="signals | evidence | packets (repeatable).")],
    video: VideoOpt = None,
) -> None:
    """Download a video's local stage data from storage into data/<kind>/<video>/."""
    from lens.storage import get_storage, pull_media

    storage = get_storage()
    for entry in _select(video):
        n = sum(pull_media(entry.id, k, REPO_ROOT, storage) for k in kind)
        typer.echo(f"pulled     {entry.id}: {n} file(s) ({', '.join(kind)})")


@storage_app.command("inbox")
def storage_inbox() -> None:
    """Which ready r2://inbox/ sources have their upload (and which do not yet)."""
    from lens.schemas.sources import Status
    from lens.storage import get_storage, inbox_key

    storage = get_storage()
    present = missing = 0
    for e in _select(None):
        if e.status is not Status.READY or not (e.url or "").startswith("r2://inbox/"):
            continue
        size = storage.size(inbox_key(e.url or ""))
        if size is None:
            missing += 1
            typer.echo(f"missing    {e.id}")
        else:
            present += 1
            typer.echo(f"present    {e.id} ({size / 1e6:.1f} MB)")
    typer.echo(f"{present} present, {missing} missing")


@storage_app.command("pull-state")
def storage_pull_state(video: VideoOpt = None) -> None:
    """Download stage markers so reruns on a fresh runner skip finished work."""
    from lens.storage import get_storage, pull_state

    storage = get_storage()
    for entry in _select(video):
        typer.echo(f"pulled     {entry.id}: {pull_state(entry.id, REPO_ROOT, storage)} marker(s)")


@storage_app.command("put-inbox")
def storage_put_inbox(path: Path) -> None:
    """Upload a local file to inbox/ (then use r2://inbox/<name> in sources.yaml)."""
    from lens.storage import get_storage

    name = path.name.lower()
    get_storage().upload(path, f"inbox/{name}")
    typer.echo(f"r2://inbox/{name}")


@storage_app.command("lifecycle")
def storage_lifecycle(
    apply: Annotated[bool, typer.Option("--apply", help="Put the rules on the R2 bucket.")] = False,
) -> None:
    """Show (or apply) the lifecycle rules that expire non-kept originals."""
    import json

    from lens.config import load_config
    from lens.storage import R2Storage, apply_lifecycle, lifecycle_configuration

    cfg = load_config()
    typer.echo(json.dumps(lifecycle_configuration(cfg), indent=2))
    if apply:
        apply_lifecycle(R2Storage.from_env(), cfg)
        typer.echo("applied")


def _planned(name: str, milestone: str, summary: str) -> None:
    def command() -> None:
        typer.echo(f"`lens {name}` is not implemented yet (milestone {milestone}).", err=True)
        raise typer.Exit(2)

    command.__doc__ = f"[{milestone}] {summary}"
    app.command(name)(command)


@app.command("eval")
def eval_(
    run: Annotated[
        str | None, typer.Option(help="Run id of the blind re-annotations to compare (lens status --rerun).")
    ] = None,
    sample: Annotated[bool, typer.Option(help="Only print the consistency sample (<video>/<task>).")] = False,
) -> None:
    """[S13] Score the annotations: answer key, blind re-annotation agreement, measured share."""
    from lens.config import load_config
    from lens.eval import consistency_sample, run_eval

    cfg = load_config()
    if sample:
        for item in consistency_sample(REPO_ROOT, cfg):
            video, eid = item.split("/")
            typer.echo(f"{video}/a2-{eid}")
        return
    if run is not None and not re.fullmatch(r"[a-z0-9][a-z0-9-]*", run):
        raise typer.BadParameter("--run must be a lowercase id (a-z, 0-9, '-')")
    out, result = run_eval(REPO_ROOT, cfg, run)
    typer.echo(result.model_dump_json(indent=1, exclude={"provenance"}))
    typer.echo(f"wrote      {out.relative_to(REPO_ROOT)}")


@app.command()
def cards(
    pending: Annotated[
        bool, typer.Option(help="List the patterns with no card, or whose card's brief has changed.")
    ] = False,
    g4_page: Annotated[
        Path | None, typer.Option(help="Write the G4 approval page (never commit it).")
    ] = None,
    g4_scenes: Annotated[bool, typer.Option(help="With --g4-page: the scene archetype questions.")] = False,
) -> None:
    """[A3] Render corpus/patterns/<pid>.md from each card JSON (or list the cards still to write)."""
    from lens.config import load_config
    from lens.synth.cards import pending_cards, render_all, render_archetypes

    if g4_page is not None:
        from lens.synth.g4 import render_g4

        syn = load_config().synth
        page = render_g4(REPO_ROOT, syn.g4_hold, syn.g4_hold_archetypes if g4_scenes else None)
        g4_page.write_text(page, "utf-8")
        typer.echo(f"wrote      {g4_page}")
        return
    if pending:
        for pid, why in pending_cards(REPO_ROOT, load_config()):
            typer.echo(f"{pid:<28} {why}")
        return
    for path in [*render_all(REPO_ROOT), *render_archetypes(REPO_ROOT)]:
        typer.echo(f"rendered   {path.relative_to(REPO_ROOT)}")


@app.command("export")
def export_cmd() -> None:
    """[S10] Motion tokens, sound/pacing/voice specs, patterns, archetypes and the skill pack -> exports/."""
    from lens.config import load_config
    from lens.export import ExportError, run_export

    try:
        written = run_export(REPO_ROOT, load_config())
    except ExportError as exc:
        typer.echo(f"FAILED     {exc}")
        raise typer.Exit(1) from exc
    typer.echo(f"wrote      {len(written)} files under exports/")


@app.command("scenes")
def scenes_cmd(
    pending: Annotated[bool, typer.Option(help="List the scene batches not sorted yet.")] = False,
) -> None:
    """[S9] Scene archetype stats -> corpus/stats/scenes.json and taxonomy/scene_proposals.yaml."""
    from lens.config import load_config
    from lens.synth.cluster import minilm
    from lens.synth.scenes import pending_batches, run_scene_stats

    cfg = load_config()
    todo = pending_batches(REPO_ROOT, cfg)
    if pending:
        for b, n in todo:
            typer.echo(f"{b}  {n} shots")
        return
    if todo:
        typer.echo(f"{len(todo)} batch(es) not sorted yet: {' '.join(b for b, _ in todo)}")
        raise typer.Exit(1)
    archetypes, other, proposals = run_scene_stats(REPO_ROOT, cfg, minilm(cfg.synth.cluster))
    typer.echo(f"built      corpus/stats/scenes.json: {archetypes} archetypes, {other} other shots")
    typer.echo(f"wrote      taxonomy/scene_proposals.yaml: {proposals} proposals")


@app.command()
def synth(
    force: ForceOpt = False,
    proposals: Annotated[bool, typer.Option(help="Also cluster `other` patterns (local model).")] = True,
) -> None:
    """[S9] Weighted corpus stats -> corpus/stats/*.json; `other` clusters -> taxonomy/proposals.yaml."""
    from lens.config import load_config
    from lens.synth import run_synth, write_proposals
    from lens.synth.cluster import minilm

    cfg = load_config()
    for name, state in run_synth(REPO_ROOT, cfg, force).items():
        typer.echo(f"{state:<10} corpus/stats/{name}.json")
    if proposals:
        n, left = write_proposals(REPO_ROOT, cfg, minilm(cfg.synth.cluster))
        typer.echo(f"wrote      taxonomy/proposals.yaml: {n} proposals, {left} one-off patterns left out")


@storage_app.command("mark-failed")
def storage_mark_failed(
    video: Annotated[list[str], typer.Option("--video", "-v")],
    note: Annotated[str, typer.Option(help="Where to look, e.g. the CI run URL.")] = "",
) -> None:
    """Record that preparing these videos failed; `lens queue` skips them until --retry-failed."""
    import json
    import tempfile
    from datetime import UTC, datetime

    from lens.storage import failed_key, get_storage

    storage = get_storage()
    for v in video:
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "failed.json"
            f.write_text(json.dumps({"video": v, "note": note, "at": datetime.now(UTC).isoformat()}))
            storage.upload(f, failed_key(v))
        typer.echo(f"marked failed {v}")
