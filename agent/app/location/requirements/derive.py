from __future__ import annotations

import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai.types import GenerateContentConfig

from app.location.requirements.schema import ScreenplayRequirements
from app.screenplay.schema import ScreenPlay
from google.genai.types import HttpOptions, HttpRetryOptions

load_dotenv()

MODEL_ID = "gemini-2.5-flash"

SYSTEM_INSTRUCTION = """You are a location-scouting requirements analyst. Given a \
structured screenplay (as JSON), derive a location requirement spec for every \
scene.

Rules:
- Preserve scene order exactly via scene_number, matching the input scenes.
- location, setting, and time_of_day must be carried over unchanged from the \
input scene.
- visual_descriptors must be short phrases (2-5 words each) describing what \
the location should look like, drawn only from the scene's description text.
- mood_tone must be one or two words capturing the emotional register of the \
scene.
- required_features must list concrete physical elements the location must \
support to shoot the scene. Infer only from what the description implies; do \
not invent unrelated features.
- cast_size must equal the number of distinct characters present in the scene.
- crew_footprint must be "small", "medium", or "large", estimated from cast \
size and scene complexity.
- budget_tier must be "low", "medium", "high", or "unknown", inferred from \
scene complexity and required_features.
- permit_sensitivity must be "public", "private", or "unknown", inferred from \
the location and setting.
- Do not invent content that is not present in or reasonably inferable from \
the source scene.
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


def derive_requirements(screenplay: ScreenPlay) -> ScreenplayRequirements:
    client = _client()
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=[SYSTEM_INSTRUCTION, screenplay.model_dump_json()],
        config=GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ScreenplayRequirements,
        ),
    )

    requirements = response.parsed
    if requirements is None:
        raise ValueError(
            "Gemini did not return a schema-conformant response. "
            f"Raw text:\n{response.text}"
        )
    return requirements


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python derive.py <path-to-screenplay.json>")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        screenplay = ScreenPlay.model_validate_json(f.read())

    requirements = derive_requirements(screenplay)
    print(requirements.model_dump_json(indent=2))
    print(f"\n[derive] {len(requirements.scenes)} scene requirements derived.", file=sys.stderr)