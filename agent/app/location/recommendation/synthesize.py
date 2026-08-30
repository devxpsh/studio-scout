from __future__ import annotations

import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai.types import GenerateContentConfig

from app.location.conflicts.detect import detect_conflicts
from app.location.conflicts.schema import Conflict, Severity
from app.location.requirements.schema import ScreenplayRequirements
from app.location.recommendation.schema import ScreenplayRationales, SceneRecommendation, ShootPlan
from app.location.scoring.schema import SceneScores

load_dotenv()

MODEL_ID = "gemini-2.5-flash"

SYSTEM_INSTRUCTION = """You are a location-scouting assistant writing rationales for \
a shoot plan. For each scene, write one or two sentences explaining why its \
top-ranked candidate was recommended, using the score breakdown and candidate \
description provided.

Rules:
- Ground every rationale in the provided score breakdown and candidate description.
- Do not invent details not present in the input.
- Keep each rationale concise and specific, not generic praise.
"""


def _client() -> genai.Client:
    return genai.Client(
        vertexai=True,
        project=os.environ["GOOGLE_CLOUD_PROJECT"],
        location=os.environ["GOOGLE_CLOUD_LOCATION"],
    )


def _generate_rationales(client: genai.Client, scene_scores: list[SceneScores]) -> dict[int, str]:
    scenes_with_top = [s for s in scene_scores if s.scored_candidates]
    if not scenes_with_top:
        return {}

    prompt = "\n\n".join(
        f"scene_number: {s.scene_number}\n"
        f"location: {s.location}\n"
        f"top_candidate: {s.scored_candidates[0].candidate.model_dump_json()}\n"
        f"score: {s.scored_candidates[0].score.model_dump_json()}"
        for s in scenes_with_top
    )

    response = client.models.generate_content(
        model=MODEL_ID,
        contents=[SYSTEM_INSTRUCTION, prompt],
        config=GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ScreenplayRationales,
        ),
    )

    result = response.parsed
    if result is None:
        raise ValueError(
            "Gemini did not return a schema-conformant response. "
            f"Raw text:\n{response.text}"
        )
    return {r.scene_number: r.rationale for r in result.scenes}


def _shoot_plan_notes(conflicts: list[Conflict]) -> str:
    counts = {severity: 0 for severity in Severity}
    for conflict in conflicts:
        counts[conflict.severity] += 1
    return (
        f"{len(conflicts)} conflicts detected: "
        f"{counts[Severity.BLOCKER]} blocker(s), "
        f"{counts[Severity.WARNING]} warning(s), "
        f"{counts[Severity.INFO]} info."
    )


def build_shoot_plan(requirements: ScreenplayRequirements, scene_scores: list[SceneScores]) -> ShootPlan:
    client = _client()
    all_conflicts = detect_conflicts(requirements, scene_scores)
    rationales = _generate_rationales(client, scene_scores)

    scenes = []
    global_conflicts = []
    for scene in scene_scores:
        scene_conflicts = [c for c in all_conflicts if scene.scene_number in c.affected_scenes]
        if any(len(c.affected_scenes) > 1 for c in scene_conflicts):
            global_conflicts.extend(c for c in scene_conflicts if len(c.affected_scenes) > 1)

        recommended = scene.scored_candidates[0].candidate.name if scene.scored_candidates else "none found"
        rationale = rationales.get(scene.scene_number, "No candidates available for this scene.")

        scenes.append(SceneRecommendation(
            scene_number=scene.scene_number,
            location=scene.location,
            top_candidates=scene.scored_candidates[:5],
            recommended=recommended,
            rationale=rationale,
            conflicts=scene_conflicts,
        ))

    deduped_global = list({id(c): c for c in global_conflicts}.values())

    return ShootPlan(
        title=requirements.title,
        scenes=scenes,
        global_conflicts=deduped_global,
        shoot_plan_notes=_shoot_plan_notes(all_conflicts),
    )


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python synthesize.py <path-to-requirements.json> <path-to-scores.json>")
        sys.exit(1)

    import json

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        requirements = ScreenplayRequirements.model_validate_json(f.read())

    with open(sys.argv[2], "r", encoding="utf-8") as f:
        scene_scores = [SceneScores.model_validate(item) for item in json.load(f)]

    plan = build_shoot_plan(requirements, scene_scores)
    print(plan.model_dump_json(indent=2))
    print(f"\n[synthesize] shoot plan built for {len(plan.scenes)} scenes.", file=sys.stderr)