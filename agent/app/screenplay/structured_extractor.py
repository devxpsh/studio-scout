"""
Studio Scout - Phase 02, Step 4
Gemini structured extraction

raw screenplay text -> ScreenPlay(schema-constrained response)

Independent of the parallel tool and of ADK. This is a standalone
pipeline stage, not an agent tool.
"""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai.types import GenerateContentConfig

from app.screenplay.extractor import extract_text
from app.screenplay.schema import ScreenPlay as Screenplay
load_dotenv()

MODEL_ID = "gemini-2.5-flash"

SYSTEM_INSTRUCTION = """You are a screenplay structuring speacialist. Given raw \
screenplay text, extract every scene into the provided schema.

Rules:
- Preserve scene order exactly as it appears in the text via scene_number \
(starting at 1).
- slugline must be the exact original slugline text (e.g. \
"EXT. OLD RAILWAY STATION - DAWN").
- setting must be normalized to "interior", "exterior",or \
"interior/exterior" based on slugline's INT./EXT./INT./EXT. prefix.
- location must be normalized location name from the slugline, \
lowercased, with no leading "EXT."/"INT." and no time-of-day suffix.
- time_of_day must be normalized to one of the fixed values in the schema \
based  on the slugline's time-of-day suffix. Use "unknown" only if the \
slugline has no time-of-day suffix.
- description must contain the scene's action/prose text, excluding \
character cues and dialogue lines.
- characters must list every character who appears or speaks in the scene, \
lowercased, in order of first appearance.
- dialogue must list every spoken line in order, with the speaking \
character's name lowercased.
- Do not invent content that is not present in the source text.
"""


def _client() -> genai.Client:
    return genai.Client(
        vertexai=True,
        project=os.environ["GOOGLE_CLOUD_PROJECT"],
        location=os.environ["GOOGLE_CLOUD_LOCATION"],
    )


def extract_screenplay(raw_text: str) -> Screenplay:
    """Send raw screenplay text to Gemini and return a validated Screenplay."""
    client = _client()
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=[SYSTEM_INSTRUCTION, raw_text],
        config=GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=Screenplay,
        ),
    )

    screenplay = response.parsed
    if screenplay is None:
        raise ValueError(
            "Gemini did not return a schema-conformant response. "
            f"Raw text:\n{response.text}"
        )
    return screenplay


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python structured_extractor.py <path-to-screenplay.pdf>")
        sys.exit(1)

    text = extract_text(sys.argv[1])
    screenplay = extract_screenplay(text)
    print(screenplay.model_dump_json(indent=2))
    print(f"\n[structured_extractor] {screenplay.scene_count()} scenes extracted.", file=sys.stderr)
