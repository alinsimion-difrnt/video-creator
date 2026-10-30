"""`create` CLI (Phase 2). Stages are registered in lens/stages.py; this CLI runs and reports them."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any

import typer
from pydantic import ValidationError

from create.project import BrandError, brand_dir, brand_missing, brand_of, check_slug, status
from lens.config import REPO_ROOT, load_config

app = typer.Typer(help="Phase 2: create a premium SaaS explainer from a brief.", no_args_is_help=True)


def _slug(project: str) -> str:
    try:
        return check_slug(project)
    except ValidationError as exc:
        raise typer.BadParameter(f"{project!r} is not a lowercase slug") from exc


@app.command()
def init(
    project: Annotated[str, typer.Argument(help="Project slug, e.g. acme-v2.")],
    brand: Annotated[
        str | None, typer.Option("--brand", help="Brand slug: the hand-off in brands/<brand>/.")
    ] = None,
    source: Annotated[
        str | None,
        typer.Option(
            "--from",
            help="Make a sibling of this project: same brief, script, voice, timing (no voice credits).",
        ),
    ] = None,
    destination: Annotated[
        str | None,
        typer.Option(
            "--destination", help="With --from: the sibling's destination, e.g. tiktok or linkedin."
        ),
    ] = None,
) -> None:
    """Create the project folders (and the brand folder if new) and say what the hand-off still needs.

    `--from <project> --destination tiktok` starts a vertical version of a landscape explainer (or the
    other way round): then run `create tokens` and `create direction` for the new frame.
    """
    slug = _slug(project)
    if source is not None:
        from create.project import derive_project

        cfg = load_config()
        if destination is not None and destination not in cfg.create.design.destination_frames:
            known = ", ".join(cfg.create.design.destination_frames)
            raise typer.BadParameter(f"{destination!r} is not a destination ({known})")
        try:
            copied = derive_project(REPO_ROOT, _slug(source), slug, destination)
        except (FileNotFoundError, FileExistsError) as exc:
            typer.echo(str(exc))
            raise typer.Exit(1) from exc
        typer.echo(f"copied {len(copied)} items from {source}: {', '.join(copied)}")
        brand = brand or brand_of(REPO_ROOT, slug)
    elif destination is not None:
        raise typer.BadParameter("--destination needs --from (a new brief names its own destination)")
    if brand is None:
        raise typer.BadParameter("--brand is required (or --from a project whose brief names one)")
    brand_slug = _slug(brand)
    for path in (
        REPO_ROOT / "projects" / slug,
        REPO_ROOT / "data" / "create" / slug,
        REPO_ROOT / "brands" / brand_slug,
    ):
        path.mkdir(parents=True, exist_ok=True)
    typer.echo(f"projects/{slug}/ and data/create/{slug}/ are ready; the brief must say brand: {brand_slug}")
    missing = brand_missing(REPO_ROOT, brand_slug)
    if missing:
        typer.echo(f"brand hand-off missing in brands/{brand_slug}/: {', '.join(missing)}")


@app.command("status")
def status_cmd(
    project: Annotated[str, typer.Argument(help="Project slug.")],
    all_rows: Annotated[bool, typer.Option("--all", help="Also the stages this route does not use.")] = False,
) -> None:
    """Each Phase 2 stage: done, ready, waiting or invalid. Exit code 1 if anything is invalid."""
    slug = _slug(project)
    if not (REPO_ROOT / "projects" / slug).is_dir():
        typer.echo(f"no project {slug!r} (run: uv run create init {slug})")
        raise typer.Exit(1)
    try:
        brand = brand_of(REPO_ROOT, slug)
    except BrandError as exc:
        typer.echo(f"brand        invalid      {exc}")
        raise typer.Exit(1) from exc
    if brand is None:
        typer.echo("brand        waiting      the brief does not name a brand yet")
    else:
        missing = brand_missing(REPO_ROOT, brand)
        if missing:
            typer.echo(f"brand        missing      brands/{brand}/: {', '.join(missing)}")
    rows = status(REPO_ROOT, slug)
    for r in rows:
        if all_rows or r.state != "unused":
            typer.echo(f"{r.stage:<18} {r.state:<8} {r.detail}")
    unused = sum(r.state == "unused" for r in rows)
    if unused and not all_rows:
        typer.echo(f"({unused} stages unused by this project's route; --all lists them)")
    if any(r.state == "invalid" for r in rows):
        raise typer.Exit(1)


@app.command()
def voice(
    project: Annotated[str, typer.Argument(help="Project slug.")],
    force: Annotated[bool, typer.Option("--force", help="Regenerate every take (spends credits).")] = False,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Show what would be generated; no API calls.")
    ] = False,
) -> None:
    """C4: ElevenLabs takes per scene (cached), the best take per scene -> projects/<project>/voice.json."""
    import json as _json

    import yaml

    from create.voice import run_voice, text_hash
    from lens.schemas.create import Script

    slug = _slug(project)
    cfg = load_config()
    script = Script.model_validate(
        yaml.safe_load((REPO_ROOT / "projects" / slug / "script.yaml").read_text())
    )
    vc = cfg.create.voice
    todo = 0
    for sc in script.scenes:
        for n in range(1, vc.takes + 1):
            side = REPO_ROOT / "data" / "create" / slug / "voice" / f"{sc.id}-t{n}.json"
            cached = side.exists() and _json.loads(side.read_text()).get("text_hash") == text_hash(
                sc.spoken, vc
            )
            if force or not cached:
                todo += len(sc.spoken)
    typer.echo(f"{vc.voice_name} on {vc.model_id}, {vc.takes} takes per scene: {todo} characters to generate")
    if dry_run:
        return
    path = run_voice(REPO_ROOT, slug, cfg, force=force, log=typer.echo)
    typer.echo(f"wrote {path.relative_to(REPO_ROOT)}")


@app.command()
def timing(project: Annotated[str, typer.Argument(help="Project slug.")]) -> None:
    """C5: scene bounds and word clock -> projects/<project>/timeline.json (+ a narration preview)."""
    from create.project import voice_mode
    from create.timing import run_timing

    slug = _slug(project)
    if voice_mode(REPO_ROOT, slug) == "presenter":
        from create.footage.run import run_presenter_timing

        p, tl = run_presenter_timing(REPO_ROOT, slug, load_config())
        typer.echo(
            f"wrote {p.relative_to(REPO_ROOT)}: {len(tl.scenes)} scenes, {len(tl.words)} words, "
            f"{tl.total_s:.1f} s"
        )
        return
    path, timeline, brief, preview = run_timing(REPO_ROOT, slug, load_config().create.timing)
    typer.echo(
        f"wrote {path.relative_to(REPO_ROOT)}: {len(timeline.scenes)} scenes, {timeline.total_s:.1f} s"
    )
    if preview:
        typer.echo(f"narration preview: {preview.relative_to(REPO_ROOT)}")
    if not brief.length.min_s <= timeline.total_s <= brief.length.max_s:
        band = f"{brief.length.min_s:g}-{brief.length.max_s:g} s"
        typer.echo(f"note: {timeline.total_s:.1f} s is outside the brief's {band}")


@app.command()
def tokens(project: Annotated[str, typer.Argument(help="Project slug.")]) -> None:
    """C3: video tokens from the brand hand-off (contrast, glyphs, frame sizes) -> tokens.json."""
    from create.tokens import run_tokens, token_errors

    slug = _slug(project)
    cfg = load_config()
    try:
        path, toks = run_tokens(REPO_ROOT, slug, cfg)
    except BrandError as exc:
        typer.echo(str(exc))
        raise typer.Exit(1) from exc
    typer.echo(f"wrote {path.relative_to(REPO_ROOT)}")
    for p in toks.contrast:
        mark = "ok" if p.passes else ("exception" if p.exception else "FAIL")
        typer.echo(f"  {p.text:>17} on {p.bg:<15} {p.ratio:>5}:1 (needs {p.required:g}) {mark}")
    for g in toks.glyphs:
        missing = [c for c, ok in g.has.items() if not ok]
        typer.echo(f"  {g.family}: missing {' '.join(missing) or 'nothing'}")
    errors = token_errors(toks, cfg.create.design, brand_dir(REPO_ROOT, slug))
    for e in errors:
        typer.echo(f"  ERROR {e}")
    if errors:
        raise typer.Exit(1)


@app.command()
def build(project: Annotated[str, typer.Argument(help="Project slug.")]) -> None:
    """C8: one HyperFrames scene per storyboard scene, plus the local render bundle (GSAP, fonts)."""
    from create.build import run_build
    from create.bundle import run_bundle

    slug = _slug(project)
    for p in run_build(REPO_ROOT, slug):
        typer.echo(f"wrote {p.relative_to(REPO_ROOT)}")
    typer.echo(f"bundle: {run_bundle(REPO_ROOT, slug).relative_to(REPO_ROOT)}")


@app.command()
def direction(project: Annotated[str, typer.Argument(help="Project slug.")]) -> None:
    """C6 direction (motion route, ADR 0032): the pack a motion builder reads -> projects/<p>/direction.md."""
    from create.direction import run_direction

    slug = _slug(project)
    try:
        path = run_direction(REPO_ROOT, slug, load_config())
    except ValueError as exc:
        typer.echo(f"ERROR {exc}")
        raise typer.Exit(1) from exc
    typer.echo(f"wrote {path.relative_to(REPO_ROOT)}: {len(path.read_text().split())} words")


@app.command()
def grade(
    project: Annotated[str, typer.Argument(help="Project slug.")],
    lint_only: Annotated[
        bool, typer.Option("--lint-only", help="Bundle and run hyperframes check only (no render).")
    ] = False,
    snapshot: Annotated[
        str | None, typer.Option("--snapshot", help="Write frames at these seconds (comma-separated).")
    ] = None,
    on_record: Annotated[
        bool, typer.Option("--on-record", help="The main session's grade: not counted against the builder.")
    ] = False,
    new_round: Annotated[
        bool, typer.Option("--new-round", help="Reset the builder's budget for the next round, then stop.")
    ] = False,
) -> None:
    """C8 grade (motion route): render the build, run the checks -> projects/<p>/motion/grade.json.

    Full grades and snapshot frames are counted per build round against config create.motion.build."""
    from create.grade import BudgetError, prepare, run_grade, snapshots, spend
    from create.grade import new_round as reset

    slug = _slug(project)
    cfg = load_config()
    budget = cfg.create.motion.build
    if new_round:
        reset(REPO_ROOT, slug)
        typer.echo(f"new round: {budget.grades} full grades, {budget.snapshot_frames} frames")
        return
    try:
        if snapshot:
            left = spend(REPO_ROOT, slug, "frames", len(snapshot.split(",")), budget.snapshot_frames)
            typer.echo(f"frames left this round: {left}")
        elif not lint_only and not on_record:
            left = spend(REPO_ROOT, slug, "grades", 1, budget.grades)
            typer.echo(f"full grades left this round: {left}")
    except BudgetError as exc:
        typer.echo(f"STOP {exc}")
        raise typer.Exit(2) from exc
    if lint_only or snapshot:
        _, found = prepare(REPO_ROOT, slug, cfg)
        for f in found:
            typer.echo(f"{f.level:<5} {f.area:<9} {f.msg}")
        if snapshot:
            for p in snapshots(REPO_ROOT, slug, [float(t) for t in snapshot.split(",")], cfg.create.render):
                typer.echo(f"frame: {p.relative_to(REPO_ROOT)}")
        if any(f.level == "fail" for f in found):
            raise typer.Exit(1)
        return
    g = run_grade(REPO_ROOT, slug, cfg)
    for f in g.findings:
        at = f" @{f.t:g}s" if f.t is not None else ""
        typer.echo(f"{f.level:<5} {f.area:<9} {f.msg}{at}")
    m = g.measures
    typer.echo(
        f"{g.fails} fails, {g.warns} warns | transitions {m.transitions or 'none'} | moves {m.moves} | "
        f"sfx {m.sfx} | dead hold {m.dead_hold_s:g} s | longest idle {m.longest_idle_s:g} s | "
        f"min text {m.min_text_px}px | accent peak {m.max_accent_moments:g}"
    )
    typer.echo(
        f"review sheets: data/create/{slug}/motion/render/review/ | wrote projects/{slug}/motion/grade.json"
    )
    if not g.ok:
        raise typer.Exit(1)


@app.command()
def music(
    project: Annotated[str, typer.Argument(help="Project slug.")],
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Show the plan and estimated credits only.")
    ] = False,
) -> None:
    """C10 music: a bed built for the video (one Eleven Music chunk per scene) -> data/create/<p>/music/."""
    from create.music import plan_for, run_music

    slug = _slug(project)
    cfg = load_config()
    body, dur = plan_for(REPO_ROOT, slug, cfg)
    chunks = body["composition_plan"]["chunks"]
    typer.echo(
        f"{cfg.create.music.model_id}: {len(chunks)} chunks, {dur:g} s "
        f"(~{dur * cfg.create.music.credits_per_s:.0f} credits if not cached)"
    )
    for c in chunks:
        typer.echo(f"  {c['duration_ms'] / 1000:>6.2f} s  {c['text'].splitlines()[0]}")
    if dry_run:
        return
    bed, holes = run_music(REPO_ROOT, slug, cfg)
    typer.echo(f"wrote {bed.relative_to(REPO_ROOT)}")
    if holes:
        typer.echo(
            f"  DROPOUT at {', '.join(f'{h} s' for h in holes)}: patch or regenerate (phase2-plan C10 QA)"
        )
        raise typer.Exit(1)


@app.command()
def mix(project: Annotated[str, typer.Argument(help="Project slug.")]) -> None:
    """C12 mix (motion route): render + narration + ducked bed + SFX -> data/create/<p>/motion/final/."""
    from create.mix import run_mix

    slug = _slug(project)
    out, notes = run_mix(REPO_ROOT, slug, load_config())
    for n in notes:
        typer.echo(f"  note: {n}")
    typer.echo(f"wrote {out.relative_to(REPO_ROOT)}")


@app.command()
def sketches(project: Annotated[str, typer.Argument(help="Project slug.")]) -> None:
    """C7: the final frame of every built scene on one sheet (data/create/<project>/sketches/)."""
    from create.sketches import run_sketches

    slug = _slug(project)
    png, page = run_sketches(REPO_ROOT, slug, load_config().create.render)
    typer.echo(f"sheet: {png.relative_to(REPO_ROOT)}\npage: {page.relative_to(REPO_ROOT)}")


@app.command()
def audit(project: Annotated[str, typer.Argument(help="Project slug.")]) -> None:
    """C8 audit: text and logos of every built scene against the frame's safe area -> audit/safe-zones.json.

    Needs a browser (playwright is a dev dependency; CHROMIUM=<path> to pick one, see create/browser.py).
    """
    try:
        import playwright  # noqa: F401
    except ImportError as exc:
        typer.echo("needs playwright: uv run --with playwright create audit " + project)
        raise typer.Exit(1) from exc
    from create.audit import run_audit

    slug = _slug(project)
    path, report = run_audit(REPO_ROOT, slug, load_config())
    typer.echo(
        f"wrote {path.relative_to(REPO_ROOT)}: {report.frame}, {len(report.scenes)} scenes, "
        f"{report.boxes_checked} boxes, {len(report.issues)} issues"
    )
    for i in report.issues:
        typer.echo(f"  {i.scene} {i.t0:5.1f}-{i.t1:5.1f}s {i.problem:<16} {i.text[:40]!r} {i.box}")
    if not report.ok:
        raise typer.Exit(1)


@app.command()
def captions(project: Annotated[str, typer.Argument(help="Project slug.")]) -> None:
    """C11: caption groups from the timeline's words, by the frame's rules -> projects/<p>/captions.json."""
    from create.captions import run_captions

    slug = _slug(project)
    path, caps = run_captions(REPO_ROOT, slug, load_config())
    sizes = [len(g.words) for g in caps.groups]
    typer.echo(
        f"wrote {path.relative_to(REPO_ROOT)}: {len(caps.groups)} groups ({caps.frame}), "
        f"{min(sizes)}-{max(sizes)} words each"
    )


@app.command()
def burn(
    project: Annotated[str, typer.Argument(help="Project slug.")],
    plate: Annotated[Path, typer.Option("--plate", help="The finished video, at the timeline's fps.")],
    audio: Annotated[Path | None, typer.Option("--audio", help="Final audio (default: the plate's).")] = None,
    out: Annotated[
        Path | None, typer.Option("--out", help="Output MP4 (default: data/create/<p>/render/).")
    ] = None,
) -> None:
    """C12: burn the project's captions onto a plate with the brand's caption style (frame-exact)."""
    import yaml

    from create.burn import run_burn

    slug = _slug(project)
    cfg = load_config()
    brief = yaml.safe_load((REPO_ROOT / "projects" / slug / "brief.yaml").read_text())
    path = run_burn(
        REPO_ROOT,
        slug,
        plate,
        cfg.create.render,
        cfg.create.design.frames,
        audio,
        out,
        brief.get("language", "en"),
        cfg.create.design.caption_face_gap,
        cfg.create.design.caption_seam_gap_px,
    )
    typer.echo(f"wrote {path}")


@app.command()
def ingest(project: Annotated[str, typer.Argument(help="Project slug.")]) -> None:
    """F1: conform every take in data/create/<p>/footage/raw/ -> masters + projects/<p>/footage.json."""
    from create.footage.run import run_ingest

    slug = _slug(project)
    path, footage = run_ingest(REPO_ROOT, slug, load_config())
    typer.echo(f"wrote {path.relative_to(REPO_ROOT)}")
    for t in footage.takes:
        hdr = ", HDR tone-mapped to SDR" if t.hdr else ""
        typer.echo(
            f"  {t.id}: {t.width}x{t.height}, {t.duration_s:.1f} s ({t.source_fps} -> {footage.fps} fps){hdr}"
        )


@app.command()
def take(
    project: Annotated[str, typer.Argument(help="Project slug.")],
    video: Annotated[Path, typer.Option("--video", help="The take Robert sent (upload or download).")],
    term: Annotated[
        list[str] | None, typer.Option("--term", help="A name to recognise (repeatable).")
    ] = None,
    language: Annotated[
        str | None, typer.Option("--language", help="Force a language (default: the brief's, else detected).")
    ] = None,
    brand: Annotated[str, typer.Option("--brand", help="The provisional brief's brand.")] = "acme",
    approve: Annotated[
        bool, typer.Option("--approve", help="Robert already said how to cut ('cuts: all'): no cut page.")
    ] = False,
    keep: Annotated[
        str, typer.Option("--keep", help="With --approve: his times to keep in, e.g. 0:41,1:05.")
    ] = "",
) -> None:
    """Presenter start in one call (skill process-take): a provisional brief if none, the take into
    footage/raw, F1 ingest, F2 transcript, F3 cuts and the phone page (or, with --approve, his decision);
    prints what he says."""
    from create.footage.take import run_take, seconds

    if keep and not approve:
        raise typer.BadParameter("--keep goes with --approve (his decision); without it he taps the cut page")
    times = [seconds(t) for t in keep.split(",") if t.strip()]
    slug = _slug(project)
    lines = run_take(
        REPO_ROOT, slug, video, load_config(), term or [], language, _slug(brand), approve, times
    )
    for line in lines:
        typer.echo(line)


@app.command()
def transcribe(
    project: Annotated[str, typer.Argument(help="Project slug.")],
    term: Annotated[
        list[str] | None, typer.Option("--term", help="A name to recognise (repeatable).")
    ] = None,
) -> None:
    """F2: every word of every take, verbatim -> projects/<project>/transcript.json (ElevenLabs Scribe)."""
    from create.footage.run import run_transcript

    slug = _slug(project)
    path, t = run_transcript(REPO_ROOT, slug, load_config(), term or [])
    fillers = sum(w.kind == "filler" for w in t.words)
    typer.echo(
        f"wrote {path.relative_to(REPO_ROOT)}: {len(t.words)} words ({t.engine}, {t.language}), "
        f"{fillers} fillers"
    )


@app.command()
def cuts(
    project: Annotated[str, typer.Argument(help="Project slug.")],
    approve: Annotated[
        str | None, typer.Option("--approve", help="'all' or comma-separated cut ids.")
    ] = None,
    reject: Annotated[str, typer.Option("--reject", help="Comma-separated cut ids to keep in.")] = "",
    page: Annotated[
        bool,
        typer.Option(
            "--page", help="Also write a phone page to tap the decisions (data/create/<p>/cuts.html)."
        ),
    ] = False,
) -> None:
    """F3: propose cuts -> projects/<p>/cuts.json; with --approve, record Robert's decisions (human gate)."""
    import json as _json

    from create.footage.run import run_cuts, write_approvals
    from lens.schemas.create import Cuts

    slug = _slug(project)
    path = REPO_ROOT / "projects" / slug / "cuts.json"
    if approve is None:
        path, proposed = run_cuts(REPO_ROOT, slug, load_config())
        typer.echo(f"wrote {path.relative_to(REPO_ROOT)}: {len(proposed.proposals)} proposals")
        for c in proposed.proposals:
            typer.echo(f"  {c.id} {c.take} {c.start_s:7.2f}-{c.end_s:7.2f}s {c.kind:<8} {c.reason[:70]}")
        if page:
            from create.footage.cutpage import run_cut_page

            typer.echo(
                f"phone page: {run_cut_page(REPO_ROOT, slug)} (publish it, tap, send back the command)"
            )
        typer.echo(
            f"approve with: uv run create cuts {slug} --approve all  (or --approve c001,c003 --reject c002)"
        )
        return
    proposed = Cuts.model_validate(_json.loads(path.read_text()))
    ids: list[str] | str = "all" if approve == "all" else [x.strip() for x in approve.split(",") if x.strip()]
    rej = [x.strip() for x in reject.split(",") if x.strip()]
    known = {c.id for c in proposed.proposals}
    unknown = sorted(((set(ids) if ids != "all" else set()) | set(rej)) - known)
    if unknown:
        raise typer.BadParameter(f"unknown cut ids: {', '.join(unknown)}")
    out = write_approvals(REPO_ROOT, slug, ids, rej)
    typer.echo(f"wrote {out.relative_to(REPO_ROOT)}")


@app.command()
def edl(project: Annotated[str, typer.Argument(help="Project slug.")]) -> None:
    """F4: apply the approved cuts -> projects/<project>/edl.json (frame-exact segments)."""
    from create.footage.run import run_edl

    slug = _slug(project)
    path, e = run_edl(REPO_ROOT, slug, load_config())
    typer.echo(
        f"wrote {path.relative_to(REPO_ROOT)}: {len(e.segments)} segments, "
        f"{e.duration_frames / e.fps:.1f} s, {len(e.applied)} cuts"
    )


@app.command()
def edit(project: Annotated[str, typer.Argument(help="Project slug.")]) -> None:
    """F6: render the edited presenter video -> data/create/<project>/footage/edited/."""
    from create.footage.run import run_edit

    slug = _slug(project)
    for path in run_edit(REPO_ROOT, slug, load_config()):
        typer.echo(f"wrote {path.relative_to(REPO_ROOT)}")


@app.command()
def reframe(project: Annotated[str, typer.Argument(help="Project slug.")]) -> None:
    """F5: face-aware crops per edited segment (full frame and bubble) -> projects/<project>/framing.json."""
    import yaml

    from create.footage.reframe import run_reframe

    slug = _slug(project)
    brief = yaml.safe_load((REPO_ROOT / "projects" / slug / "brief.yaml").read_text())
    path, f = run_reframe(REPO_ROOT, slug, load_config(), brief["destination"])
    faces = sum(s.face is not None for s in f.segments)
    typer.echo(f"wrote {path.relative_to(REPO_ROOT)}: {len(f.segments)} segments ({faces} with a face)")


@app.command()
def pixel(
    sprite: Annotated[str, typer.Argument(help="kitten, fred or fishes.")],
    out: Annotated[Path, typer.Option("--out", help="Folder for the previews.")] = Path("data/create/_pixel"),
    anims: Annotated[
        str | None, typer.Option("--anims", help="Comma-separated animations (default: all).")
    ] = None,
    acc: Annotated[str, typer.Option("--acc", help="Fred's accessories, comma-separated.")] = "",
    scale: Annotated[int, typer.Option("--scale", help="Pixels per sprite pixel.")] = 10,
) -> None:
    """Pixel-art sprites (create/pixel, skill pixel-art): for each animation a frame sheet, an onion skin, a
    GIF and an MP4 loop, for reviews. Nothing here is committed (media rule)."""
    from create.pixel import fishes, fred, kitten
    from create.pixel.core import onion, save_gif, save_mp4, sheet

    mod: Any = {"kitten": kitten, "fred": fred, "fishes": fishes}[sprite]
    names = anims.split(",") if anims else list(mod.FPS)
    out.mkdir(parents=True, exist_ok=True)
    for a in names:
        frames = mod.frames(a, set(filter(None, acc.split(",")))) if sprite == "fred" else mod.frames(a)
        stem = out / f"{sprite}-{a}"
        sheet(frames, scale // 2 or 1).save(f"{stem}-sheet.png")
        onion(frames, scale // 2 or 1).save(f"{stem}-onion.png")
        save_gif(frames, f"{stem}.gif", scale, mod.FPS[a])
        save_mp4(frames, f"{stem}.mp4", scale, mod.FPS[a])
        typer.echo(f"wrote {stem}.gif / .mp4 ({len(frames)} frames @ {mod.FPS[a]} fps)")


@app.command()
def lab(
    spec: Annotated[Path, typer.Argument(help="Lab spec (docs/lab/<name>.yaml).")],
    photo: Annotated[
        Path, typer.Option("--photo", help="A photo of someone sitting (media: never committed).")
    ],
    draft: Annotated[
        bool, typer.Option("--draft", help="Render at the draft scale (review rounds).")
    ] = False,
    preview: Annotated[
        str | None, typer.Option("--preview", help="Comma-separated seconds: a contact sheet, no render.")
    ] = None,
    matte_: Annotated[
        bool, typer.Option("--matte", help="Cut the presenter out where the plan needs it.")
    ] = False,
    force: Annotated[bool, typer.Option("--force", help="Render even if the plan check has errors.")] = False,
) -> None:
    """Reel lab (ADR 0029): a test presenter video from a photo, an ElevenLabs voice and a plan, to practise
    props, effects and motion. Writes data/lab/<name>/ and data/lab/out/<name>.mp4."""
    import shutil

    from create import lab as lab_mod
    from create.footage.reel import build, run_reel
    from create.footage.reel import preview as contact_sheet

    cfg = load_config()
    root = lab_mod.build(spec, photo, cfg)
    name = yaml_load(spec)["name"]
    if matte_:
        from create.footage.matte import run_matte

        run_matte(root, name, cfg)
    out_dir = REPO_ROOT / "data" / "lab" / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    if preview:
        comp, _ = build(root, name, cfg)
        times = [float(x) for x in preview.split(",")]
        sheet = contact_sheet(comp, times, out_dir / f"{name}-sheet.jpg", cols=min(4, len(times)))
        typer.echo(f"wrote {sheet}")
        return
    video = run_reel(root, name, cfg, force=force, draft=draft)
    target = out_dir / f"{name}{'-draft' if draft else ''}.mp4"
    shutil.copy(video, target)
    typer.echo(f"wrote {target}")
    data = json.loads((root / "data" / "create" / name / "render" / "reel" / "reel-data.json").read_text())
    scale = cfg.create.footage.reel.draft_scale if draft else 1.0
    study_out = out_dir / f"{name}-study.jpg"
    st = lab_mod.study(target, data, study_out, scale=scale, per=cfg.create.lab.study_rows)
    typer.echo(f"wrote {st}")
    if bad := lab_mod.green_edges(target):
        typer.echo(f"WARNING green edge in {len(bad)} frames, from {bad[0]} s (a crop larger than its input)")


def yaml_load(path: Path) -> dict[str, Any]:
    import yaml

    data: dict[str, Any] = yaml.safe_load(path.read_text())
    return data


@app.command()
def matte(
    project: Annotated[str, typer.Argument(help="Project slug.")],
    plan: Annotated[
        Path | None, typer.Option("--plan", help="Reel plan (default: projects/<p>/reel.yaml).")
    ] = None,
) -> None:
    """F7: cut the presenter out of the edited video (HyperFrames remove-background, a local model) where
    the reel plan needs it: props behind the presenter, anime backgrounds (ADR 0027). Faster on a Mac."""
    from create.footage.matte import run_matte

    slug = _slug(project)
    written = run_matte(REPO_ROOT, slug, load_config(), plan)
    for p in written:
        typer.echo(f"wrote {p.relative_to(REPO_ROOT)}")
    if not written:
        typer.echo("matte: nothing new to cut out")


@app.command()
def pip(
    project: Annotated[str, typer.Argument(help="Project slug.")],
    background: Annotated[
        Path, typer.Option("--background", help="What plays behind (render, screen recording).")
    ],
    corner: Annotated[
        str | None, typer.Option("--corner", help="br | bl | tr | tl (default: layout.yaml)")
    ] = None,
    out: Annotated[
        Path | None, typer.Option("--out", help="Output MP4 (default: under data/create/).")
    ] = None,
    fit: Annotated[str, typer.Option("--fit", help="auto | cover (fill, crop) | contain (whole)")] = "auto",
) -> None:
    """Presenter layouts over a background: per scene full, corner bubble or off (projects/<p>/layout.yaml;
    without it the bubble throughout). Run after `create edit` (and `create reframe` to follow the face)."""
    import yaml

    from create.footage.layout import run_layout

    if corner is not None and corner not in ("br", "bl", "tr", "tl"):
        raise typer.BadParameter("corner must be br, bl, tr or tl")
    if fit not in ("auto", "cover", "contain"):
        raise typer.BadParameter("fit must be auto, cover or contain")
    slug = _slug(project)
    brief = yaml.safe_load((REPO_ROOT / "projects" / slug / "brief.yaml").read_text())
    lang = brief.get("language", "en")
    path = run_layout(REPO_ROOT, slug, background, load_config(), out, lang, corner, fit)  # type: ignore[arg-type]
    typer.echo(f"wrote {path}")


@app.command()
def overlay(
    project: Annotated[str, typer.Argument(help="Project slug.")],
    out: Annotated[
        Path | None, typer.Option("--out", help="Output MP4 (default: under data/create/).")
    ] = None,
) -> None:
    """Graphics over the presenter's own video from projects/<p>/overlays.yaml, placed clear of the face and
    the captions (run after `create edit`; `create reframe` makes them follow the face)."""
    import yaml

    from create.footage.overlays import run_overlay

    slug = _slug(project)
    brief = yaml.safe_load((REPO_ROOT / "projects" / slug / "brief.yaml").read_text())
    path = run_overlay(REPO_ROOT, slug, load_config(), out, brief.get("language", "en"))
    typer.echo(f"wrote {path}")


@app.command()
def cover(
    project: Annotated[str, typer.Argument(help="Project slug.")],
    title: Annotated[str, typer.Option("--title", help="The hook; **word** takes the accent.")],
    video: Annotated[
        Path | None, typer.Option("--video", help="Frame source (default: the clean edit).")
    ] = None,
    at: Annotated[float, typer.Option("--at", help="Seconds into the video for the frame.")] = 1.0,
    tag: Annotated[
        str, typer.Option("--tag", help="A small label under the title (--split: the kicker pill above it).")
    ] = "",
    out: Annotated[Path | None, typer.Option("--out", help="Output PNG.")] = None,
    split: Annotated[
        bool,
        typer.Option(
            "--split",
            help="Presenter video on a split base: title above the seam, his frame untouched below "
            "(default --video: the base render).",
        ),
    ] = False,
    sub: Annotated[str, typer.Option("--sub", help="--split: one line under the title.")] = "",
    icon: Annotated[
        Path | None, typer.Option("--icon", help="--split: a logo or icon in the kicker pill.")
    ] = None,
    onto: Annotated[
        Path | None,
        typer.Option("--onto", help="Also write <video>-cover.mp4: this video with the cover as frame 0."),
    ] = None,
    plan: Annotated[
        Path | None,
        typer.Option("--plan", help="--split: the plan whose seam to use (default reel-base.yaml)."),
    ] = None,
) -> None:
    """A cover image: a frame with the hook inside the cover-safe area (it survives grid crops). Presenter
    videos with a panel or split layout take `--split` (never a title on his face)."""
    from create.cover import onto_first_frame, run_cover, run_split_cover

    cfg = load_config()
    if split:
        path = run_split_cover(REPO_ROOT, _slug(project), video, title, cfg, at, tag, sub, icon, out, plan)
    else:
        path = run_cover(REPO_ROOT, _slug(project), video, title, cfg, at, tag, out)
    typer.echo(f"wrote {path}")
    if onto is not None:
        typer.echo(f"wrote {onto_first_frame(path, onto, cfg.create.footage.panel.composite_crf)}")


@app.command()
def prep(project: Annotated[str, typer.Argument(help="Project slug.")]) -> None:
    """Presenter footage after the cut approvals: edl -> reframe -> timing -> edit -> captions, in order (what
    `create reel` needs). Each step is the same as its own command; stops at the first failure."""
    import yaml

    from create.captions import run_captions
    from create.footage.reframe import run_reframe
    from create.footage.run import run_edit, run_edl, run_presenter_timing

    slug = _slug(project)
    cfg = load_config()
    brief = yaml.safe_load((REPO_ROOT / "projects" / slug / "brief.yaml").read_text())
    _, e = run_edl(REPO_ROOT, slug, cfg)
    typer.echo(f"edl: {len(e.segments)} segments, {e.duration_frames / e.fps:.1f} s")
    _, f = run_reframe(REPO_ROOT, slug, cfg, brief["destination"])
    typer.echo(
        f"reframe: {len(f.segments)} segments, {sum(s.face is not None for s in f.segments)} with a face"
    )
    _, tl = run_presenter_timing(REPO_ROOT, slug, cfg)
    typer.echo(f"timing: {len(tl.scenes)} scenes, {len(tl.words)} words")
    for path in run_edit(REPO_ROOT, slug, cfg):
        typer.echo(f"edit: {path}")
    _, caps = run_captions(REPO_ROOT, slug, cfg)
    typer.echo(f"captions: {len(caps.groups)} groups. Next: create words {slug}, then a reel plan")


@app.command()
def words(
    project: Annotated[str, typer.Argument(help="Project slug.")],
    times: Annotated[
        bool, typer.Option("--times", help="Each word's start in seconds too (i:text@s), for a panel page.")
    ] = False,
) -> None:
    """The edited take's words with their indexes and times, one line per scene, plus the cuts: what a reel
    plan (projects/<p>/reel.yaml) is written against (word indexes, never times). A panel page cues on
    seconds: `--times` prints them, so nobody reads timeline.json."""
    import json

    from lens.schemas.create import Edl, Timeline

    base = REPO_ROOT / "projects" / _slug(project)
    tl = Timeline.model_validate(json.loads((base / "timeline.json").read_text()))
    for sc in tl.scenes:
        ws = [w for w in tl.words if w.scene == sc.scene]
        said = " ".join(f"{w.i}:{w.text}" + (f"@{w.start_s:.2f}" if times else "") for w in ws)
        typer.echo(f"{sc.scene} {sc.start_s:5.1f}-{sc.end_s:5.1f}s  {said}")
    edl_p = base / "edl.json"
    if edl_p.exists():
        edl = Edl.model_validate(json.loads(edl_p.read_text()))
        cuts = [f"{s.rec_in / edl.fps:.1f}" for s in edl.segments[1:]]
        typer.echo(f"cuts (s): {' '.join(cuts)}")


@app.command()
def reel(
    project: Annotated[str, typer.Argument(help="Project slug.")],
    plan: Annotated[
        Path | None, typer.Option("--plan", help="Reel plan (default: projects/<p>/reel.yaml).")
    ] = None,
    out: Annotated[
        Path | None, typer.Option("--out", help="Output MP4 (default: under data/create/).")
    ] = None,
    preview: Annotated[
        str | None,
        typer.Option("--preview", help="Comma-separated seconds: write a contact sheet, no render."),
    ] = None,
    check: Annotated[
        bool, typer.Option("--check", help="Check the plan and where every widget lands, no render.")
    ] = False,
    force: Annotated[bool, typer.Option("--force", help="Render even if the plan has check errors.")] = False,
    draft: Annotated[
        bool,
        typer.Option("--draft", help="Render smaller and faster, for review rounds (not a deliverable)."),
    ] = False,
) -> None:
    """The whole presenter video in one render from projects/<p>/reel.yaml: layouts, animated widgets on the
    presenter's words, captions clear of the face and chest, a push-in per shot and a grade (after `create
    edit`, `create reframe` and `create captions`). Run `--check` before rendering; check the video with
    `create qa --video`."""
    from create.footage.reel import build, run_reel
    from create.footage.reel import preview as contact_sheet

    slug = _slug(project)
    if check:
        from create.browser import HINT, available
        from create.footage.reel_check import run_check

        if not available():
            raise typer.BadParameter(HINT)
        found = run_check(REPO_ROOT, slug, load_config(), plan)
        shown: dict[str, int] = {}
        for f in found:  # every error; at most three warnings per rule (the rest counted)
            shown[f.rule] = shown.get(f.rule, 0) + 1
            if f.level == "error" or shown[f.rule] <= 3:
                typer.echo(f.line())
        hidden = {
            r: n - 3
            for r, n in shown.items()
            if n > 3 and all(f.level == "warn" for f in found if f.rule == r)
        }
        if hidden:
            typer.echo("more warnings: " + ", ".join(f"{r} +{n}" for r, n in hidden.items()))
        errors = sum(f.level == "error" for f in found)
        typer.echo(f"{errors} errors, {len(found) - errors} warnings")
        if errors:
            raise typer.Exit(1)
        return
    if preview:
        comp, _ = build(REPO_ROOT, slug, load_config(), plan)
        sheet = out or comp / "preview.png"
        typer.echo(f"wrote {contact_sheet(comp, [float(t) for t in preview.split(',')], sheet)}")
        return
    typer.echo(f"wrote {run_reel(REPO_ROOT, slug, load_config(), plan, out, force, draft)}")


@app.command()
def panel(
    project: Annotated[str, typer.Argument(help="Project slug.")],
    base: Annotated[
        Path | None,
        typer.Option("--base", help="Reel render to lay the panel over (its plan says `panel: true`)."),
    ] = None,
    out: Annotated[
        Path | None, typer.Option("--out", help="Output MP4 (default: data/create/<p>/render/<p>-panel.mp4).")
    ] = None,
    stills: Annotated[
        str | None,
        typer.Option("--stills", help="Comma-separated seconds: PNG stills of the panel only, for a review."),
    ] = None,
    init: Annotated[
        bool,
        typer.Option("--init", help="The starter page (if none yet) and the assets: GSAP, fonts, logos."),
    ] = False,
    font: Annotated[
        list[str] | None, typer.Option("--font", help="--init: an extra Google font family (repeatable).")
    ] = None,
    assets: Annotated[
        bool,
        typer.Option("--assets", help="List the assets: size, light or dark, and files that are not images."),
    ] = False,
) -> None:
    """The bespoke panel (ADR 0034, skill build-panel): step projects/<p>/panel/index.html frame by frame
    (assets in data/create/<p>/panel/assets/) and lay it over a reel render. Check the result with `create qa`
    and `create review`."""
    from create.footage.panel import asset_lines, composite, init_panel, panel_paths, render_panel
    from lens.schemas.create import Timeline

    slug = _slug(project)
    if init and (stills or base):
        raise typer.BadParameter("--init sets the panel up: run --stills or --base after it")
    if init:
        for line in init_panel(REPO_ROOT, slug, font or []):
            typer.echo(f"wrote {line}")
        return
    if assets:
        for line in asset_lines(panel_paths(REPO_ROOT, slug)[1] / "assets"):
            typer.echo(line)
        return
    cfg = load_config()
    pc = cfg.create.footage.panel
    tl_path = REPO_ROOT / "projects" / slug / "timeline.json"
    timeline = Timeline.model_validate(json.loads(tl_path.read_text()))
    if stills:
        times = [float(t) for t in stills.split(",")]
        if len(times) > pc.max_stills:
            raise typer.BadParameter(f"{len(times)} stills: at most {pc.max_stills} per sheet (run it twice)")
        folder = render_panel(REPO_ROOT, slug, pc, timeline.fps, 0, times)
        typer.echo(f"wrote {folder}/sheet.png ({len(times)} stills, stamped; one image for the reviewer)")
        typer.echo(
            f"budget: {pc.review_sheets} images a round (a sheet or one t<time>.png), {pc.max_stills} a sheet"
        )
        return
    if base is None:
        raise typer.BadParameter("--base: the reel render (plan with `panel: true`) to lay the panel over")
    mp4 = render_panel(REPO_ROOT, slug, pc, timeline.fps, timeline.total_s)
    target = out or REPO_ROOT / "data" / "create" / slug / "render" / f"{slug}-panel.mp4"
    typer.echo(f"wrote {composite(base, mp4, target, pc.composite_crf)}")


@app.command()
def edits(
    project: Annotated[str, typer.Argument(help="Project slug.")],
    page: Annotated[
        bool, typer.Option("--page", help="Write the edit page (data/create/<p>/edit.html) to send Robert.")
    ] = False,
    plan: Annotated[
        Path | None, typer.Option("--plan", help="The plan of the version he watched (default reel.yaml).")
    ] = None,
    video: Annotated[
        Path | None, typer.Option("--video", help="The render he watched, embedded shrunk in the page.")
    ] = None,
    apply: Annotated[
        str | None, typer.Option("--apply", help="The page's answer: a file with the pasted text, or '-'.")
    ] = None,
) -> None:
    """Robert's own corrections: --page writes a phone page (crop per shot, the plan's zooms, notes on a
    time); --apply stores its answer in projects/<p>/edits.yaml, which reframe and reel use as given."""
    import sys

    from create.footage.edits import load_edits, merge, read_answer, write_edits

    slug = _slug(project)
    if page:
        from create.footage.editpage import run_edit_page

        path, warnings = run_edit_page(REPO_ROOT, slug, load_config(), plan, video)
        for w in warnings:
            typer.echo(f"warning: {w}")
        typer.echo(f"edit page: {path} ({path.stat().st_size / 1e6:.1f} MB; publish it, send the link)")
    if apply is None:
        if not page:
            raise typer.BadParameter("use --page and/or --apply")
        return
    sent = read_answer(sys.stdin.read() if apply == "-" else Path(apply).read_text())
    if sent["edits"] != slug:
        raise typer.BadParameter(f"this answer is for {sent['edits']!r}, not {slug!r}")
    base = REPO_ROOT / "projects" / slug
    path = write_edits(base, merge(load_edits(base), sent))
    typer.echo(f"wrote {path.relative_to(REPO_ROOT)}")
    plan_arg = f" --plan projects/{slug}/{sent['plan']}" if sent.get("plan") else ""
    if sent.get("shots"):
        typer.echo(
            f"  {len(sent['shots'])} shot crops: run create reframe {slug}, create edit {slug}, then the reel"
        )
    if any(k in sent for k in ("push", "drop_punches", "zooms")):
        typer.echo(f"  zoom changes for {sent.get('plan')}: applied by create reel{plan_arg}")
    for n in sent.get("notes", []):
        typer.echo(f"  note {n['t']:.1f}s: {n['text']}")


@app.command()
def review(
    project: Annotated[str, typer.Argument(help="Project slug.")],
    video: Annotated[Path, typer.Option("--video", help="The finished video (from create reel).")],
    at: Annotated[
        str | None,
        typer.Option("--at", help="Comma-separated settled seconds: a frame-exact sheet (panel videos)."),
    ] = None,
) -> None:
    """Contact sheet, motion strips and a reviewer brief for a fresh-eyes review of a finished video
    (data/create/<p>/review/<video>/; the review-reel skill reads only these)."""
    import json

    from create.footage.review import run_review
    from lens.schemas.create import Tokens

    slug = _slug(project)
    cfg = load_config()
    tokens = Tokens.model_validate(json.loads((REPO_ROOT / "projects" / slug / "tokens.json").read_text()))
    times = [float(t) for t in at.split(",")] if at else None
    out = run_review(REPO_ROOT, slug, video, cfg.create.design.frames[tokens.frame], at=times)
    typer.echo(
        f"wrote {out}/brief.md (with sheet.png{', settled.png' if times else ''}, motion.png if widgets)"
    )


@app.command()
def qa(
    project: Annotated[str, typer.Argument(help="Project slug.")],
    video: Annotated[Path, typer.Option("--video", help="The finished video (from create burn).")],
    verbose: Annotated[bool, typer.Option("--verbose", help="Print every check, not only failures.")] = False,
) -> None:
    """C13: check a finished video against its destination (format, loudness, hook, pacing, captions,
    graphics) -> projects/<project>/qa/<video>.json. Exit code 1 if anything fails."""
    from create.qa import run_qa

    slug = _slug(project)
    path, report = run_qa(REPO_ROOT, slug, video, load_config())
    for c in report.checks:
        if verbose or not c.ok:  # short by default: the passing checks are in the report file
            mark = "ok  " if c.ok else "FAIL"
            typer.echo(f"  {mark} {c.id:<20} {c.value:<28} (want {c.target}) {c.note}")
    passed = sum(c.ok for c in report.checks)
    typer.echo(f"wrote {path}: {passed}/{len(report.checks)} checks pass")
    if not report.ok:
        raise typer.Exit(1)
