# studio scout web api

fastapi provides the browser-facing api, server-sent-event progress stream, and production static-file hosting for the react dashboard.

| endpoint | purpose |
| --- | --- |
| `get /api/health` | health and runtime diagnostics |
| `post /api/upload` | multipart pdf upload with `file`, optional `prompt`, and optional `region`; returns sse events |
| `get /api/recommendations` | returns the latest generated shoot plan |
| `get /api/upload` | direct-browser usage hint |

## local run

```bash
uv sync
uv run uvicorn main:app --reload --port 8000
```

vite uses port 8000 during development. in production, fastapi mounts built react assets after its api routes, so the browser uses same-origin requests.

## cloud run

the deployed service is https://studio-scout-922011529524.asia-south1.run.app. cloud build uses [`cloudbuild.yaml`](../cloudbuild.yaml), which explicitly builds the lowercase [`dockerfile`](../dockerfile). production runs in `asia-south1`, uses vertex ai in `global`, injects `PARALLEL_API_KEY` from secret manager, and allows 900-second requests for the agent workflow.

do not include `.env` files or credentials in the image. cloud run local storage is ephemeral.
