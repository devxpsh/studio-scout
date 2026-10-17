# studio scout web api

fastapi provides the browser-facing api, server-sent-event (sse) progress stream, per-run workspace isolation, sha-256 pdf extraction caching, and production static-file hosting for the react frontend.

| endpoint | purpose |
| --- | --- |
| `get /api/health` | health and runtime diagnostics |
| `post /api/upload` | multipart pdf upload with `file`, optional `prompt`, and optional `region`; streams live sse trace events, `agent_report`, and final `shoot_plan` |
| `get /api/recommendations` | returns the generated shoot plan (supports optional `?run_id=<run_id>` query parameter; defaults to latest run) |
| `get /api/upload` | direct-browser usage hint |

## runtime storage layout

- `agent/data/cache/<sha256>.json` — cached `ScreenPlay` extractions keyed by pdf sha-256 hash.
- `agent/data/runs/<run_id>/` — isolated per-run workspace containing `screenplay.pdf`, `screenplay.json`, `agent_report.json`, and `recommendations.json`.
- `agent/data/recommendations.json` — latest completed shoot plan for cli and fallback compatibility.

## local run

```bash
uv sync
uv run uvicorn main:app --reload --port 8000
```

vite uses port 8000 during development. in production, fastapi mounts built react assets (`frontend/dist`) after its api routes, so the browser uses same-origin requests.

## cloud run

the deployed service is https://studio-scout-922011529524.asia-south1.run.app. cloud build uses [`cloudbuild.yaml`](../cloudbuild.yaml), which builds the lowercase [`dockerfile`](../dockerfile). production runs in `asia-south1`, uses vertex ai in `global`, and injects `PARALLEL_API_KEY` from secret manager.
