# studio scout agent service

this directory contains the google adk multi-agent workflow and deterministic location-intelligence pipeline.

## responsibilities

- extract structured scenes from a screenplay pdf.
- orchestrate script breakdown, location grounding, and logistics/risk agents.
- call parallel search for current location evidence.
- research, score, de-duplicate, and flag location conflicts.
- emit `agent_report.json` and `recommendations.json` as runtime artifacts.

## setup and verification

```bash
uv sync
cp .env.example .env
gcloud auth application-default login
uv run python -m app.demo_trace
```

set `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, `GOOGLE_GENAI_USE_VERTEXAI=True`, and `PARALLEL_API_KEY` in `.env` first.

key files: `app/agents/orchestrator.py` defines the adk sequence, `app/tools/parallel_search.py` calls the official parallel sdk, and `app/location/research/search.py` configures vertex ai and parallel grounding. generated files in `data/` must not be committed.

see the root [judge guide](../docs/judge-verification-adk-parallel.md) for full verification.
