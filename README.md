# studio scout

> an agentic location-scouting workspace that turns a screenplay pdf into evidence-backed filming-location recommendations, production risks, and a usable shoot-plan dashboard.

[live application](https://studio-scout-922011529524.asia-south1.run.app) · [judge guide](docs/judge-verification-adk-parallel.md) · [submission checklist](docs/submission-checklist.md)

## the problem and solution

location scouting requires a team to translate creative scene requirements into real places, then validate feasibility, permits, cost, logistics, continuity, and evidence. studio scout shortens that research loop. it is decision support for filmmakers and studio crews, not a replacement for a location manager, permit authority, or safety review.

upload a screenplay pdf, choose a research region, and studio scout:

1. extracts scene-level screenplay data with gemini.
2. uses google adk to coordinate script-breakdown, location-grounding, and logistics/risk agents.
3. calls parallel search at runtime for current, source-backed candidate research.
4. merges the structured agent report with deterministic scoring and conflict detection.
5. streams progress to a react dashboard with evidence-linked recommendations.

## hackathon alignment

studio scout is for the **parallel track** of [agentic cinema: the blockbuster hackathon](https://agentic-cinema.devpost.com/).

| requirement | implementation evidence |
| --- | --- |
| media workflow | screenplay-to-location-scouting workflow for filmmakers and production teams |
| multi-agent system | [`agent/app/agents/orchestrator.py`](agent/app/agents/orchestrator.py) registers three google adk `agenttool` agents |
| google cloud and gemini | `google-adk` and `google-genai` run gemini through vertex ai; the web app runs on cloud run |
| active partner use | [`parallel_search.py`](agent/app/tools/parallel_search.py) calls the official `parallel-web` sdk at runtime; the research stage also configures `toolparallelaisearch` |
| web platform | react frontend served by fastapi from one cloud run container |
| reproducibility | source, mit license, dockerfile, cloud build configuration, and setup instructions are included |

the [official rules](https://agentic-cinema.devpost.com/rules) require actual runtime use of google cloud and the selected partner service, a hosted project url, public open-source code, and a public english demo video of no more than three minutes. review them before final submission.

## architecture

```text
screenplay pdf + prompt + region
            |
            v
 fastapi upload api and sse progress stream
            |
            +--> gemini screenplay extraction
            +--> google adk orchestrator
            |      +--> script breakdown
            |      +--> location grounding --> parallel search
            |      `--> logistics and risk
            `--> deterministic research, scoring, and conflict detection
                         |
                         v
              evidence-linked shoot plan in react dashboard
```

## judge quick start

open https://studio-scout-922011529524.asia-south1.run.app, upload a screenplay pdf, and enter a region-specific prompt such as `find filming locations in new jersey`. observe the streamed workflow, then inspect candidates, scores, conflicts, and evidence links. use the [judge guide](docs/judge-verification-adk-parallel.md) for source-level and runtime proof.

## local development

requirements: python 3.13, [uv](https://docs.astral.sh/uv/), node.js, a vertex ai project, application default credentials, and a parallel api key.

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

the root [`dockerfile`](dockerfile) is a multi-stage build: node compiles react, then the final python image serves the api and static dashboard. [`cloudbuild.yaml`](cloudbuild.yaml) explicitly uses that lowercase filename. the deployed cloud run service is in `asia-south1`; it uses vertex ai in `global` and injects `PARALLEL_API_KEY` from secret manager.

cloud run filesystem storage is ephemeral. uploaded screenplays and generated artifacts are not durable after an instance is replaced.

## documentation

- [implementation summary](docs/implementation-summary.md)
- [judge verification guide](docs/judge-verification-adk-parallel.md)
- [agent guide](agent/README.md)
- [api and cloud run guide](api/README.md)

## license

released under the [mit license](LICENSE).
