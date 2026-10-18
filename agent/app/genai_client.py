"""Shared Gemini API client factory supporting Google AI Studio Free Tier (default) and Vertex AI."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai.types import HttpOptions, HttpRetryOptions

# Load .env from agent/ directory if present, then current working directory.
_AGENT_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
if _AGENT_ENV_PATH.exists():
    load_dotenv(_AGENT_ENV_PATH)
load_dotenv()

DEFAULT_MODEL_ID = "gemini-2.5-flash"


def is_vertex_ai_enabled() -> bool:
    """Return True only when Vertex AI is explicitly enabled and GEMINI_API_KEY is not set."""
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if gemini_key:
        return False
    use_vertex = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").strip().lower()
    return use_vertex in ("true", "1", "yes") and bool(
        os.environ.get("GOOGLE_CLOUD_PROJECT", "").strip()
    )


def configure_genai_env() -> None:
    """Synchronize environment variables for both google-genai and google-adk."""
    if not is_vertex_ai_enabled():
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"


configure_genai_env()


def get_model_id() -> str:
    """Return the configured Gemini model ID (defaults to gemini-2.5-flash for free-tier quota)."""
    return os.environ.get("GEMINI_MODEL", DEFAULT_MODEL_ID).strip() or DEFAULT_MODEL_ID


def get_genai_client(
    attempts: int = 5,
    initial_delay: float = 2.0,
    max_delay: float = 60.0,
) -> genai.Client:
    """Create a google.genai.Client configured for Google AI Studio Free Tier or Vertex AI."""
    configure_genai_env()
    http_options = HttpOptions(
        retry_options=HttpRetryOptions(
            attempts=attempts,
            initial_delay=initial_delay,
            max_delay=max_delay,
            exp_base=2,
        )
    )

    if is_vertex_ai_enabled():
        return genai.Client(
            vertexai=True,
            project=os.environ["GOOGLE_CLOUD_PROJECT"],
            location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
            http_options=http_options,
        )

    api_key = (
        os.environ.get("GEMINI_API_KEY", "").strip()
        or os.environ.get("GOOGLE_API_KEY", "").strip()
    )
    if not api_key:
        raise RuntimeError(
            "Missing GEMINI_API_KEY. Get a free API key from https://aistudio.google.com/apikey "
            "and set GEMINI_API_KEY in agent/.env (or environment variables)."
        )

    return genai.Client(
         vertexai=False,
        api_key=api_key,
        http_options=http_options,
    )
