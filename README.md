# studio scout

> an agentic location-scouting workspace that turns a screenplay pdf into evidence-backed filming-location recommendations, production risks, and an interactive shoot-plan dossier.

[live application](https://studio-scout-j78x.onrender.com/) · [implementation summary](docs/implementation-summary.md)

## the problem and solution

location scouting requires a team to translate creative scene requirements into real places, then validate feasibility, permits, cost, logistics, continuity, and evidence. studio scout shortens that research loop. it is decision support for filmmakers and studio crews, not a replacement for a location manager, permit authority, or safety review.

upload a screenplay pdf, choose a target shooting region (or explore the built-in sample dossier), and studio scout:

1. extracts scene-level screenplay data with gemini (cached by sha-256 pdf content hash to skip redundant re-parsing across regional runs).
2. uses google adk in an isolated per-run workspace to coordinate script-breakdown, location-grounding, and logistics/risk agents.
3. calls parallel search at runtime for current, source-backed candidate research.
4. batches candidate extraction and 6-axis deterministic scoring across scenes to stay well within free-tier rate limits (`4` total llm calls per 5-scene run).
5. streams real-time progress and keepalive heartbeats via server-sent events (sse) to a 35mm contact-sheet react dashboard with google maps deep links and csv/json call-sheet exports.

> **run guidance**: a standard run with **5 scenes takes ~1–3 minutes** to complete full breakdown, live web grounding, and 6-axis scoring. for optimal speed and free-tier quota reliability, we recommend running **up to 5 scenes at a time**.

## technical overview

| capability | implementation |
| --- | --- |
| media workflow | screenplay-to-location-scouting workflow for filmmakers and pre-production teams |
| multi-agent system | [`agent/app/agents/orchestrator.py`](agent/app/agents/orchestrator.py) coordinates `ScriptBreakdownAgent`, `LocationGrounder`, and `LogisticsRiskAssessor` |
| google gemini & adk | [`agent/app/genai_client.py`](agent/app/genai_client.py) runs `google-adk` and `google-genai` on the **google ai studio free tier** (`GEMINI_API_KEY`) with automatic multi-model flash rotation and cooldown caching |
| grounded web search | [`parallel_search.py`](agent/app/tools/parallel_search.py) queries the `parallel-web` sdk directly on free tier (with automatic fallback to built-in `GoogleSearch` grounding if `PARALLEL_API_KEY` is omitted) |
| concurrency & caching | sha-256 pdf extraction caching (`agent/data/cache/`), `ContextVar`-isolated per-run workspaces (`agent/data/runs/<run_id>/`), and batched scene research/scoring |
| web platform & exports | editorial react + typescript frontend with 5-section intake desk, sample dossier preview, scene search/filters, google maps deep links, and csv/json export |

## architecture

```text
screenplay pdf + prompt + region
            |
            v
 fastapi upload api & sse stream (per-run workspace + sha-256 pdf cache + 4s keepalive)
            |
            +--> gemini screenplay extraction (or sha-256 cache hit)
            +--> multi-agent pipeline (ContextVar-bound screenplay.json)
            |      +--> script breakdown (structured scene requirements)
            |      +--> location grounding --> parallel web search + batched candidate extraction
            |      +--> logistics & 6-axis rubric scoring (batched across scenes)
            |      `--> orchestrator shoot-plan synthesis & conflict detection
            `--> streamed agent_report + shoot_plan + interactive dossier (csv/json export + maps)
```

## quick start

open https://studio-scout-j78x.onrender.com/:
- click **sample dossier** in the top bar (or **explore sample dossier →** in the hero) to inspect a complete multi-scene grounded shoot plan immediately.
- or drop a screenplay pdf (recommended: up to 5 scenes per run, ~1–3 min turnaround) into the intake terminal, pick a target shooting region (e.g. `New Jersey`, `Bay Area, California`, `London, UK`, `Mumbai, India`), add optional constraint presets, and launch a live location scout.

## local development (free tier — zero gcp billing)

requirements: python 3.13, [uv](https://docs.astral.sh/uv/), node.js 22+, and a free [google ai studio api key](https://aistudio.google.com/apikey) (`GEMINI_API_KEY`).

```bash
cp agent/.env.example agent/.env
cd agent && uv sync
cd ../api && uv sync
cd ../frontend && npm ci
```

set `GEMINI_API_KEY` (and optional `PARALLEL_API_KEY`) in `agent/.env`:

```env
GEMINI_API_KEY=your-free-ai-studio-key
GOOGLE_GENAI_USE_VERTEXAI=False
PARALLEL_API_KEY=your-parallel-api-key   # optional; falls back to Google Search grounding
```

in separate terminals:

```bash
cd api && uv run uvicorn main:app --reload --port 8000
cd frontend && npm run dev
```

the frontend targets `http://localhost:8000` in development and same-origin api routes in the production container.

## deployment (render free tier)

the live application is deployed at https://studio-scout-j78x.onrender.com/ using [`render.yaml`](render.yaml) as a free docker web service on [render](https://render.com) with zero gcp billing required:
1. connect your `studio-scout` github repository on render (**new -> blueprint**).
2. enter your free `GEMINI_API_KEY` (and optional `PARALLEL_API_KEY`) when prompted.

## documentation

- [implementation summary](docs/implementation-summary.md)
- [agent guide](agent/README.md)
- [api guide](api/README.md)
- [frontend guide](frontend/README.md)

## license

released under the [mit license](LICENSE).