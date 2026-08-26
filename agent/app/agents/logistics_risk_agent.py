"""
Studio Scout — Phase 03
Logistics & Risk Engine.

Takes location-grounding evidence for a scene and flags basic logistics
and risk signals. Pure reasoning agent -- no external tool. It must not
invent facts beyond what the grounding evidence already established.
"""

from google.adk.agents import Agent
from google.adk.workflow._retry_config import RetryConfig

RETRY_CONFIG = RetryConfig(
    max_attempts=5,
    initial_delay=2.0,
    max_delay=30.0,
    backoff_factor=2.0,
    jitter=0.5,
)

logistics_risk_agent = Agent(
    name="logistics_risk_agent",
    model="gemini-2.5-flash",
    description=(
        "Reviews location-grounding research for a scene and flags "
        "logistics, permit, access, and risk considerations."
    ),
    instruction=(
        "You are the Logistics & Risk Engine for Studio Scout. You will be "
        "given a scene's requirements (setting, time_of_day, description) "
        "and the location-grounding research already gathered for it "
        "(candidate real-world locations and whatever permit/access "
        "information was found).\n\n"
        "Your job:\n"
        "1. For each candidate location, flag logistics considerations "
        "implied by the scene itself -- e.g. night shoots need lighting "
        "and crew safety planning; crowded public exteriors need crowd "
        "control and permits; interiors in commercial/abandoned "
        "properties need access and liability coverage.\n"
        "2. Note any permit or access risk explicitly mentioned in the "
        "grounding research. If the grounding research found no permit "
        "information, say that plainly rather than guessing.\n"
        "3. Give each candidate a rough qualitative risk level (low / "
        "medium / high) with a one-line justification grounded only in "
        "what you were given.\n"
        "4. Do not invent locations, permits, costs, or regulations that "
        "were not part of the input. If you lack enough information to "
        "assess a factor, say so instead of fabricating a plausible-"
        "sounding answer."
    ),
    tools=[],
    retry_config=RETRY_CONFIG,
)