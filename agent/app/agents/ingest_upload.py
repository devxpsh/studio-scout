"""
Studio Scout — Phase 03
Upload ingestion callback.

Intercepts a PDF uploaded via adk web's chat interface (arrives as raw
bytes on a Part.inline_data with mime_type "application/pdf" inside the
incoming user Content) BEFORE the orchestrator's own LLM turn runs.
Writes it to data/screenplay.pdf and runs the existing Phase 02 pipeline
synchronously to (re)produce data/screenplay.json, so script_breakdown_agent
has fresh data to load once the orchestrator's normal flow proceeds.

Known, accepted tradeoffs (hackathon scope, not production):
- The Gemini call inside build_fixture() runs synchronously inside this
  async callback, blocking the event loop for its duration.
- The uploaded PDF's raw bytes remain in the message content after
  extraction (user_content is read-only) -- unused but harmless.
"""

from pathlib import Path

from google.adk.agents.callback_context import CallbackContext

from app.screenplay.build_fixture import build_fixture

SCREENPLAY_PDF_PATH = Path(__file__).resolve().parents[2] / "data" / "screenplay.pdf"
SCREENPLAY_JSON_PATH = Path(__file__).resolve().parents[2] / "data" / "screenplay.json"

PDF_MIME_TYPE = "application/pdf"


def ingest_uploaded_screenplay(callback_context: CallbackContext):
    """before_agent_callback: if a PDF was uploaded this turn, ingest it.

    Returns None in all cases so the orchestrator's normal turn always
    proceeds -- this callback only has side effects (writing files), it
    never short-circuits the agent's response.
    """
    user_content = callback_context.user_content
    if user_content is None or not user_content.parts:
        return None

    pdf_bytes = None
    for part in user_content.parts:
        if part.inline_data and part.inline_data.mime_type == PDF_MIME_TYPE:
            pdf_bytes = part.inline_data.data
            break

    if pdf_bytes is None:
        return None  # no PDF uploaded this turn, nothing to do

    SCREENPLAY_PDF_PATH.parent.mkdir(parents=True, exist_ok=True)
    if SCREENPLAY_PDF_PATH.exists() and SCREENPLAY_PDF_PATH.read_bytes() == pdf_bytes:
      print(f"[ingest_uploaded_screenplay] screenplay already prepared at {SCREENPLAY_PDF_PATH}")
      return None

    SCREENPLAY_PDF_PATH.write_bytes(pdf_bytes)

    print(f"[ingest_uploaded_screenplay] wrote {SCREENPLAY_PDF_PATH}")

    build_fixture(str(SCREENPLAY_PDF_PATH), str(SCREENPLAY_JSON_PATH))

    print(f"[ingest_uploaded_screenplay] rebuilt {SCREENPLAY_JSON_PATH}")

    return None