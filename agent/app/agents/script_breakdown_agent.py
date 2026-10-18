"""
Studio Scout — Phase 03
Script Breakdown Agent.

Loads the already-validated data/screenplay.json (produced by Phase 02)
and exposes it to the orchestrator as scene-level research requirements.
Does NOT re-run PDF extraction or Gemini structured extraction -- that
work is already done and validated; this agent's job is to serve it.
"""

from contextvars import ContextVar
import json
from pathlib import Path

from google.adk.agents import Agent
from google.adk.workflow._retry_config import RetryConfig

from app.agents.tracing import trace_after_tool, trace_before_tool
from app.genai_client import configure_genai_env, get_model_id

configure_genai_env()

RETRY_CONFIG = RetryConfig(
    max_attempts=5,
    initial_delay=2.0,
    max_delay=30.0,
    backoff_factor=2.0,
    jitter=0.5,
)

SCREENPLAY_JSON_PATH = Path(__file__).resolve().parents[2] / "data" / "screenplay.json"
CURRENT_SCREENPLAY_JSON_PATH: ContextVar[Path | None] = ContextVar(
    "current_screenplay_json_path", default=None
)


def get_screenplay_breakdown() -> dict:
    """Load the validated screenplay.json and return its structured scene data.

    Returns a dict with 'title' and 'scenes', where each scene includes
    scene_number, slugline, setting, location, time_of_day, description,
    characters, and dialogue -- exactly as produced by the Phase 02 pipeline.
    """
    target_path = CURRENT_SCREENPLAY_JSON_PATH.get() or SCREENPLAY_JSON_PATH
    if not target_path.exists():
        return {
            "error": (
                f"screenplay.json not found at {target_path}. "
                "Run Phase 02's build_fixture.py first."
            )
        }

    with open(target_path, "r", encoding="utf-8") as f:
        return json.load(f)


script_breakdown_agent = Agent(
    name="script_breakdown_agent",
    model=get_model_id(),
    description=(
        "Serves the structured screenplay breakdown -- scenes, locations, "
        "settings, and time-of-day -- as research requirements for other "
        "agents in the Studio Scout pipeline."
    ),
    instruction=(
        "You are the Script Breakdown Agent for Studio Scout. Call "
        "get_screenplay_breakdown to load the structured screenplay data. "
        "When asked for scene research requirements, return each scene's "
        "scene_number, location, setting, time_of_day, and a short summary "
        "of description -- this is what other agents will use to research "
        "real-world shooting locations. Do not invent scenes, locations, "
        "or details that are not present in the loaded data."
    ),
    tools=[get_screenplay_breakdown],
    retry_config=RETRY_CONFIG,
    before_tool_callback=trace_before_tool,
    after_tool_callback=trace_after_tool,
)