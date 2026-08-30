from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field

from app.location.conflicts.schema import Conflict
from app.location.scoring.schema import ScoredCandidate


class SceneRationale(BaseModel):
    scene_number: int = Field(..., ge=1)
    rationale: str = Field(..., description="One or two sentences on why the top candidate was recommended.")


class ScreenplayRationales(BaseModel):
    scenes: List[SceneRationale]


class SceneRecommendation(BaseModel):
    scene_number: int
    location: str
    top_candidates: List[ScoredCandidate] = Field(..., description="Ranked best-first.")
    recommended: str = Field(..., description="Name of the recommended candidate.")
    rationale: str
    conflicts: List[Conflict] = Field(default_factory=list, description="Conflicts affecting this scene.")


class ShootPlan(BaseModel):
    title: str
    scenes: List[SceneRecommendation]
    global_conflicts: List[Conflict] = Field(default_factory=list, description="Conflicts affecting multiple scenes.")
    shoot_plan_notes: str = Field(..., description="Deterministic summary of conflict counts by severity.")