from __future__ import annotations

from app.location.scoring.schema import ScoreBreakdown

WEIGHTS = {
    "visual_match": 0.30,
    "feasibility": 0.25,
    "logistics": 0.15,
    "cost_fit": 0.15,
    "permit_ease": 0.10,
    "evidence_confidence": 0.05,
}


def compute_composite(score: ScoreBreakdown) -> float:
    total = sum(getattr(score, dimension) * weight for dimension, weight in WEIGHTS.items())
    return round(total, 2)