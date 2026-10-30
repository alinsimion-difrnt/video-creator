from lens.stages import STAGES, Runner, Stage, check_dag, is_write_allowed, templates_overlap


def _stage(sid: str, after=(), reads=(), writes=()) -> Stage:
    return Stage(sid, Runner.CODE, tuple(after), tuple(reads), tuple(writes), "M0", "test")


def test_registry_is_valid():
    assert check_dag(STAGES) == []


def test_detects_cycle():
    errors = check_dag([_stage("a", after=["b"]), _stage("b", after=["a"])])
    assert any(e.startswith("cycle") for e in errors)


def test_detects_unknown_dependency():
    assert any("unknown dependency" in e for e in check_dag([_stage("a", after=["nope"])]))


def test_detects_overlapping_writes():
    errors = check_dag(
        [
            _stage("a", writes=["videos/{video}/a1.json"]),
            _stage("b", writes=["videos/**"]),
        ]
    )
    assert any("write overlap" in e for e in errors)


def test_detects_case_insensitive_collision():
    # Acme.wav vs Acme.wav overwrote each other in v1 (handoff section 5.14).
    assert templates_overlap("assets/acme.wav", "assets/Acme.wav")
    errors = check_dag([_stage("a", writes=["out/acme.wav"]), _stage("b", writes=["out/Acme.wav"])])
    assert any("not lowercase" in e for e in errors)
    assert any("write overlap" in e for e in errors)


def test_detects_undeclared_read():
    errors = check_dag([_stage("a", writes=["x/{video}.json"]), _stage("b", reads=["x/{video}.json"])])
    assert any("no upstream stage writes" in e for e in errors)


def test_read_from_upstream_ok():
    stages = [_stage("a", writes=["x/{video}.json"]), _stage("b", after=["a"], reads=["x/{video}.json"])]
    assert check_dag(stages) == []


def test_non_overlapping_siblings():
    assert not templates_overlap("videos/{video}/events/{eid}.a2.json", "videos/{video}/a1.json")
    assert not templates_overlap(
        "runs/{run_id}/progress/a1-{task}.json", "runs/{run_id}/progress/a2-{task}.json"
    )
    assert not templates_overlap("reports/compare/{video}/{date}.html", "reports/compare/{video}/fixes.json")


def test_is_write_allowed():
    a2 = ["a2_annotate_event"]
    assert is_write_allowed("videos/linear-initiatives-2025/events/e012.a2.json", a2)
    assert not is_write_allowed("videos/linear-initiatives-2025/a1.json", a2)
    assert not is_write_allowed("videos/Linear/events/e012.a2.json", a2)  # not lowercase
    assert is_write_allowed("corpus/patterns/stagger_list_reveal.md", ["a3_pattern_cards"])
    assert not is_write_allowed("lens/cli.py", ["a3_pattern_cards"])
