# studio scout

> an agentic location-scouting workspace that turns a screenplay pdf into evidence-backed filming-location recommendations, production risks, and an interactive shoot-plan dossier.

[live application](https://studio-scout-j78x.onrender.com/) · [implementation summary](docs/implementation-summary.md)

## the problem and solution

location scouting requires a team to translate creative scene requirements into real places, then validate feasibility, permits, cost, logistics, continuity, and evidence. studio scout shortens that research loop. it is decision support for filmmakers and studio crews, not a replacement for a location manager, permit authority, or safety review.

upload a screenplay pdf, choose a target shooting region (or explore the built-in sample dossier), and studio scout:

1. extracts scene-level screenplay data with gemini (cached by sha-256 pdf content hash to skip redundant re-parsing across regional runs).
2. uses google adk in an isolated per-run workspace to coordinate script-breakdown, location-grounding, and logistics/risk agents.
3. calls parallel search at runtime for current, source-backed candidate research.
4. batches candidate extraction and 6-axis deterministic scoring across scenes for fast, consistent multi-scene turnaround.
5. streams real-time progress and keepalive heartbeats via server-sent events (sse) to a 35mm contact-sheet react dashboard with google maps deep links and csv/json call-sheet exports.

> **run guidance**: a standard run with **5 scenes takes ~1–3 minutes** to complete full breakdown, live web grounding, and 6-axis scoring. for optimal speed and scouting depth, running **up to 5 scenes at a time** is recommended.

## technical overview

| capability | implementation |
| --- | --- |
| media workflow | screenplay-to-location-scouting workflow for filmmakers and pre-production teams |
| multi-agent system | [`agent/app/agents/orchestrator.py`](agent/app/agents/orchestrator.py) coordinates `ScriptBreakdownAgent`, `LocationGrounder`, and `LogisticsRiskAssessor` |
| google gemini & adk | [`agent/app/genai_client.py`](agent/app/genai_client.py) runs `google-adk` and `google-genai` via the gemini api (`GEMINI_API_KEY`) with automatic multi-model flash fallback and cooldown caching (plus optional vertex ai support) |
| grounded web search | [`parallel_search.py`](agent/app/tools/parallel_search.py) queries the `parallel-web` sdk at runtime for live regional venue citations (with automatic `GoogleSearch` grounding fallback) |
| concurrency & caching | sha-256 pdf extraction caching (`agent/data/cache/`), `ContextVar`-isolated per-run workspaces (`agent/data/runs/<run_id>/`), and batched multi-scene research/scoring |
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

## local development

requirements: python 3.13, [uv](https://docs.astral.sh/uv/), node.js 22+, a gemini api key (`GEMINI_API_KEY`), and a parallel search api key (`PARALLEL_API_KEY`).

```bash
cp agent/.env.example agent/.env
cd agent && uv sync
cd ../api && uv sync
cd ../frontend && npm ci
```

set `GEMINI_API_KEY` and `PARALLEL_API_KEY` in `agent/.env`:

```env
GEMINI_API_KEY=your-gemini-api-key
GOOGLE_GENAI_USE_VERTEXAI=False
PARALLEL_API_KEY=your-parallel-api-key
```

in separate terminals:

```bash
cd api && uv run uvicorn main:app --reload --port 8000
cd frontend && npm run dev
```

the frontend targets `http://localhost:8000` in development and same-origin api routes in the production container.

## deployment

the root [`Dockerfile`](Dockerfile) is a multi-stage build: node compiles the react bundle and static/seo assets, then the python runtime image serves fastapi and the compiled frontend on a single origin. the production service is deployed on render via [`render.yaml`](render.yaml) at https://studio-scout-j78x.onrender.com/.

## documentation

- [implementation summary](docs/implementation-summary.md)
- [agent guide](agent/README.md)
- [api guide](api/README.md)
- [frontend guide](frontend/README.md)

## license

released under the [mit license](LICENSE).