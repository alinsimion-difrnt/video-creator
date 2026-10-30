"""`reports/compare/<id>/metrics.json`: where a video sits against targets, and what to fix."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from lens.schemas.common import Provenance, Slug, Strict

Section = Literal["voice", "sound", "motion", "rhythm"]


class MetricResult(Strict):
    id: Slug
    value: float | None
    unit: str
    min: float | None  # targets-only: the target; corpus: the cohort's 25th percentile
    max: float | None  # targets-only: the target; corpus: the cohort's 75th percentile
    status: Literal["pass", "fail", "n/a"]
    gap: float | None  # targets-only: in units; corpus: in band widths (75th - 25th percentile)
    source: str
    note: str | None
    section: Section | None = None  # corpus mode
    percentile: float | None = Field(default=None, ge=0, le=100)  # weighted, among the cohort
    cohort_median: float | None = None
    cohort_n: int | None = None


class Fix(Strict):
    metric: Slug
    problem: str
    evidence: list[str]
    target: str
    change: str
    effort: Literal["S", "M", "L"]
    severity: float = Field(ge=0)
    timestamps_s: list[float] = Field(default_factory=list)  # where in the video (A4, corpus mode)
    refs: list[str] = Field(default_factory=list)  # pattern:<id> | archetype:<id> | token:<path> (A4)


class BaselineCheck(Strict):
    name: str
    measured: float | None
    expected: float
    tolerance: float = Field(ge=0)
    ok: bool


class CompareReport(Strict):
    provenance: Provenance
    video_id: Slug
    mode: Literal["targets-only", "corpus"]
    destination: Slug
    metrics: list[MetricResult]
    fixes: list[Fix] = Field(max_length=10)
    baseline: list[BaselineCheck] | None
    not_yet_measured: list[str]
    cohort: list[str] = Field(default_factory=list)  # corpus mode: the videos compared against


class FixesFile(Strict):
    """`reports/compare/<id>/fixes.json` (A4 compare-fixes): Claude's top fixes from the corpus metrics."""

    provenance: Provenance
    video: Slug
    fixes: list[Fix] = Field(min_length=1, max_length=10)
