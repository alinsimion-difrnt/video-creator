"""study/tiktok/sources.py: picking the study's videos."""

from __future__ import annotations

from study.tiktok.config import Select
from study.tiktok.sources import Candidate, looks_english, select

NOW = 1_800_000_000.0
DAY = 86400


def cand(i: int, topic: str, handle: str, likes: int, **kw: object) -> Candidate:
    base = dict(
        id=str(i),
        handle=handle,
        topic=topic,
        found="x",
        caption="how to rank in chatgpt",
        duration_s=45.0,
        plays=likes * 10,
        likes=likes,
        create_time=int(NOW - 30 * DAY),
    )
    base.update(kw)
    return Candidate(**base)  # type: ignore[arg-type]


def test_looks_english() -> None:
    assert looks_english("How to rank in ChatGPT #seo #geo")
    assert looks_english("#ai #claudecode")
    assert not looks_english("Cómo usar la IA para tu negocio y más")  # Spanish: no common English word
    assert not looks_english("Как использовать нейросеть")
    assert not looks_english("ChatGPT Prompt Trend Foto zeige mir dein Foto in den Kommentaren")


def test_topic_of_keeps_matching_topic_moves_or_drops() -> None:
    from study.tiktok.config import load
    from study.tiktok.sources import topic_of

    kw = load().select.topic_keywords
    assert topic_of(cand(1, "claude", "a", 1, caption="5 Claude Code plugins"), kw) == "claude"
    assert topic_of(cand(2, "claude", "a", 1, caption="SEO for beginners: keywords"), kw) == "seo"
    assert topic_of(cand(3, "claude", "a", 1, caption="#dogsoftiktok #doglover"), kw) is None
    ex = load().select.exclude
    assert topic_of(cand(4, "geo", "a", 1, caption="I miss geo #geo #geologyshi"), kw, ex) is None
    assert topic_of(cand(5, "geo", "a", 1, caption="SEO is dead, the future is GEO"), kw, ex) == "geo"
    assert not looks_english("Optimize your SEO para paboran ka ni TikTok")


def test_select_balances_topics_caps_creators_and_filters() -> None:
    kw = {"ai": "ai|chatgpt", "seo": "seo|rank", "geo": "chatgpt|rank"}
    cfg = Select(
        total=5,
        per_topic=2,
        max_per_creator=2,
        min_seconds=12,
        max_seconds=180,
        max_age_days=365,
        min_likes=50,
        exclude="",
        topic_keywords=kw,
    )
    cands = [
        cand(1, "ai", "a", 900),
        cand(2, "ai", "a", 800),
        cand(3, "ai", "a", 700),  # third from creator a: capped
        cand(4, "ai", "b", 600),  # ai is full after two
        cand(5, "seo", "c", 500),
        cand(6, "seo", "d", 400, duration_s=300.0),  # too long
        cand(7, "seo", "e", 300, create_time=int(NOW - 800 * DAY)),  # too old
        cand(8, "geo", "f", 200, caption="Как использовать"),  # not English
        cand(9, "geo", "g", 100),
        cand(10, "geo", "h", 20),  # too few likes
    ]
    got = [c.id for c in select(cands, cfg, NOW)]
    assert got[:4] == ["1", "2", "5", "9"]  # per topic first, by likes
    assert got[4] == "4"  # then the best left over, any topic
    assert len(got) == 5
