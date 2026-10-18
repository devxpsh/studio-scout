from __future__ import annotations

import json
import sys

from typing import List

from google import genai
from google.genai.types import GenerateContentConfig
from pydantic import BaseModel

from app.genai_client import (
    generate_content_with_fallback,
    get_genai_client,
    get_model_id,
)
from app.location.requirements.schema import SceneRequirements, ScreenplayRequirements
from app.location.research.schema import SceneCandidates
from app.location.scoring.rubric import compute_composite
from app.location.scoring.schema import SceneCandidateScores, ScoredCandidate, SceneScores

MODEL_ID = get_model_id()


class _ScreenplayCandidateScoresBatch(BaseModel):
    scenes: List[SceneCandidateScores]


SYSTEM_INSTRUCTION = """You are a location-scouting scoring analyst. Given one or more \
scenes' requirements and candidate locations, score every candidate on each \
dimension.

Rules:
- Return one SceneCandidateScores entry per input scene, matching scene_number.
- Return exactly one CandidateScore per candidate, using candidate_index matching \
its 0-based position in that scene's candidates list.
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
    return get_genai_client(attempts=5, initial_delay=2, max_delay=60)


def _build_scene_scores(
    requirements: SceneRequirements,
    candidates: SceneCandidates,
    result: SceneCandidateScores,
) -> SceneScores:
    scored = [
        ScoredCandidate(
            candidate=candidates.candidates[cs.candidate_index],
            score=cs.score,
            composite_score=compute_composite(cs.score),
        )
        for cs in result.scores
        if 0 <= cs.candidate_index < len(candidates.candidates)
    ]
    scored.sort(key=lambda sc: sc.composite_score, reverse=True)
    return SceneScores(
        scene_number=requirements.scene_number,
        location=requirements.location,
        scored_candidates=scored,
    )


def score_scene(
    client: genai.Client, requirements: SceneRequirements, candidates: SceneCandidates
) -> SceneScores:
    if not candidates.candidates:
        return SceneScores(
            scene_number=requirements.scene_number,
            location=requirements.location,
            scored_candidates=[],
        )

    prompt = (
        f"Scene requirements:\n{requirements.model_dump_json()}\n\n"
        f"Candidates:\n{candidates.model_dump_json()}"
    )
    response = generate_content_with_fallback(
        client,
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

    return _build_scene_scores(requirements, candidates, result)


def score_screenplay(
    requirements: ScreenplayRequirements, all_candidates: list[SceneCandidates]
) -> list[SceneScores]:
    client = _client()
    candidates_by_scene = {c.scene_number: c for c in all_candidates}
    scenes_to_score = [
        (scene_req, candidates_by_scene[scene_req.scene_number])
        for scene_req in requirements.scenes
        if scene_req.scene_number in candidates_by_scene
    ]

    results_by_scene: dict[int, SceneScores] = {}
    non_empty_pairs: list[tuple[SceneRequirements, SceneCandidates]] = []
    for req, cands in scenes_to_score:
        if not cands.candidates:
            results_by_scene[req.scene_number] = SceneScores(
                scene_number=req.scene_number,
                location=req.location,
                scored_candidates=[],
            )
        else:
            non_empty_pairs.append((req, cands))

    batch_size = 5
    for idx in range(0, len(non_empty_pairs), batch_size):
        batch_pairs = non_empty_pairs[idx : idx + batch_size]
        prompt = "\n\n".join(
            f"=== SCENE {req.scene_number} ===\n"
            f"Scene requirements:\n{req.model_dump_json()}\n\n"
            f"Candidates:\n{cands.model_dump_json()}"
            for req, cands in batch_pairs
        )
        response = generate_content_with_fallback(
            client,
            contents=[SYSTEM_INSTRUCTION, prompt],
            config=GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=_ScreenplayCandidateScoresBatch,
            ),
        )
        parsed_batch: _ScreenplayCandidateScoresBatch | None = response.parsed
        batch_map = (
            {s.scene_number: s for s in parsed_batch.scenes}
            if parsed_batch is not None
            else {}
        )
        for req, cands in batch_pairs:
            scene_result = batch_map.get(req.scene_number)
            if scene_result is not None:
                results_by_scene[req.scene_number] = _build_scene_scores(
                    req, cands, scene_result
                )
            else:
                results_by_scene[req.scene_number] = score_scene(client, req, cands)

    return [
        results_by_scene[req.scene_number]
        for req, _ in scenes_to_score
        if req.scene_number in results_by_scene
    ]


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