"""
Studio Scout — Phase 03
Location & Permit Grounding Agent.

Takes a scene's location/setting/time_of_day/description (plus a region
supplied by the caller at invocation time) and uses parallel_search to
research real-world shooting-location candidates. Region is NOT hardcoded
here -- the orchestrator passes it per-run as part of the request text
when it calls this agent via AgentTool.
"""

from google.adk.agents import Agent
from google.adk.workflow._retry_config import RetryConfig

from app.agents.tracing import trace_after_tool, trace_before_tool
from app.tools.parallel_search import parallel_search

RETRY_CONFIG = RetryConfig(
    max_attempts=5,
    initial_delay=2.0,
    max_delay=30.0,
    backoff_factor=2.0,
    jitter=0.5,
)

location_grounding_agent = Agent(
    name="location_grounding_agent",
    model="gemini-2.5-flash",
    description=(
        "Researches real-world film shooting locations for a single scene, "
        "grounded in current web search results via the parallel_search tool."
    ),
    instruction=(
        "You are the Location & Permit Grounding Agent for Studio Scout. "
        "You will be given a scene's location description, setting "
        "(interior/exterior), time of day, a short scene description, and "
        "a target region to search within.\n\n"
        "Your job:\n"
        "1. Formulate a specific, well-targeted search query that includes "
        "the given region -- do not search without a region anchor.\n"
        "2. Call the parallel_search tool with that query whenever you need "
        "current, factual information you don't already know.\n"
        "3. From the results, identify 1-3 real-world candidate locations "
        "or location types that plausibly match the scene's requirements.\n"
        "4. For each candidate, briefly note any permit, access, or "
        "availability information the search results surfaced, if any.\n"
        "5. Base your answer only on what the search results actually "
        "say. Do not invent locations, permits, or details that are not "
        "supported by the retrieved evidence. If results are insufficient, "
        "say so explicitly rather than guessing.\n"
        "6. Mention the source (title/url) for each claim you make."
    ),
    tools=[parallel_search],
    retry_config=RETRY_CONFIG,
    before_tool_callback=trace_before_tool,
    after_tool_callback=trace_after_tool,
)