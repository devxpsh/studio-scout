# studio scout agent service

this directory contains the google adk multi-agent workflow and deterministic location-intelligence pipeline.

## responsibilities

- extract structured scenes from a screenplay pdf.
- orchestrate script breakdown, location grounding, and logistics/risk agents.
- call parallel search for current location evidence.
- research, score, de-duplicate, and flag location conflicts.
- emit `agent_report.json` and `recommendations.json` as runtime artifacts.

## setup and verification (free tier)

```bash
uv sync
cp .env.example .env
# Set GEMINI_API_KEY (from https://aistudio.google.com/apikey) in .env
uv run python -m app.demo_trace
```

by default, [`app/genai_client.py`](app/genai_client.py) configures `google-genai` and `google-adk` to use the **google ai studio free tier** (`GEMINI_API_KEY`, `GOOGLE_GENAI_USE_VERTEXAI=False`, `gemini-2.5-flash`). if `PARALLEL_API_KEY` is set, [`app/tools/parallel_search.py`](app/tools/parallel_search.py) queries the `parallel-web` sdk directly; otherwise [`app/location/research/search.py`](app/location/research/search.py) automatically falls back to built-in `GoogleSearch` grounding. vertex ai remains supported as an opt-in mode by setting `GOOGLE_GENAI_USE_VERTEXAI=True` and `GOOGLE_CLOUD_PROJECT`. generated files in `data/` must not be committed.
