from __future__ import annotations

import sys
import argparse

from collections.abc import Callable
from app.agents.report_schema import StudioScoutReport
from app.location.recommendation.synthesize import build_shoot_plan
from app.location.recommendation.schema import ShootPlan
from app.location.requirements.derive import derive_requirements
from app.location.research.search import research_screenplay
from app.location.scoring.score import score_screenplay
from app.screenplay.schema import ScreenPlay


def run_pipeline(
    screenplay: ScreenPlay,
    region: str = "Bay Area, California",
    agent_report_path: str | None = None,
    agent_report: StudioScoutReport | None = None,
    on_progress: Callable[[str], None] | None = None,
) -> ShootPlan:
    if on_progress:
        on_progress("Deriving structured scene requirements...")
    requirements = derive_requirements(screenplay)

    if agent_report_path or agent_report:
        print(
            f"[pipeline] consuming ADK report: {agent_report_path or 'in-memory'}",
            file=sys.stderr,
        )
    if on_progress:
        on_progress("Consolidating grounded location candidates...")
    candidates = research_screenplay(
        requirements,
        region,
        agent_report_path=agent_report_path,
        agent_report=agent_report,
    )

    if on_progress:
        on_progress("Scoring candidates across visual, feasibility, permit & cost dimensions...")
    scores = score_screenplay(requirements, candidates)

    if on_progress:
        on_progress("Synthesizing shoot plan and checking cross-scene conflicts...")
    return build_shoot_plan(requirements, scores)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("screenplay_path")
    parser.add_argument("region", nargs="?", default="Bay Area, California")
    parser.add_argument("--agent-report", dest="agent_report_path")
    args = parser.parse_args()

    with open(args.screenplay_path, "r", encoding="utf-8") as f:
        screenplay = ScreenPlay.model_validate_json(f.read())

    plan = run_pipeline(screenplay, args.region, args.agent_report_path)

    with open("data/recommendations.json", "w", encoding="utf-8") as f:
        f.write(plan.model_dump_json(indent=2))

    print(f"[pipeline] wrote data/recommendations.json — {len(plan.scenes)} scenes, {plan.shoot_plan_notes}", file=sys.stderr)