# Judge Verification: Google ADK and Parallel Search

This guide shows how to verify that Studio Scout genuinely uses Google ADK and Parallel Search at runtime. The integrations are implemented in source code and can also be demonstrated with live tool-call output.

## What Is Being Verified

Studio Scout uses two related execution paths:

1. **Google ADK orchestration** coordinates the Script Breakdown Agent, Location & Permit Grounding Agent, and Logistics & Risk Agent.
2. **Parallel Search** supplies current web research for real-world filming locations and evidence.

There are two Parallel integrations in the repository:

- The ADK grounding agent exposes the `parallel_search` function, implemented with the official `parallel-web` Python client.
- The deterministic location pipeline configures Vertex AI's `ToolParallelAiSearch` for grounded candidate research.

## 1. Verify Dependencies

From the repository root:

```bash
cd agent
uv sync
uv run python -c "import google.adk, google.genai, parallel; print('google-adk:', google.adk.__file__); print('google-genai:', google.genai.__file__); print('parallel:', parallel.__file__)"
```

The project manifest declares the relevant dependencies in `agent/pyproject.toml`:

```toml
google-adk>=2.7.1
parallel-web>=1.3.0
```

This proves the project is not only mentioning these services in documentation; the runtime dependencies are installed and importable.

## 2. Verify Google ADK Wiring

The ADK root agent is exported from `agent/app/agent.py`:

```python
from app.agents.orchestrator import studio_scout_orchestrator as root_agent
```

The orchestrator is a real ADK `Agent` and uses real `AgentTool` instances:

```python
from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
```

It registers three agents as tools:

```python
tools=[
    AgentTool(agent=script_breakdown_agent),
    AgentTool(agent=location_grounding_agent),
    AgentTool(agent=logistics_risk_agent),
]
```

The orchestrator is therefore not a hand-written mock dispatcher. Gemini ADK decides when to invoke the registered agent tools according to the orchestrator instructions, and each sub-agent returns data to the parent agent.

The orchestrator also has a real upload callback:

```python
before_agent_callback=ingest_uploaded_screenplay
```

That callback writes the uploaded PDF and builds structured screenplay data before the agent turn proceeds.

## 3. Run the ADK Trace Demonstration

Make sure `agent/.env` contains valid Google Cloud settings and a valid `PARALLEL_API_KEY`, then run:

```bash
cd agent
uv run python -m app.demo_trace
```

The demonstration uses the real ADK runtime:

```python
runner = InMemoryRunner(agent=root_agent, app_name="studio_scout_app")

async for event in runner.run_async(
    user_id="test_user",
    session_id=session.id,
    new_message=message,
):
    ...
```

A successful run prints sections such as:

```text
TOOL CALL — Gemini invoked a tool at runtime
tool name : script_breakdown_agent

TOOL CALL — Gemini invoked a tool at runtime
tool name : location_grounding_agent

TOOL RESPONSE — actual data returned to Gemini
```

The exact number and order of calls can vary because the orchestrator processes the screenplay scene by scene.

## 4. Verify Parallel Search in the ADK Agent

The Location & Permit Grounding Agent imports and registers the real search tool:

```python
from app.tools.parallel_search import parallel_search

location_grounding_agent = Agent(
    ...,
    tools=[parallel_search],
)
```

The implementation in `agent/app/tools/parallel_search.py` uses the Parallel SDK directly:

```python
from parallel import Parallel

client = Parallel(api_key=os.environ.get("PARALLEL_API_KEY"))
result = client.search(
    search_queries=[query],
    mode="basic",
)
```

It returns actual result data to the agent, including:

- title
- URL
- excerpt
- source marked as `parallel`

For nested tools, the runtime tracer in `agent/app/agents/tracing.py` prints:

```text
NESTED TOOL CALL — parallel_search

NESTED TOOL RESPONSE — parallel_search
```

This is important because `location_grounding_agent` runs inside an `AgentTool`; without the callback, nested tool calls would not necessarily appear in the parent runner's event stream.

## 5. Verify the Parallel API Directly

With a valid `PARALLEL_API_KEY`, run this minimal live check:

```bash
cd agent
uv run python - <<'PY'
from app.tools.parallel_search import parallel_search

results = parallel_search("filming locations New Jersey abandoned warehouse")
print(f"returned {len(results)} results")
for result in results:
    print(result["source"], result["title"], result["url"])
PY
```

Expected evidence:

- The command performs a real network search.
- It returns one or more result objects.
- Each result has a real URL and `source` equal to `parallel`.

Do not print or share the API key. The key should only be loaded from the local `.env` file.

## 6. Verify Parallel in the Deterministic Pipeline

The Phase 4 research implementation also configures Vertex's Parallel grounding tool in `agent/app/location/research/search.py`:

```python
Tool(
    parallel_ai_search=ToolParallelAiSearch(
        api_key=PARALLEL_API_KEY,
        custom_configs={"mode": "basic", "max_results": 10},
    )
)
```

The actual scene query includes the user-selected region:

```text
Find real-world filming locations in <region> matching: <scene requirements>
```

The returned grounding chunks are converted into evidence URLs. Those URLs flow into candidate extraction, scoring, conflict detection, and finally `recommendations.json`.

To verify this path, run the full pipeline with a known structured screenplay:

```bash
cd agent
uv run python -m app.location.pipeline data/screenplay.json "New Jersey"
```

Then inspect the generated report:

```bash
python - <<'PY'
import json

with open("data/recommendations.json", encoding="utf-8") as file:
    plan = json.load(file)

for scene in plan["scenes"]:
    print(f"Scene {scene['scene_number']}: {scene['location']}")
    for candidate in scene["top_candidates"]:
        print(" ", candidate["candidate"]["name"])
        for evidence in candidate["candidate"]["evidence"]:
            print("   ", evidence["source_url"])
PY
```

The report should contain grounded candidate evidence URLs when the search returns supporting sources.

## 7. Verify Through the Product UI

Start the API with the API project's environment:

```bash
cd api
uv run uvicorn main:app --reload --port 8000
```

Start the frontend in another terminal:

```bash
cd frontend
npm run dev
```

Upload a PDF with an explicit region prompt, for example:

```text
Find all screenplay locations in New Jersey
```

During processing, judges can observe:

1. The screenplay extraction event.
2. Script Breakdown activity.
3. Location & Permit Grounding activity.
4. Logistics & Risk activity.
5. The final shoot-plan generation event.
6. Real evidence links in the dashboard after completion.

The browser receives progress events from `POST /api/upload` using SSE. The FastAPI bridge runs the ADK trace when available, captures the orchestrator's structured `StudioScoutReport` to `agent/data/agent_report.json`, then runs the location pipeline with `--agent-report`. The pipeline converts ADK candidates into scoring candidates, merges non-duplicate Parallel results, and performs numeric scoring and conflict enrichment. The dashboard displays the combined result.

## What Counts as Strong Proof

For a demo or judging session, show these three things together:

1. **Source proof:** open the orchestrator and `parallel_search.py` files to show the real SDK imports, agent tools, and API call.
2. **Runtime proof:** run `uv run python -m app.demo_trace` and show `TOOL CALL`, `NESTED TOOL CALL — parallel_search`, and `NESTED TOOL RESPONSE` output.
3. **Result proof:** open the final dashboard, show the `Agent synthesis` section, and click an evidence URL in the search-backed scored plan.

To verify the handoff directly, watch the API terminal for:

```text
[pipeline] consuming ADK report: data/agent_report.json
```

Then inspect `agent/data/agent_report.json` and compare one of its candidate names with the generated `recommendations.json`. The candidate should appear in the scored plan unless it was removed by a later validation or ranking rule.

This combination proves that the services are both integrated in code and invoked during execution, rather than merely appearing in the project description.

## Limitations to State Honestly

- Google Cloud Vertex AI and Parallel require valid credentials and available quota.
- A temporary Vertex `429 RESOURCE_EXHAUSTED` response can delay or stop a run; extraction has bounded retry handling.
- The ADK trace and the deterministic `ShootPlan` are separate outputs. ADK demonstrates multi-agent orchestration, while the deterministic pipeline produces the dashboard's scored plan.
- Upload runs are serialized because the current pipeline writes shared intermediate files under `agent/data`.
