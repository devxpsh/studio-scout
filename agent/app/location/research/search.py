from __future__ import annotations

from dataclasses import dataclass
import os
import sys
from pathlib import Path

from google import genai
from google.genai.types import (
    AutomaticFunctionCallingConfig,
    GenerateContentConfig,
    GoogleSearch,
    Tool,
    ToolParallelAiSearch,
)

from app.agents.report_schema import StudioScoutReport
from app.genai_client import get_genai_client, get_model_id, is_vertex_ai_enabled
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

EXTRACTION_SYSTEM_INSTRUCTION = """You are a location-scouting research assistant. Given \
grounded search results and a list of available sources about candidate filming \
locations for a scene, extract them into the provided schema.

Rules:
- scene_number and location must match the input exactly.
- Include up to 5 candidates, ranked best-first, based on the grounded text — even \
if a candidate has no matching source in the available sources list.
- Every evidence entry's source_url must be copied exactly from the available \
sources list. Never invent or alter a URL.
- If no available source supports a candidate, leave that candidate's evidence \
list empty. Do not omit the candidate itself for lacking evidence.
- description must be grounded in the provided text, not invented.
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
        f"Find real-world filming locations in {region} matching: "
        f"{descriptors}. Mood: {requirements.mood_tone}. "
        f"Must support: {features}. "
        "List specific named places with addresses or areas, not generic advice."
    )


def _ground_scene(
    client: genai.Client, requirements: SceneRequirements, region: str
) -> tuple[str, list]:
    # In Google AI Studio Free Tier mode with PARALLEL_API_KEY available,
    # query the Parallel Search API directly instead of Vertex-only ToolParallelAiSearch.
    if not is_vertex_ai_enabled() and os.environ.get("PARALLEL_API_KEY", "").strip():
        descriptors = " ".join(requirements.visual_descriptors[:2]) or requirements.location
        short_query = f"{region} filming location {requirements.location} {descriptors}"[:120]
        results = parallel_search(short_query)
        if results:
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

    response = client.models.generate_content(
        model=MODEL_ID,
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


def _extract_candidates(client: genai.Client, requirements: SceneRequirements, grounded_text: str, chunks: list) -> SceneCandidates:
    prompt = (
        f"scene_number: {requirements.scene_number}\n"
        f"location: {requirements.location}\n\n"
        f"Grounded search results:\n{grounded_text}\n\n"
        f"Available sources (cite source_url exactly as shown here):\n{_format_sources(chunks)}"
    )
    response = client.models.generate_content(
        model=MODEL_ID,
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


def research_scene(
    client: genai.Client, requirements: SceneRequirements, region: str
) -> SceneCandidates:
    grounded_text, chunks = _ground_scene(client, requirements, region)
    return _extract_candidates(client, requirements, grounded_text, chunks)


from concurrent.futures import ThreadPoolExecutor


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

    client: genai.Client | None = None

    def _process_scene(scene: SceneRequirements) -> SceneCandidates:
        nonlocal client
        agent_scene = report_by_scene.get(scene.scene_number)
        agent_candidates = (
            _candidates_from_agent_scene(agent_scene, region)
            if agent_scene is not None
            else []
        )

        # If the ADK grounding agent already produced sufficient grounded candidates,
        # skip redundant re-grounding to save latency and API quota.
        if len(agent_candidates) >= 2:
            return SceneCandidates(
                scene_number=scene.scene_number,
                location=scene.location,
                candidates=agent_candidates,
            )

        if client is None:
            client = _client()
        researched_scene = research_scene(client, scene, region)
        if not agent_candidates:
            return researched_scene

        existing_names = {c.name.casefold() for c in agent_candidates}
        return SceneCandidates(
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

    with ThreadPoolExecutor(max_workers=3) as pool:
        return list(pool.map(_process_scene, requirements.scenes))


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