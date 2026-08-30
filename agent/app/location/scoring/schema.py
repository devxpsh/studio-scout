from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field

from app.location.research.schema import Candidate


class ScoreBreakdown(BaseModel):
    visual_match: int = Field(..., ge=0, le=100, description="How well the candidate matches the scene's visual descriptors and mood.")
    feasibility: int = Field(..., ge=0, le=100, description="How well the candidate supports the scene's required_features.")
    logistics: int = Field(..., ge=0, le=100, description="Crew/cast capacity, access, and parking fit.")
    cost_fit: int = Field(..., ge=0, le=100, description="Fit against the scene's inferred budget_tier.")
    permit_ease: int = Field(..., ge=0, le=100, description="Inferred ease of obtaining permits, based on permit_sensitivity.")
    evidence_confidence: int = Field(..., ge=0, le=100, description="Aggregate confidence in the candidate's supporting evidence.")


class CandidateScore(BaseModel):
    candidate_index: int = Field(..., ge=0, description="0-based index into the scene's candidates list.")
    score: ScoreBreakdown = Field(..., description="Per-dimension score for this candidate.")


class SceneCandidateScores(BaseModel):
    scene_number: int = Field(..., ge=1, description="Matches SceneCandidates.scene_number.")
    scores: List[CandidateScore] = Field(..., description="One entry per candidate in the scene's candidates list.")


class ScoredCandidate(BaseModel):
    candidate: Candidate
    score: ScoreBreakdown
    composite_score: float = Field(..., ge=0, le=100, description="Weighted composite of the score breakdown.")


class SceneScores(BaseModel):
    scene_number: int = Field(..., ge=1)
    location: str
    scored_candidates: List[ScoredCandidate] = Field(..., description="Ranked best-first by composite_score.")