"""Pydantic models: the file interface is the contract (BUILD_PLAN section 2.4)."""

from pydantic import BaseModel

from lens.schemas.annotation import A1File, A2File
from lens.schemas.cards import ArchetypeCard, PatternCard
from lens.schemas.common import Provenance
from lens.schemas.compare import CompareReport, FixesFile
from lens.schemas.config import LensConfig
from lens.schemas.corpus import MotionStats, PacingStats, PatternsFile, SoundStats
from lens.schemas.create import Brief, Script, Storyboard, Timeline, Tokens, Voice
from lens.schemas.eval import EvalFile
from lens.schemas.evidence import CandidatesFile
from lens.schemas.exports import (
    ArchetypesExport,
    MotionTokens,
    PacingSpec,
    PatternsExport,
    SoundSpec,
    VoiceSpec,
)
from lens.schemas.gold import GoldFile
from lens.schemas.measure import MeasureFile
from lens.schemas.packets import Anchors, EventFacts, PacketManifest
from lens.schemas.record import RecordFile
from lens.schemas.scenes import SceneBatch, ScenesFile
from lens.schemas.signals import SignalsSummary
from lens.schemas.sources import SourceEntry, SourcesFile
from lens.schemas.taxonomy import Taxonomy
from lens.schemas.video import Palette, VideoMeta

# Exported as exports/schemas/<name>.schema.json and used by `lens validate`.
SCHEMAS: dict[str, type[BaseModel]] = {
    "provenance": Provenance,
    "lens-config": LensConfig,
    "sources": SourcesFile,
    "taxonomy": Taxonomy,
    "video-meta": VideoMeta,
    "palette": Palette,
    "signals-summary": SignalsSummary,
    "compare-report": CompareReport,
    "candidates": CandidatesFile,
    "anchors": Anchors,
    "event-facts": EventFacts,
    "packet-manifest": PacketManifest,
    "measure": MeasureFile,
    "a1": A1File,
    "a2": A2File,
    "record": RecordFile,
    "gold": GoldFile,
    "eval": EvalFile,
    "motion-stats": MotionStats,
    "sound-stats": SoundStats,
    "pacing-stats": PacingStats,
    "pattern-stats": PatternsFile,
    "pattern-card": PatternCard,
    "scene-batch": SceneBatch,
    "scene-stats": ScenesFile,
    "archetype-card": ArchetypeCard,
    "motion-tokens": MotionTokens,
    "sound-spec": SoundSpec,
    "pacing-spec": PacingSpec,
    "voice-spec": VoiceSpec,
    "archetypes-export": ArchetypesExport,
    "patterns-export": PatternsExport,
    "compare-fixes": FixesFile,
    "create-brief": Brief,
    "create-script": Script,
    "create-voice": Voice,
    "create-timeline": Timeline,
    "create-tokens": Tokens,
    "create-storyboard": Storyboard,
}

__all__ = [
    "SCHEMAS",
    "A1File",
    "A2File",
    "Anchors",
    "CandidatesFile",
    "CompareReport",
    "EvalFile",
    "EventFacts",
    "GoldFile",
    "LensConfig",
    "MeasureFile",
    "PacketManifest",
    "Palette",
    "Provenance",
    "RecordFile",
    "SignalsSummary",
    "SourceEntry",
    "SourcesFile",
    "Taxonomy",
    "VideoMeta",
]
