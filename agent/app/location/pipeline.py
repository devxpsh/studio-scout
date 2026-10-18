from __future__ import annotations

import argparse
from collections.abc import Callable
import sys

from app.agents.report_schema import (
    EvidenceSource,
    LocationCandidate,
    RegionSource,
    RiskLevel,
    SceneReport,
    StudioScoutReport,
)
from app.location.recommendation.schema import ShootPlan
from app.location.recommendation.synthesize import build_shoot_plan
from app.location.requirements.derive import derive_requirements
from app.location.requirements.schema import ScreenplayRequirements
from app.location.research.search import research_screenplay
from app.location.scoring.score import score_screenplay
from app.screenplay.schema import ScreenPlay


def build_report_from_plan(
    screenplay: ScreenPlay,
    requirements: ScreenplayRequirements,
    shoot_plan: ShootPlan,
    region: str,
) -> StudioScoutReport:
    """Construct a StudioScoutReport directly from pipeline outputs so Free Tier runs
    populate both agent_report and shoot_plan without duplicate LLM calls."""
    orig_by_num = {s.scene_number: s for s in screenplay.scenes}
    req_by_num = {s.scene_number: s for s in requirements.scenes}

    scene_reports: list[SceneReport] = []
    for scene_rec in shoot_plan.scenes:
        orig = orig_by_num.get(scene_rec.scene_number)
        req = req_by_num.get(scene_rec.scene_number)
        slugline = orig.slugline if orig else f"SCENE {scene_rec.scene_number}"
        setting = orig.setting if orig else req.setting if req else "exterior"
        time_of_day = orig.time_of_day if orig else req.time_of_day if req else "day"
        features_str = (
            ", ".join(req.required_features[:3])
            if req and req.required_features
            else "standard production access"
        )
        mood_str = req.mood_tone.capitalize() if req and req.mood_tone else "Cinematic"
        summary = f"{mood_str} {setting.value if hasattr(setting, 'value') else setting} shoot requiring {features_str}."

        candidates: list[LocationCandidate] = []
        for sc in scene_rec.top_candidates:
            if sc.score.permit_ease < 45 or sc.score.logistics < 45:
                risk = RiskLevel.HIGH
            elif sc.score.permit_ease >= 70 and sc.score.logistics >= 65:
                risk = RiskLevel.LOW
            else:
                risk = RiskLevel.MEDIUM

            candidates.append(
                LocationCandidate(
                    name=sc.candidate.name,
                    sub_region=sc.candidate.address_or_area,
                    summary=sc.candidate.description,
                    evidence=[
                        EvidenceSource(title=e.source_title, url=e.source_url)
                        for e in sc.candidate.evidence
                        if e.source_url
                    ],
                    risk_level=risk,
                    risk_justification=(
                        f"Permit ease {sc.score.permit_ease}/100, feasibility "
                        f"{sc.score.feasibility}/100, composite {sc.composite_score:.0f}/100."
                    ),
                    logistics_notes=(
                        f"Visual match {sc.score.visual_match}/100 · "
                        f"Logistics {sc.score.logistics}/100 · "
                        f"Cost fit {sc.score.cost_fit}/100."
                    ),
                )
            )

        scene_reports.append(
            SceneReport(
                scene_number=scene_rec.scene_number,
                slugline=slugline,
                setting=setting,
                time_of_day=time_of_day,
                location_description=scene_rec.location,
                scene_summary=summary,
                candidates=candidates,
            )
        )

    return StudioScoutReport(
        screenplay_title=shoot_plan.title,
        region_used=region,
        region_source=RegionSource.USER_SPECIFIED,
        overall_summary=(
            f"Scouted and scored {len(shoot_plan.scenes)} scenes across {region}. "
            f"{shoot_plan.shoot_plan_notes}"
        ),
        scenes=scene_reports,
    )


def run_pipeline(
    screenplay: ScreenPlay,
    region: str = "Bay Area, California",
    agent_report_path: str | None = None,
    agent_report: StudioScoutReport | None = None,
    on_progress: Callable[[str], None] | None = None,
    on_trace: Callable[[str, str, str], None] | None = None,
    out_report: list[StudioScoutReport] | None = None,
) -> ShootPlan:
    def _emit(agent: str, status: str, msg: str) -> None:
        if on_trace:
            on_trace(agent, status, msg)
        elif on_progress and status == "running":
            on_progress(msg)

    _emit(
        "script_breakdown",
        "running",
        f"Deriving visual, cast, and permit requirements for {screenplay.scene_count()} scenes...",
    )
    requirements = derive_requirements(screenplay)
    _emit(
        "script_breakdown",
        "done",
        f"Derived structured production requirements for {len(requirements.scenes)} scenes.",
    )

    if agent_report_path or agent_report:
        print(
            f"[pipeline] consuming ADK report: {agent_report_path or 'in-memory'}",
            file=sys.stderr,
        )
    _emit(
        "location_grounding",
        "running",
        f"Grounding real-world filming locations in {region}...",
    )
    candidates = research_screenplay(
        requirements,
        region,
        agent_report_path=agent_report_path,
        agent_report=agent_report,
    )
    total_cands = sum(len(s.candidates) for s in candidates)
    _emit(
        "location_grounding",
        "done",
        f"Grounded {total_cands} candidate locations across {len(candidates)} scenes in {region}.",
    )

    _emit(
        "logistics_risk",
        "running",
        "Scoring candidates across visual, feasibility, permit & cost dimensions...",
    )
    scores = score_screenplay(requirements, candidates)
    _emit(
        "logistics_risk",
        "done",
        f"Completed 6-dimension rubric scoring and risk assessment for {len(scores)} scenes.",
    )

    _emit(
        "orchestrator",
        "running",
        "Synthesizing shoot plan rationales and checking cross-scene conflicts...",
    )
    shoot_plan = build_shoot_plan(requirements, scores)
    if out_report is not None and agent_report is None:
        out_report.append(
            build_report_from_plan(screenplay, requirements, shoot_plan, region)
        )
    return shoot_plan


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