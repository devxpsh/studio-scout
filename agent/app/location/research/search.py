from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import os
from pathlib import Path
import sys
from typing import List

from google import genai
from google.genai.types import (
    AutomaticFunctionCallingConfig,
    GenerateContentConfig,
    GoogleSearch,
    Tool,
    ToolParallelAiSearch,
)
from pydantic import BaseModel

from app.agents.report_schema import StudioScoutReport
from app.genai_client import (
    generate_content_with_fallback,
    get_genai_client,
    get_model_id,
    is_vertex_ai_enabled,
)
from app.location.requirements.schema import SceneRequirements, ScreenplayRequirements
from app.location.research.schema import Candidate, SceneCandidates
from app.tools.parallel_search import parallel_search

MODEL_ID = get_model_id()
DEFAULT_REGION = "Bay Area, California"

PARALLEL_API_KEY = os.environ.get("PARALLEL_API_KEY")
PARALLEL_ENDPOINT = os.environ.get("PARALLEL_GROUNDING_ENDPOINT")


@dataclass
class _WebSource:
    title: str
    uri: str
    domain: str = "web"


@dataclass
class _SourceChunk:
    web: _WebSource


class _ScreenplayCandidatesBatch(BaseModel):
    scenes: List[SceneCandidates]


EXTRACTION_SYSTEM_INSTRUCTION = """You are a location-scouting research assistant. Given \
scene requirements, grounded search results, and a list of available sources about \
filming locations in the target region, extract real-world candidate filming \
locations into the provided schema.

Rules:
- scene_number and location must match the input scene exactly.
- Always include 3 to 5 named real-world candidate filming locations in the target \
region for EVERY scene, ranked best-first.
- When a scene's script location is fictional, sci-fi, period, or abstract (e.g. an \
orbital station bay, spacecraft corridor, or escape pod), recommend real-world \
architectural stand-ins, industrial facilities, historic ships/bunkers, museums, or \
soundstages in the target region that match the scene's visual_descriptors and \
required_features.
- Every evidence entry's source_url must be copied verbatim from the Available \
sources list provided for that scene. Never invent or alter a URL.
- If no available source directly backs a candidate, leave its evidence list empty \
rather than omitting the candidate.
"""


def _client() -> genai.Client:
    return get_genai_client(attempts=5, initial_delay=2, max_delay=60)


def _grounding_tool() -> Tool:
    if is_vertex_ai_enabled() and PARALLEL_API_KEY:
        return Tool(
            parallel_ai_search=ToolParallelAiSearch(
                api_key=PARALLEL_API_KEY,
                custom_configs={
                    "mode": "basic",
                    "max_results": 10,
                },
            )
        )
    return Tool(google_search=GoogleSearch())


def _build_query(requirements: SceneRequirements, region: str) -> str:
    descriptors = ", ".join(requirements.visual_descriptors) or requirements.location
    features = ", ".join(requirements.required_features)
    return (
        f"Find real-world filming locations or architectural stand-ins in {region} matching: "
        f"{descriptors}. Mood: {requirements.mood_tone}. "
        f"Must support: {features}. "
        "List specific named places with addresses or areas, not generic advice."
    )


def _ground_scene_via_parallel(
    requirements: SceneRequirements, region: str
) -> tuple[str, list]:
    setting_word = (
        requirements.setting.value
        if hasattr(requirements.setting, "value")
        else str(requirements.setting)
    )
    descriptors = " ".join(requirements.visual_descriptors[:2]) or requirements.location
    features = " ".join(requirements.required_features[:1])
    short_query = (
        f"{region} filming locations {setting_word} {descriptors} {features}"[:120]
    )
    results = parallel_search(short_query)
    if not results:
        results = parallel_search(f"{region} film production locations industrial studio")
    grounded_lines = []
    chunks = []
    for idx, r in enumerate(results, start=1):
        title = r.get("title") or "Untitled source"
        url = r.get("url") or ""
        excerpt = r.get("excerpt") or ""
        grounded_lines.append(f"[{idx}] {title} ({url}):\n{excerpt}")
        if url:
            chunks.append(_SourceChunk(web=_WebSource(title=title, uri=url)))
    return "\n\n".join(grounded_lines), chunks


def _ground_scene(
    client: genai.Client, requirements: SceneRequirements, region: str
) -> tuple[str, list]:
    if not is_vertex_ai_enabled() and os.environ.get("PARALLEL_API_KEY", "").strip():
        grounded_text, chunks = _ground_scene_via_parallel(requirements, region)
        if grounded_text:
            return grounded_text, chunks

    response = generate_content_with_fallback(
        client,
        contents=_build_query(requirements, region),
        config=GenerateContentConfig(
            tools=[_grounding_tool()],
            automatic_function_calling=AutomaticFunctionCallingConfig(
                maximum_remote_calls=1,
            ),
        ),
    )
    metadata = response.candidates[0].grounding_metadata if response.candidates else None
    chunks = metadata.grounding_chunks if metadata and metadata.grounding_chunks else []
    return response.text or "", chunks


def _format_sources(chunks: list) -> str:
    if not chunks:
        return "(no sources returned)"
    lines = []
    for i, c in enumerate(chunks, start=1):
        web = getattr(c, "web", None)
        if web is None:
            continue
        title = getattr(web, "title", "") or "Source"
        uri = getattr(web, "uri", "") or ""
        domain = getattr(web, "domain", "") or "web"
        lines.append(f"[{i}] {title} — {uri} ({domain})")
    return "\n".join(lines) if lines else "(no sources returned)"


def _format_scene_prompt_block(
    requirements: SceneRequirements,
    region: str,
    grounded_text: str,
    chunks: list,
) -> str:
    return (
        f"=== SCENE {requirements.scene_number} ===\n"
        f"scene_number: {requirements.scene_number}\n"
        f"location: {requirements.location}\n"
        f"target_region: {region}\n"
        f"setting: {requirements.setting.value if hasattr(requirements.setting, 'value') else requirements.setting}\n"
        f"visual_descriptors: {', '.join(requirements.visual_descriptors)}\n"
        f"mood_tone: {requirements.mood_tone}\n"
        f"required_features: {', '.join(requirements.required_features)}\n\n"
        f"Grounded search results:\n{grounded_text or '(none)'}\n\n"
        f"Available sources (cite source_url verbatim):\n{_format_sources(chunks)}"
    )


def _extract_candidates(
    client: genai.Client,
    requirements: SceneRequirements,
    grounded_text: str,
    chunks: list,
    region: str = DEFAULT_REGION,
) -> SceneCandidates:
    prompt = _format_scene_prompt_block(requirements, region, grounded_text, chunks)
    response = generate_content_with_fallback(
        client,
        contents=[EXTRACTION_SYSTEM_INSTRUCTION, prompt],
        config=GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SceneCandidates,
        ),
    )
    candidates = response.parsed
    if candidates is None:
        raise ValueError(
            "Gemini did not return a schema-conformant response. "
            f"Raw text:\n{response.text}"
        )
    return candidates


def _extract_candidates_batch(
    client: genai.Client,
    items: list[tuple[SceneRequirements, str, list]],
    region: str,
) -> dict[int, SceneCandidates]:
    prompt = "\n\n".join(
        _format_scene_prompt_block(req, region, grounded_text, chunks)
        for req, grounded_text, chunks in items
    )
    response = generate_content_with_fallback(
        client,
        contents=[EXTRACTION_SYSTEM_INSTRUCTION, prompt],
        config=GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=_ScreenplayCandidatesBatch,
        ),
    )
    parsed: _ScreenplayCandidatesBatch | None = response.parsed
    if parsed is None:
        raise ValueError(
            "Gemini did not return a schema-conformant batch response. "
            f"Raw text:\n{response.text}"
        )
    return {sc.scene_number: sc for sc in parsed.scenes}


def research_scene(
    client: genai.Client, requirements: SceneRequirements, region: str
) -> SceneCandidates:
    grounded_text, chunks = _ground_scene(client, requirements, region)
    return _extract_candidates(client, requirements, grounded_text, chunks, region)


def _candidates_from_agent_scene(agent_scene, region: str) -> list[Candidate]:
    return [
        Candidate.model_validate(
            {
                "name": candidate.name,
                "address_or_area": candidate.sub_region or region,
                "description": (
                    f"{candidate.summary} Risk: {candidate.risk_justification} "
                    f"Logistics: {candidate.logistics_notes}"
                ).strip(),
                "evidence": [
                    {
                        "source_url": source.url,
                        "source_title": source.title,
                        "snippet": candidate.summary,
                    }
                    for source in candidate.evidence
                ],
            }
        )
        for candidate in agent_scene.candidates
    ]


def research_screenplay(
    requirements: ScreenplayRequirements,
    region: str = DEFAULT_REGION,
    agent_report_path: str | None = None,
    agent_report: StudioScoutReport | None = None,
) -> list[SceneCandidates]:
    report = agent_report
    if report is None and agent_report_path:
        report = StudioScoutReport.model_validate_json(
            Path(agent_report_path).read_text(encoding="utf-8")
        )
    report_by_scene = (
        {scene.scene_number: scene for scene in report.scenes} if report else {}
    )

    agent_candidates_by_scene: dict[int, list[Candidate]] = {}
    scenes_needing_research: list[SceneRequirements] = []
    results_by_scene: dict[int, SceneCandidates] = {}

    for scene in requirements.scenes:
        agent_scene = report_by_scene.get(scene.scene_number)
        agent_candidates = (
            _candidates_from_agent_scene(agent_scene, region)
            if agent_scene is not None
            else []
        )
        agent_candidates_by_scene[scene.scene_number] = agent_candidates
        if len(agent_candidates) >= 2:
            results_by_scene[scene.scene_number] = SceneCandidates(
                scene_number=scene.scene_number,
                location=scene.location,
                candidates=agent_candidates,
            )
        else:
            scenes_needing_research.append(scene)

    if scenes_needing_research:
        client = _client()
        # Ground all scenes in parallel (uses Parallel Search API directly when available)
        with ThreadPoolExecutor(max_workers=3) as pool:
            grounded_list = list(
                pool.map(
                    lambda s: (s, *_ground_scene(client, s, region)),
                    scenes_needing_research,
                )
            )

        # Batch structured extraction (up to 5 scenes per single Gemini LLM call)
        batch_size = 5
        for idx in range(0, len(grounded_list), batch_size):
            batch_items = grounded_list[idx : idx + batch_size]
            extracted_map = _extract_candidates_batch(client, batch_items, region)
            for scene, grounded_text, chunks in batch_items:
                researched_scene = extracted_map.get(scene.scene_number)
                if researched_scene is None:
                    researched_scene = _extract_candidates(
                        client, scene, grounded_text, chunks, region
                    )
                agent_candidates = agent_candidates_by_scene.get(scene.scene_number, [])
                if not agent_candidates:
                    results_by_scene[scene.scene_number] = researched_scene
                else:
                    existing_names = {c.name.casefold() for c in agent_candidates}
                    results_by_scene[scene.scene_number] = SceneCandidates(
                        scene_number=scene.scene_number,
                        location=scene.location,
                        candidates=[
                            *agent_candidates,
                            *[
                                c
                                for c in researched_scene.candidates
                                if c.name.casefold() not in existing_names
                            ],
                        ],
                    )

    return [
        results_by_scene[scene.scene_number]
        for scene in requirements.scenes
        if scene.scene_number in results_by_scene
    ]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python search.py <path-to-requirements.json>")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        requirements = ScreenplayRequirements.model_validate_json(f.read())

    results = research_screenplay(requirements)
    for scene_candidates in results:
        print(scene_candidates.model_dump_json(indent=2))
    print(f"\n[search] {len(results)} scenes researched.", file=sys.stderr)