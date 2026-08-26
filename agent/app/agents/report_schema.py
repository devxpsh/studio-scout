"""
Studio Scout — Phase 03
Structured report schema for the orchestrator's final synthesized output.

Designed to be directly renderable by the frontend without further
parsing: risk levels are an enum (for badge/color coding), evidence is
a list of {title, url} pairs (for clickable citation chips), and each
scene carries its own one-line summary (for a collapsed card view)
alongside the full candidate breakdown (for the expanded view).

Reuses Setting/TimeOfDay from the Phase 02 screenplay schema rather
than redefining them, so a scene's setting/time_of_day render
identically whether the frontend is showing screenplay data or this
report.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from app.screenplay.schema import Setting, TimeOfDay


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"  # insufficient evidence to assess -- distinct from LOW


class RegionSource(str, Enum):
    USER_SPECIFIED = "user_specified"
    INFERRED_FROM_SCREENPLAY = "inferred_from_screenplay"


class EvidenceSource(BaseModel):
    title: str = Field(..., description="Title of the source article/page.")
    url: str = Field(..., description="URL of the source, for a clickable citation chip.")


class LocationCandidate(BaseModel):
    name: str = Field(..., description="Name of the real-world candidate location.")
    sub_region: Optional[str] = Field(
        None, description="City/state/district within the overall region, e.g. 'Satara district, Maharashtra'."
    )
    summary: str = Field(..., description="One to two sentence summary of why this candidate fits, for a card view.")
    evidence: List[EvidenceSource] = Field(
        default_factory=list, description="Sources backing this candidate, for citation chips."
    )
    risk_level: RiskLevel = Field(..., description="Qualitative risk level, for a colored badge.")
    risk_justification: str = Field(..., description="One to two sentence justification for the risk level.")
    logistics_notes: str = Field(
        default="", description="Logistics considerations (lighting, permits, crowd control, etc.)."
    )


class SceneReport(BaseModel):
    scene_number: int = Field(..., ge=1)
    slugline: str
    setting: Setting
    time_of_day: TimeOfDay
    location_description: str = Field(..., description="The screenplay's own location text, e.g. 'old railway station'.")
    scene_summary: str = Field(..., description="One-line summary of the scene's location needs, for a collapsed card header.")
    candidates: List[LocationCandidate] = Field(default_factory=list)


class StudioScoutReport(BaseModel):
    screenplay_title: str
    region_used: str = Field(..., description="The region location research was scoped to.")
    region_source: RegionSource = Field(
        ..., description="Whether the region was given by the user or inferred from the screenplay's own content."
    )
    overall_summary: str = Field(
        ..., description="Two to three sentence executive summary across all scenes, for a dashboard header."
    )
    scenes: List[SceneReport] = Field(default_factory=list)

    def scene_count(self) -> int:
        return len(self.scenes)

    def highest_risk_scenes(self) -> List[SceneReport]:
        """Scenes where at least one candidate is HIGH risk -- useful for a frontend 'flagged' filter."""
        return [
            s for s in self.scenes
            if any(c.risk_level == RiskLevel.HIGH for c in s.candidates)
        ]