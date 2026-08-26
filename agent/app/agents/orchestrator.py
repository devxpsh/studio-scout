"""
Studio Scout — Phase 03
Orchestrator.

Root agent that coordinates the three micro-agents as explicit tools:
  script_breakdown_agent    -> structured scene requirements
  location_grounding_agent  -> real-world location research (Parallel)
  logistics_risk_agent      -> logistics/risk flags on that research

Each sub-agent is invoked deterministically via AgentTool, not via
LLM-judgment sub_agents delegation, so the runtime trace stays clean
and demonstrable (FunctionCall / FunctionResponse per sub-agent call).
"""

from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.workflow._retry_config import RetryConfig

from app.agents.ingest_upload import ingest_uploaded_screenplay
from app.agents.report_schema import StudioScoutReport
from app.agents.script_breakdown_agent import script_breakdown_agent
from app.agents.location_grounding_agent import location_grounding_agent
from app.agents.logistics_risk_agent import logistics_risk_agent

DEFAULT_REGION = None  # no silent default -- the orchestrator asks instead

# Studio Scout's multi-agent chain makes several Gemini calls per scene
# (breakdown + grounding + risk), which can burst past Vertex AI's
# per-minute quota. Retry with backoff instead of failing the whole run
# on a transient 429 RESOURCE_EXHAUSTED.
DEFAULT_RETRY_CONFIG = RetryConfig(
    max_attempts=5,
    initial_delay=2.0,
    max_delay=30.0,
    backoff_factor=2.0,
    jitter=0.5,
)

studio_scout_orchestrator = Agent(
    name="studio_scout_orchestrator",
    model="gemini-2.5-flash",
    description=(
        "Orchestrates the Studio Scout pipeline: script breakdown, "
        "location grounding, and logistics/risk assessment, scene by scene."
    ),
    instruction=(
        "You are the Studio Scout orchestrator. If the user just uploaded "
        "a screenplay PDF, it has already been processed automatically "
        "before your turn began -- its structured data is ready and "
        "waiting via script_breakdown_agent. You do not need to do "
        "anything special to handle an upload; simply proceed with the "
        "steps below.\n\n"
        "You coordinate three "
        "sub-agents to turn a screenplay into location research:\n\n"
        "1. Call script_breakdown_agent first to get the structured scene "
        "breakdown (scene_number, location, setting, time_of_day, "
        "description for every scene).\n"
        "2. Determine the target region for location research. Check "
        "both the user's message and the screenplay content itself "
        "(character names, place names, dialect, or other setting cues "
        "in the scene descriptions) for a region signal. If you find a "
        "clear signal, state what you inferred and why, then proceed. "
        "If there is no clear region signal from either source, do NOT "
        "guess or default silently -- stop and ask the user which "
        "country or region they want location research to focus on, "
        "then wait for their reply before calling "
        "location_grounding_agent for any scene.\n"
        "3. For each scene, call location_grounding_agent, passing the "
        "scene's location, setting, time_of_day, description, and the "
        "region. Do this once per scene -- do not batch multiple scenes "
        "into a single call.\n"
        "4. For each scene, take the grounding evidence you just received "
        "and call logistics_risk_agent with the scene requirements plus "
        "that evidence, to get logistics/risk flags.\n"
        "5. Synthesize a final report conforming to the required output "
        "schema: an overall_summary, the region_used and region_source, "
        "and a scene entry for every scene with its own scene_summary "
        "and full list of location candidates (each with evidence, "
        "risk_level, risk_justification, and logistics_notes). Present "
        "scenes in order.\n\n"
        "Do not skip steps or invent information -- every claim in your "
        "final report must trace back to what a sub-agent actually "
        "returned."
    ),
    tools=[
        AgentTool(agent=script_breakdown_agent),
        AgentTool(agent=location_grounding_agent),
        AgentTool(agent=logistics_risk_agent),
    ],
    retry_config=DEFAULT_RETRY_CONFIG,
    before_agent_callback=ingest_uploaded_screenplay,
    output_schema=StudioScoutReport,
    output_key="studio_scout_report",
)