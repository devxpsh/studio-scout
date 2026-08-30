from __future__ import annotations

import sys

from app.location.recommendation.synthesize import build_shoot_plan
from app.location.recommendation.schema import ShootPlan
from app.location.requirements.derive import derive_requirements
from app.location.research.search import research_screenplay
from app.location.scoring.score import score_screenplay
from app.screenplay.schema import ScreenPlay


def run_pipeline(screenplay: ScreenPlay) -> ShootPlan:
    requirements = derive_requirements(screenplay)
    candidates = research_screenplay(requirements)
    scores = score_screenplay(requirements, candidates)
    return build_shoot_plan(requirements, scores)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python pipeline.py <path-to-screenplay.json>")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        screenplay = ScreenPlay.model_validate_json(f.read())

    plan = run_pipeline(screenplay)

    with open("data/recommendations.json", "w", encoding="utf-8") as f:
        f.write(plan.model_dump_json(indent=2))

    print(f"[pipeline] wrote data/recommendations.json — {len(plan.scenes)} scenes, {plan.shoot_plan_notes}", file=sys.stderr)