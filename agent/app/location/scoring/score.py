from __future__ import annotations

import json
import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai.types import GenerateContentConfig
from google.genai.types import HttpOptions, HttpRetryOptions

from app.location.requirements.schema import SceneRequirements, ScreenplayRequirements
from app.location.research.schema import SceneCandidates
from app.location.scoring.rubric import compute_composite
from app.location.scoring.schema import SceneCandidateScores, ScoredCandidate, SceneScores

load_dotenv()

MODEL_ID = "gemini-2.5-flash"

SYSTEM_INSTRUCTION = """You are a location-scouting scoring analyst. Given a scene's \
requirements and a list of candidate locations, score every candidate on each \
dimension.

Rules:
- Return exactly one CandidateScore per candidate, using candidate_index matching \
its 0-based position in the input candidates list.
- visual_match: how well the candidate's description matches visual_descriptors \
and mood_tone.
- feasibility: how well the candidate supports required_features.
- logistics: fit for cast_size and crew_footprint, based on the candidate's \
description.
- cost_fit: fit against budget_tier, inferred from the candidate's description.
- permit_ease: inferred ease of obtaining permits, based on permit_sensitivity and \
whether the candidate appears to be public or private property.
- evidence_confidence: based on the quality and specificity of the candidate's \
evidence list. Candidates with no evidence score low here.
- All scores are integers from 0 to 100.
- Do not invent details not present in the requirements or candidate description.
"""


def _client() -> genai.Client:
    return genai.Client(
        vertexai=True,
        project=os.environ["GOOGLE_CLOUD_PROJECT"],
        location=os.environ["GOOGLE_CLOUD_LOCATION"],
        http_options=HttpOptions(
            retry_options=HttpRetryOptions(
                attempts=5,
                initial_delay=2,
                max_delay=60,
                exp_base=2,
            )
        ),
    )


def score_scene(client: genai.Client, requirements: SceneRequirements, candidates: SceneCandidates) -> SceneScores:
    if not candidates.candidates:
        return SceneScores(scene_number=requirements.scene_number, location=requirements.location, scored_candidates=[])

    prompt = (
        f"Scene requirements:\n{requirements.model_dump_json()}\n\n"
        f"Candidates:\n{candidates.model_dump_json()}"
    )
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=[SYSTEM_INSTRUCTION, prompt],
        config=GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SceneCandidateScores,
        ),
    )

    result = response.parsed
    if result is None:
        raise ValueError(
            "Gemini did not return a schema-conformant response. "
            f"Raw text:\n{response.text}"
        )

    scored = [
        ScoredCandidate(
            candidate=candidates.candidates[cs.candidate_index],
            score=cs.score,
            composite_score=compute_composite(cs.score),
        )
        for cs in result.scores
    ]
    scored.sort(key=lambda sc: sc.composite_score, reverse=True)

    return SceneScores(scene_number=requirements.scene_number, location=requirements.location, scored_candidates=scored)


def score_screenplay(requirements: ScreenplayRequirements, all_candidates: list[SceneCandidates]) -> list[SceneScores]:
    client = _client()
    candidates_by_scene = {c.scene_number: c for c in all_candidates}
    results = []
    for scene_requirements in requirements.scenes:
        candidates = candidates_by_scene.get(scene_requirements.scene_number)
        if candidates is None:
            continue
        results.append(score_scene(client, scene_requirements, candidates))
    return results


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python score.py <path-to-requirements.json> <path-to-candidates.json>")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        requirements = ScreenplayRequirements.model_validate_json(f.read())

    with open(sys.argv[2], "r", encoding="utf-8") as f:
        all_candidates = [SceneCandidates.model_validate(item) for item in json.load(f)]

    results = score_screenplay(requirements, all_candidates)
    for scene_scores in results:
        print(scene_scores.model_dump_json(indent=2))
    print(f"\n[score] {len(results)} scenes scored.", file=sys.stderr)