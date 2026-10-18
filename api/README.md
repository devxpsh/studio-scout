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

## free-tier deployment

- **render free tier**: [`render.yaml`](../render.yaml) deploys the multi-stage [`Dockerfile`](../Dockerfile) on render's free plan using `GEMINI_API_KEY` (google ai studio free tier) and `GOOGLE_GENAI_USE_VERTEXAI=False`.
- **cloud run always-free tier**: [`scripts/deploy-cloudrun-free.sh`](../scripts/deploy-cloudrun-free.sh) deploys to `us-central1` with `--min-instances=0 --max-instances=1 --memory=512Mi --cpu=1 --cpu-throttling` and `GOOGLE_GENAI_USE_VERTEXAI=False` so zero vertex ai credits are consumed.
