# judge verification guide: google adk, vertex ai, and parallel

this guide provides direct evidence that studio scout uses google cloud ai services and parallel at runtime.

## deployed application

- application: https://studio-scout-922011529524.asia-south1.run.app
- health: https://studio-scout-922011529524.asia-south1.run.app/api/health

upload a screenplay pdf and use a region-specific prompt. expected behavior: streamed extraction and agent events, then ranked candidates, conflict flags, and evidence links in the dashboard.

## google cloud evidence

| evidence | source |
| --- | --- |
| adk root agent | [`agent/app/agent.py`](../agent/app/agent.py) |
| three-agent orchestration with `agenttool` | [`agent/app/agents/orchestrator.py`](../agent/app/agents/orchestrator.py) |
| gemini vertex ai client | [`agent/app/location/research/search.py`](../agent/app/location/research/search.py) |
| cloud run container | [`dockerfile`](../dockerfile) |
| cloud build configuration | [`cloudbuild.yaml`](../cloudbuild.yaml) |

the orchestrator registers script-breakdown, location-grounding, and logistics/risk agents using google adk. the research pipeline creates `genai.client(vertexai=true, project=..., location=...)`; the deployed web application runs on cloud run.

```bash
cd agent
uv sync
uv run python -c "import google.adk, google.genai; print(google.adk.__file__); print(google.genai.__file__)"
```

## parallel evidence

[`agent/app/tools/parallel_search.py`](../agent/app/tools/parallel_search.py) directly uses the official sdk:

```python
from parallel import Parallel
result = client.search(search_queries=[query], mode="basic")
```

the deterministic research path also configures `toolparallelaisearch`. to test the sdk path with a valid key:

```bash
cd agent
uv run python - <<'PY'
from app.tools.parallel_search import parallel_search
for item in parallel_search("new jersey filming location warehouse"):
    print(item["source"], item["title"], item["url"])
PY
```

the output is live parallel data, not a fixture. for a complete trace, run `uv run python -m app.demo_trace` from `agent/`.

## judging-criteria mapping

| criterion | evidence |
| --- | --- |
| technological implementation | adk orchestration, vertex ai gemini, active parallel search, deterministic scoring, cloud run |
| design | complete upload-to-dashboard flow with progress, evidence, scores, and conflicts |
| potential impact | converts screenplay requirements into reviewable production research |
| quality of idea | combines creative location fit with operational feasibility rather than generic suggestions |

## constraints

- live research requires vertex ai and parallel credentials.
- recommendations require human permit, availability, cost, and safety confirmation.
- cloud run local storage is ephemeral.

