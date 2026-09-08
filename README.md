# Studio Scout

Studio Scout turns a screenplay PDF into a production-oriented location scouting plan. It extracts scenes, identifies the region to research, finds real-world candidate locations, scores them, flags conflicts, and presents the result as a call-sheet-style dashboard.

Built for the Google Cloud Agentic Cinema hackathon and the Parallel track.

## What It Does

- Accepts a screenplay PDF and a natural-language scouting prompt.
- Extracts structured scenes with Gemini.
- Uses Google ADK to coordinate:
  - Script Breakdown Agent
  - Location & Permit Grounding Agent
  - Logistics & Risk Agent
- Uses Parallel Search for current, source-backed location research.
- Hands the ADK report into the deterministic location pipeline.
- Scores candidates across visual fit, feasibility, logistics, cost, permits, and evidence confidence.
- Detects continuity, budget, permit, and low-confidence conflicts.
- Streams processing events to the browser over Server-Sent Events.

## Architecture

```text
PDF + prompt + region
        |
        v
FastAPI upload bridge
        |
        +--> screenplay extraction -> screenplay.json
        |
        +--> Google ADK orchestrator
        |       +--> Script Breakdown Agent
        |       +--> Location Grounding Agent -> Parallel Search
        |       +--> Logistics & Risk Agent
        |       +--> StudioScoutReport -> agent_report.json
        |
        +--> location pipeline --agent-report agent_report.json
                +--> ADK candidates + Parallel candidates
                +--> scoring and conflict detection
                +--> recommendations.json
        |
        v
React dashboard
```

The ADK report is not discarded: it is persisted as `agent/data/agent_report.json`, converted into the pipeline candidate schema, merged with non-duplicate Parallel results, and then scored.

## Repository Layout

```text
agent/       Google ADK agents and location intelligence pipeline
api/         FastAPI bridge for uploads, SSE, and recommendations
frontend/    React + Vite dashboard
docs/        Implementation and judge-verification guides
LICENSE      MIT license for project code
```

## Requirements

- Python 3.13+
- `uv`
- Node.js and npm
- A Google Cloud project with Vertex AI access and billing enabled
- Application Default Credentials for local Google Cloud calls
- A Parallel API key

## Configuration

Copy the example file and fill in your own values:

```bash
cp agent/.env.example agent/.env
```

Required values:

```dotenv
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=global
GOOGLE_GENAI_USE_VERTEXAI=True
PARALLEL_API_KEY=your-parallel-api-key
```

Authenticate locally:

```bash
gcloud auth application-default login
```

Do not commit `.env`, API keys, service-account keys, uploaded PDFs, virtual environments, or generated runtime artifacts.

## Run Locally

Install the agent dependencies:

```bash
cd agent
uv sync
```

Install the API dependencies:

```bash
cd ../api
uv sync
```

Install the frontend dependencies:

```bash
cd ../frontend
npm install
```

Start the API:

```bash
cd ../api
uv run uvicorn main:app --reload --port 8000
```

Start the frontend in a second terminal:

```bash
cd frontend
npm run dev
```

Open the Vite URL, select a PDF, and enter a prompt such as:

```text
Find all screenplay locations in New Jersey
```

The API health check is available at `http://localhost:8000/api/health`.

## Run The Agent Directly

Run the ADK trace demonstration:

```bash
cd agent
uv run python -m app.demo_trace
```

This prints ADK tool calls, nested `parallel_search` calls, tool responses, and the structured agent report.

Run the deterministic pipeline with an existing structured screenplay:

```bash
cd agent
uv run python -m app.location.pipeline \
  data/screenplay.json \
  "New Jersey" \
  --agent-report data/agent_report.json
```

The pipeline writes `data/recommendations.json`.

## Deploy The ADK Agent

Studio Scout includes a source-based Agent Platform deployment helper at `agent/deploy_agent.py`. It follows Google’s Agent Platform Runtime deployment model: an entrypoint module/object, a requirements file, environment variables, and the `google-adk` framework declaration.

First install the deployment SDK in your local agent environment:

```bash
cd agent
uv add "google-cloud-aiplatform[agent_engines,adk]>=1.112.0"
```

Set the deployment variables:

```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"
export GOOGLE_CLOUD_STAGING_BUCKET="gs://your-agent-staging-bucket"
export PARALLEL_API_KEY="your-parallel-api-key"
```

Enable the required services and ensure the deploying identity has the Agent Platform User role (`roles/aiplatform.user`):

```bash
gcloud services enable aiplatform.googleapis.com \
  storage.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  cloudtrace.googleapis.com \
  telemetry.googleapis.com \
  cloudresourcemanager.googleapis.com
```

Deploy:

```bash
cd agent
uv run python deploy_agent.py
```

The deployment helper wraps `app.agent.root_agent` in `vertexai.agent_engines.AdkApp`, stages the local `app/` package and `requirements.txt`, and creates a managed Agent Platform Runtime resource.

The script prints the deployed Agent Platform resource name. The deployment can take several minutes. After deployment, use the returned resource with the Agent Platform SDK and `async_stream_query`.

The deployment requires a cloud project, billing, enabled APIs, IAM permissions, and valid credentials. It cannot be completed from source code alone.

## Verify Google ADK And Parallel

Use the dedicated judge guide:

[docs/judge-verification-adk-parallel.md](docs/judge-verification-adk-parallel.md)

It includes source inspection steps, dependency checks, direct Parallel verification, live ADK tracing, nested tool evidence, and dashboard proof.

## Documentation

- [Implementation summary](docs/implementation-summary.md)
- [Judge verification guide](docs/judge-verification-adk-parallel.md)
- [Agent README](agent/README.md)
- [API README](api/README.md)

## Validation

Frontend:

```bash
cd frontend
npm run build
```

Backend syntax:

```bash
cd api
uv run python -m py_compile main.py
cd ../agent
uv run python -m compileall -q app
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).

Google Cloud, Google ADK, Gemini, Vertex AI, and Parallel are trademarks or services of their respective owners. This project is an independent hackathon submission.
