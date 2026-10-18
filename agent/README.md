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
uv run python -m app.demo_trace
```

[`app/genai_client.py`](app/genai_client.py) configures `google-genai` and `google-adk` using `GEMINI_API_KEY` (`GOOGLE_GENAI_USE_VERTEXAI=False`) with automatic multi-model flash fallback. [`app/tools/parallel_search.py`](app/tools/parallel_search.py) queries the `parallel-web` sdk when `PARALLEL_API_KEY` is configured, and [`app/location/research/search.py`](app/location/research/search.py) falls back to `GoogleSearch` grounding if omitted. vertex ai is also supported by setting `GOOGLE_GENAI_USE_VERTEXAI=True` and `GOOGLE_CLOUD_PROJECT`. generated files in `data/` must not be committed.

