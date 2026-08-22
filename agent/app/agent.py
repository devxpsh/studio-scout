from google.adk.agents import Agent
from app.tools.parallel_search import parallel_search

root_agent = Agent(
    name="studio_scout",
    model="gemini-2.5-flash",
    description="Studio Scout - an agent that helps find film shooting locations.",
    instruction=(
        "You are Studio Scout, an assistant that helps filmmakers find"
        "shooting locations, permits, and relevant film production info. "
        "Use the parallel_search tool whenever you need current, factual "
        "information you don't already know. Base your answers on the "
        "search results, and mention sources when relevant."
    ),
    tools=[parallel_search],
)