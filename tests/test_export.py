"""S10 exports: the leak check refuses corpus brands, ids and text; ranges carry the measured spread."""

from __future__ import annotations

from lens.export import leaks, rng
from lens.schemas.corpus import Stat


def test_leaks_finds_brands_ids_and_text_case_insensitively():
    bad = ["Acme", "acme-intro-video", "Ship faster with fewer meetings"]
    texts = {
        "a.json": '{"summary": "a card pops in"}',
        "b.md": "Used by ACME in its launch",
        "c.md": "see acme-intro-video e004",
        "d.md": "the line ship faster with fewer meetings appears",
        "e.md": "acmesoft is a different word",
    }
    assert leaks(texts, bad) == [
        "b.md: 'Acme'",
        "c.md: 'Acme'",  # the id contains the brand too
        "c.md: 'acme-intro-video'",
        "d.md: 'Ship faster with fewer meetings'",
    ]


def test_word_brands_count_only_as_names_mid_sentence():
    texts = {
        "ease.md": "Easing: linear 12%. Linear tweens hold speed.",
        "title.md": "# Cursor Leads The Demo\n- [Cursor Leads](x.md)",
        "name.md": "as the team at Linear did in its launch",
        "pointer.md": "the cursor clicks the button",
    }
    assert leaks(texts, ["Linear", "Cursor"], ["Linear", "Cursor"]) == ["name.md: 'Linear'"]


def test_range_is_the_interquartile_spread():
    s = Stat(n=9, videos=3, weight=4.0, median=500.0, p25=400.0, p75=650.0, ci=(450.0, 560.0))
    r = rng(s)
    assert (r.median, r.low, r.high, r.n, r.videos) == (500.0, 400.0, 650.0, 9, 3)
    assert rng(None).median is None and rng(None).n == 0
