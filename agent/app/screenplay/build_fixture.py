"""
Studio Scout -- Phase 02, Step 5
Validate and produce the final screenplay.json fixture

screenplay.pdf -> extractor -> structured_extractor -> validated Screenplay -> screenplay.json
"""

from __future__ import annotations

import sys
from pathlib import Path

from app.screenplay.extractor import extract_text
from app.screenplay.structured_extractor import extract_screenplay


def build_fixture(pdf_path: str, out_path: str) -> None:
    raw_text = extract_text(pdf_path)

    screenplay = extract_screenplay(raw_text)
    validated = screenplay.__class__.model_validate(screenplay.model_dump())

    Path(out_path).write_text(validated.model_dump_json(indent=2))

    print(f"[build_fixture] wrote {out_path}")
    print(f"[build_fixture] {validated.scene_count()} scenes")
    print(f"[build_fixture] locations: {validated.locations()}")



if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python build_fixture.py <path-to-screenplay.pdf> <path-to-screenplay.json>")
        sys.exit(1)

    build_fixture(sys.argv[1], sys.argv[2])
