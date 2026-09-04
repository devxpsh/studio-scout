# Studio Scout Implementation Summary

## Product Flow

Studio Scout accepts a screenplay PDF and an optional instruction such as `Find filming locations in New Jersey`. The frontend sends both values to the FastAPI bridge, which streams progress events while the backend prepares a fresh shoot plan.

## Backend Changes

- Added `POST /api/upload` for multipart PDF uploads.
- Added prompt and optional region fields to upload requests.
- Added region clarification when the request does not identify a research region.
- Added PDF persistence and structured screenplay extraction through the existing agent environment.
- Added bounded Vertex AI retry handling for transient `429 RESOURCE_EXHAUSTED` responses.
- Added region-aware location research instead of relying only on a hardcoded region.
- Added automatic execution of the deterministic location pipeline after extraction.
- Added serialized upload runs because the pipeline currently writes shared files under `agent/data`.
- Added SSE progress events for extraction, agent activity, scoring, and report completion.
- Captured the ADK orchestrator's structured `StudioScoutReport` over SSE and displayed its synthesis, region, and source alongside the scored plan.
- Persisted the ADK report as an intermediate artifact and passed it into the scoring pipeline with `--agent-report`.
- Made ADK tracing optional so a trace dependency failure does not prevent report generation.
- Added `GET /api/health` to show the interpreter and `uv` executable used by the running API.
- Added a helpful `GET /api/upload` response for direct browser visits.

## Frontend Changes

- Added a PDF upload form with selected-file feedback.
- Added a free-form scouting prompt field.
- Added live processing events to the agent trace view.
- Added region clarification input during processing.
- Added cancellation handling for React development effect replay.
- Prevented stale recommendation data from being used after a failed upload.
- Added explicit backend failure messaging.
- Kept the dashboard contract aligned with the Python `ShootPlan` schema.

## Data and Pipeline

The report pipeline is:

```text
PDF
-> extracted screenplay text
-> structured screenplay scenes
-> scene location requirements
-> Parallel-grounded location research
-> candidate scoring
-> conflict detection
-> ShootPlan
-> recommendations.json
-> dashboard
```

The dashboard uses the generated `agent/data/recommendations.json` artifact. Client-side code does not recompute candidate composite scores.

The dashboard now presents one combined run: the ADK report supplies the agent-generated synthesis and candidate seed data, while the deterministic `ShootPlan` uses those candidates plus fresh Parallel results for numeric rankings and conflict enrichment.

## Repository Hygiene

Added a root `.gitignore` for:

- Python virtual environments and caches
- Frontend dependencies and build output
- macOS metadata
- Uploaded screenplay PDFs
- Local VS Code state

Low-value and stale source comments were removed. Comments that explain non-obvious behavior, such as retry policy, lazy AI imports, and React Strict Mode cancellation, were retained.

## Validation Performed

- Frontend production build with `npm run build`
- API Python compilation
- Agent Python compilation
- Direct screenplay extraction against the project PDF
- SSE region-clarification path verification
- API health endpoint verification
