"""Shared Gemini API client factory supporting Google AI Studio Free Tier (default) and Vertex AI."""

from __future__ import annotations

import itertools
import os
from pathlib import Path
import socket
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai.types import GenerateContentConfig, HttpOptions, HttpRetryOptions

# Prefer IPv4 (AF_INET) before IPv6 (AF_INET6) so Python's synchronous/async
# httpcore socket connections do not hang 75s on blackholed IPv6 routes.
_ORIG_GETADDRINFO = socket.getaddrinfo


def _prefer_ipv4_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    results = _ORIG_GETADDRINFO(host, port, family, type, proto, flags)
    ipv4 = [r for r in results if r[0] == socket.AF_INET]
    ipv6 = [r for r in results if r[0] != socket.AF_INET]
    return ipv4 + ipv6


socket.getaddrinfo = _prefer_ipv4_getaddrinfo

# Load .env from agent/ directory if present, then current working directory.
_AGENT_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
if _AGENT_ENV_PATH.exists():
    load_dotenv(_AGENT_ENV_PATH)
load_dotenv()

DEFAULT_MODEL_ID = "gemini-2.5-flash"

# On Google AI Studio Free Tier, rate limits (RPM/RPD) are enforced per-model.
# Rotating and falling back across healthy Flash models avoids 429 bottlenecks.
FREE_TIER_MODEL_POOL: tuple[str, ...] = (
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3.5-flash",
    "gemini-3-flash-preview",
    "gemini-2.5-flash",
)
_model_cycle = itertools.cycle(FREE_TIER_MODEL_POOL)
_model_cooldown_until: dict[str, float] = {}


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
    """Return the configured primary Gemini model ID."""
    return os.environ.get("GEMINI_MODEL", DEFAULT_MODEL_ID).strip() or DEFAULT_MODEL_ID


def next_free_tier_model() -> str:
    """Return the next model in the Free Tier rotation pool (or primary model on Vertex AI)."""
    if is_vertex_ai_enabled() or os.environ.get("GEMINI_MODEL", "").strip():
        return get_model_id()
    import time

    now = time.monotonic()
    for _ in range(len(FREE_TIER_MODEL_POOL)):
        candidate = next(_model_cycle)
        if _model_cooldown_until.get(candidate, 0.0) <= now:
            return candidate
    return next(_model_cycle)


def get_genai_client(
    attempts: int = 2,
    initial_delay: float = 1.5,
    max_delay: float = 10.0,
) -> genai.Client:
    """Create a google.genai.Client configured for Google AI Studio Free Tier or Vertex AI."""
    configure_genai_env()

    if is_vertex_ai_enabled():
        http_options = HttpOptions(
            retry_options=HttpRetryOptions(
                attempts=attempts,
                initial_delay=initial_delay,
                max_delay=max_delay,
                exp_base=2,
            )
        )
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

    # On Free Tier, use attempts=1 at the HTTP layer so any 429 immediately
    # triggers model rotation in generate_content_with_fallback instead of
    # sleeping 30-60s on the same rate-limited model.
    free_http_options = HttpOptions(
        retry_options=HttpRetryOptions(
            attempts=1,
            initial_delay=0.5,
            max_delay=1.0,
            exp_base=2,
        )
    )
    return genai.Client(
        vertexai=False,
        api_key=api_key,
        http_options=free_http_options,
    )


def generate_content_with_fallback(
    client: genai.Client,
    *,
    contents: Any,
    config: GenerateContentConfig | None = None,
    preferred_model: str | None = None,
):
    """Call generate_content and automatically rotate across Free Tier Flash models on 429/503/404."""
    start_model = preferred_model or next_free_tier_model()
    if is_vertex_ai_enabled():
        return client.models.generate_content(
            model=start_model,
            contents=contents,
            config=config,
        )

    import time

    now = time.monotonic()
    active_pool = [
        m
        for m in FREE_TIER_MODEL_POOL
        if m != start_model and _model_cooldown_until.get(m, 0.0) <= now
    ]
    cooled_pool = [
        m
        for m in FREE_TIER_MODEL_POOL
        if m != start_model and _model_cooldown_until.get(m, 0.0) > now
    ]
    candidates = [start_model] + active_pool + cooled_pool
    last_error: Exception | None = None
    for pass_idx in range(2):
        for model_name in candidates:
            try:
                return client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config,
                )
            except Exception as err:  # noqa: BLE001
                last_error = err
                msg = str(err)
                if any(
                    code in msg
                    for code in (
                        "429",
                        "RESOURCE_EXHAUSTED",
                        "503",
                        "UNAVAILABLE",
                        "404",
                        "NOT_FOUND",
                    )
                ):
                    _model_cooldown_until[model_name] = time.monotonic() + 60.0
                    continue
                raise
        if pass_idx == 0:
            time.sleep(2.0)
    assert last_error is not None
    raise last_error

