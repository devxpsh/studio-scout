# studio scout

> an agentic location-scouting workspace that turns a screenplay pdf into evidence-backed filming-location recommendations, production risks, and an interactive shoot-plan dossier.

[live application](https://studio-scout-922011529524.asia-south1.run.app) · [implementation summary](docs/implementation-summary.md)

## the problem and solution

location scouting requires a team to translate creative scene requirements into real places, then validate feasibility, permits, cost, logistics, continuity, and evidence. studio scout shortens that research loop. it is decision support for filmmakers and studio crews, not a replacement for a location manager, permit authority, or safety review.

upload a screenplay pdf, choose a target shooting region (or explore the built-in sample dossier), and studio scout:

1. extracts scene-level screenplay data with gemini (cached by sha-256 pdf content hash to skip redundant re-parsing across regional runs).
2. uses google adk in an isolated per-run workspace to coordinate script-breakdown, location-grounding, and logistics/risk agents.
3. calls parallel search at runtime for current, source-backed candidate research.
4. reuses grounded adk candidates when sufficient and parallelizes per-scene research and 6-axis deterministic scoring (`ThreadPoolExecutor`).
5. streams real-time progress via server-sent events (sse) to a 35mm contact-sheet react dashboard with google maps deep links and csv/json call-sheet exports.

## technical overview

| capability | implementation |
| --- | --- |
| media workflow | screenplay-to-location-scouting workflow for filmmakers and pre-production teams |
| multi-agent system | [`agent/app/agents/orchestrator.py`](agent/app/agents/orchestrator.py) coordinates `ScriptBreakdownAgent`, `LocationGrounder`, and `LogisticsRiskAssessor` |
| google cloud and gemini | `google-adk` and `google-genai` run gemini through vertex ai; the web app runs on google cloud run (`asia-south1`) |
| grounded web search | [`parallel_search.py`](agent/app/tools/parallel_search.py) calls the official `parallel-web` sdk at runtime; fallback research configures `ToolParallelAiSearch` |
| concurrency & caching | sha-256 pdf extraction caching (`agent/data/cache/`), `ContextVar`-isolated per-run workspaces (`agent/data/runs/<run_id>/`), and parallel scene research/scoring |
| web platform & exports | editorial react + typescript frontend with 5-section intake desk, sample dossier preview, scene search/filters, google maps deep links, and csv/json export |

## architecture

```text
screenplay pdf + prompt + region
            |
            v
 fastapi upload api & sse stream (per-run workspace + sha-256 pdf cache)
            |
            +--> gemini screenplay extraction (or sha-256 cache hit)
            +--> google adk orchestrator (ContextVar-bound screenplay.json)
            |      +--> script breakdown
            |      +--> location grounding --> parallel web search
            |      `--> logistics and risk assessment
            `--> in-process parallel research, 6-axis scoring & conflict solver
                         |
                         v
      streamed shoot_plan + interactive dossier (csv/json export + maps)
```

## quick start

open https://studio-scout-922011529524.asia-south1.run.app:
- click **sample dossier** in the top bar (or **explore sample dossier →** in the hero) to inspect a complete multi-scene grounded shoot plan immediately.
- or drop a screenplay pdf into the intake terminal, pick a target shooting region (e.g. `New Jersey`, `Bay Area, California`, `London, UK`, `Mumbai, India`), add optional constraint presets, and launch a live location scout.

## local development

requirements: python 3.13, [uv](https://docs.astral.sh/uv/), node.js 22+, a vertex ai project, application default credentials, and a parallel api key.

```bash
cp agent/.env.example agent/.env
cd agent && uv sync
cd ../api && uv sync
cd ../frontend && npm ci
```

set `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION=global`, `GOOGLE_GENAI_USE_VERTEXAI=True`, and `PARALLEL_API_KEY` in `agent/.env`, then run `gcloud auth application-default login`.

in separate terminals:

```bash
cd api && uv run uvicorn main:app --reload --port 8000
cd frontend && npm run dev
```

the frontend targets `http://localhost:8000` in development and same-origin api routes in the production container.

## deployment

the root [`dockerfile`](dockerfile) is a multi-stage build: node compiles the react bundle and seo/static assets, then the final python image serves fastapi and the static frontend. [`cloudbuild.yaml`](cloudbuild.yaml) builds the container image and publishes it to artifact registry (`asia-south1-docker.pkg.dev/studio-scout-506216/studio-scout/app:latest`), which is deployed to cloud run in `asia-south1`.

```bash
gcloud builds submit --config cloudbuild.yaml \
  --substitutions _IMAGE=asia-south1-docker.pkg.dev/studio-scout-506216/studio-scout/app:latest .
gcloud run deploy studio-scout \
  --image asia-south1-docker.pkg.dev/studio-scout-506216/studio-scout/app:latest \
  --region asia-south1 --platform managed
```

## documentation

- [implementation summary](docs/implementation-summary.md)
- [agent guide](agent/README.md)
- [api and cloud run guide](api/README.md)
- [frontend guide](frontend/README.md)

## license

released under the [mit license](LICENSE).