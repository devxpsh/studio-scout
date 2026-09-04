from __future__ import annotations

import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai.types import (
    GenerateContentConfig,
    Tool,
    ToolParallelAiSearch,
)

from app.location.requirements.schema import ScreenplayRequirements, SceneRequirements
from app.location.research.schema import SceneCandidates
from google.genai.types import HttpOptions, HttpRetryOptions
from google.genai.types import AutomaticFunctionCallingConfig

load_dotenv()

MODEL_ID = "gemini-2.5-flash"
DEFAULT_REGION = "Bay Area, California"

PARALLEL_API_KEY = os.environ.get("PARALLEL_API_KEY")
PARALLEL_ENDPOINT = os.environ.get("PARALLEL_GROUNDING_ENDPOINT")

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


def _grounding_tool() -> Tool:
    return Tool(
        parallel_ai_search=ToolParallelAiSearch(
            api_key=PARALLEL_API_KEY,
            custom_configs={
                "mode": "basic",
                "max_results": 10,
            },
        )
    )


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
    metadata = response.candidates[0].grounding_metadata
    chunks = metadata.grounding_chunks if metadata and metadata.grounding_chunks else []
    return response.text, chunks

def _format_sources(chunks: list) -> str:
    if not chunks:
        return "(no sources returned)"
    return "\n".join(
        f"[{i}] {c.web.title} — {c.web.uri} ({c.web.domain})"
        for i, c in enumerate(chunks, start=1)
    )


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


def research_screenplay(
    requirements: ScreenplayRequirements, region: str = DEFAULT_REGION
) -> list[SceneCandidates]:
    client = _client()
    return [research_scene(client, scene, region) for scene in requirements.scenes]


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