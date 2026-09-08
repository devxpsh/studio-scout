"""FastAPI bridge for screenplay uploads, progress events, and shoot plans."""

from __future__ import annotations

import json
import asyncio
import re
import shutil
import subprocess
import sys
import uuid
from asyncio import Lock
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

# AI dependencies are imported lazily so health and read-only endpoints remain available.

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENT_DIR = REPO_ROOT / "agent"
RECOMMENDATIONS_PATH = AGENT_DIR / "data" / "recommendations.json"
SCREENPLAY_PDF_PATH = AGENT_DIR / "data" / "screenplay.pdf"
SCREENPLAY_JSON_PATH = AGENT_DIR / "data" / "screenplay.json"
AGENT_REPORT_PATH = AGENT_DIR / "data" / "agent_report.json"
FRONTEND_DIST = REPO_ROOT / "frontend" / "dist"
RUN_LOCK = Lock()
EXTRACTION_LOCK = Lock()

sys.path.insert(0, str(AGENT_DIR))

app = FastAPI(title="Studio Scout API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server default
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    """Expose the interpreter used by the running API for local diagnosis."""
    return {
        "status": "ok",
        "python": sys.executable,
        "uv": shutil.which("uv") or "not found",
        "agent_dir": str(AGENT_DIR),
    }


@app.get("/api/recommendations")
def get_recommendations() -> JSONResponse:
    """Returns data/recommendations.json verbatim. Read-only — never
    re-invokes app/location/pipeline.py. 404s clearly if it hasn't been
    generated yet, rather than returning an empty/misleading shape."""
    if not RECOMMENDATIONS_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"{RECOMMENDATIONS_PATH} does not exist yet. Run: "
                "uv run python -m app.location.pipeline data/screenplay.json"
            ),
        )
    with open(RECOMMENDATIONS_PATH) as f:
        return JSONResponse(content=json.load(f))


AGENT_NAME_MAP = {
    "studio_scout_orchestrator": "orchestrator",
    "script_breakdown_agent": "script_breakdown",
    "location_grounding_agent": "location_grounding",
    "logistics_risk_agent": "logistics_risk",
}


def _region_from_prompt(prompt: str) -> str | None:
    """Extract the final 'in/around/near <region>' phrase from the request."""
    matches = re.findall(
        r"\b(?:in|around|near|within)\s+([^.!?\n]+)", prompt, flags=re.IGNORECASE
    )
    if not matches:
        return None
    region = matches[-1].strip(" ,")
    if region.lower() in {"the pdf", "the screenplay", "this screenplay"}:
        return None
    return region


def _trace_event(agent: str, status: str, message: str) -> dict:
    """Matches the frontend's TraceEvent shape exactly (src/lib/types.ts)."""
    return {
        "id": str(uuid.uuid4()),
        "agent": agent,
        "status": status,
        "message": message,
        "timestamp": "",  # frontend doesn't currently render this; fill in if it starts to
    }


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


def _agent_report_from_text(text: str) -> dict | None:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    required = {"screenplay_title", "region_used", "overall_summary", "scenes"}
    return parsed if required.issubset(parsed) else None


async def _run_and_stream(
    pdf_bytes: bytes, filename: str, prompt: str, region: str | None
):
    async with RUN_LOCK:
        async for event in _run_and_stream_locked(pdf_bytes, filename, prompt, region):
            yield event


async def _run_and_stream_locked(
    pdf_bytes: bytes, filename: str, prompt: str, region: str | None
):
    """Runs the Phase 3 orchestrator on an uploaded PDF, yielding SSE lines
    as agent events arrive. Verified against google-adk==2.7.1's real
    Runner.run_async / Event / Content shapes — NOT verified against your
    actual orchestrator, since app/agent.py wasn't available while writing
    this."""

    region = region or _region_from_prompt(prompt)
    if not region:
        yield _sse({
            "region_required": True,
            "question": "Which country or region should location research focus on?",
        })
        yield _sse({"done": True})
        return

    async with EXTRACTION_LOCK:
        SCREENPLAY_PDF_PATH.parent.mkdir(parents=True, exist_ok=True)
        SCREENPLAY_PDF_PATH.write_bytes(pdf_bytes)
        RECOMMENDATIONS_PATH.unlink(missing_ok=True)
        AGENT_REPORT_PATH.unlink(missing_ok=True)
        yield _sse(_trace_event("orchestrator", "running", "Extracting screenplay scenes..."))
        try:
            extraction = await asyncio.to_thread(
                subprocess.run,
                [
                    sys.executable, "-m",
                    "app.screenplay.build_fixture", "data/screenplay.pdf", "data/screenplay.json",
                ],
                cwd=AGENT_DIR,
                capture_output=True,
                text=True,
                timeout=900,
            )
        except Exception as error:
            yield _sse(_trace_event("orchestrator", "done", f"Screenplay extraction failed: {error}"))
            yield _sse({"done": True, "error": f"Could not extract scenes: {error}"})
            return
        if extraction.returncode != 0 or not SCREENPLAY_JSON_PATH.exists():
            detail = (extraction.stderr or extraction.stdout).strip()[-1000:]
            yield _sse(_trace_event("orchestrator", "done", f"Screenplay extraction failed: {detail}"))
            if "429" in detail or "RESOURCE_EXHAUSTED" in detail:
                error = "Vertex AI quota is temporarily exhausted. Wait a minute and retry."
            else:
                error = f"Could not extract scenes from this screenplay. {detail}"
            yield _sse({"done": True, "error": error})
            return

    adk_available = True
    runner = None
    types = None
    try:
        from google.genai import types
    except Exception as error:
        yield _sse(_trace_event("orchestrator", "done", f"GenAI trace unavailable: {error}"))
        yield _sse(_trace_event("orchestrator", "running", "Continuing with report generation."))
        adk_available = False

    try:
        from google.adk.runners import InMemoryRunner
    except Exception as error:
        yield _sse(
            _trace_event(
                "script_breakdown",
                "done",
                f"ADK not available in this environment ({error}). "
                f"Run: uv add google-adk==2.7.1 google-genai==2.19.0",
            )
        )
        yield _sse(_trace_event("orchestrator", "done", "Continuing with report generation."))
        adk_available = False

    if adk_available:
        try:
            from app.agent import root_agent  # type: ignore
            runner = InMemoryRunner(agent=root_agent, app_name="studio_scout")
            user_id = "demo-user"
            session_id = str(uuid.uuid4())
            await runner.session_service.create_session(
                app_name="studio_scout", user_id=user_id, session_id=session_id
            )
        except Exception as error:
            yield _sse(_trace_event("orchestrator", "done", f"ADK unavailable: {error}"))
            yield _sse(_trace_event("orchestrator", "done", "Continuing with report generation."))
            runner = None

    if runner is not None:
        # Mirrors the upload-triggered workflow: the callback sees the PDF
        # part before the orchestrator's normal turn begins.
        message = types.Content(
            role="user",
            parts=[
                types.Part(
                    inline_data=types.Blob(
                        data=pdf_bytes,
                        mime_type="application/pdf",
                        display_name=filename,
                    )
                ),
                types.Part(
                    text=(
                        prompt.strip()
                        or "Find shooting locations for this screenplay."
                    )
                    + f"\nResearch region: {region}",
                ),
            ],
        )
        yield _sse(_trace_event("script_breakdown", "running", "Ingesting uploaded screenplay..."))
        try:
            async for event in runner.run_async(
                user_id=user_id, session_id=session_id, new_message=message
            ):
                agent_key = AGENT_NAME_MAP.get(event.author, "unknown")
                if agent_key == "unknown":
                    continue

                if not event.content or not event.content.parts:
                    continue

                for part in event.content.parts:
                    if part.function_call:
                        yield _sse(
                            _trace_event(
                                agent_key, "running", f"Calling {part.function_call.name}..."
                            )
                        )
                    elif part.function_response:
                        yield _sse(
                            _trace_event(
                                agent_key, "done", f"{part.function_response.name} returned"
                            )
                        )
                    elif part.text:
                        report = _agent_report_from_text(part.text)
                        if report is not None:
                            AGENT_REPORT_PATH.write_text(
                                json.dumps(report, indent=2), encoding="utf-8"
                            )
                            yield _sse({"agent_report": report})
                        yield _sse(_trace_event(agent_key, "done", part.text[:200]))

        except Exception as e:  # noqa: BLE001 — surface the failure and continue to Phase 4
            yield _sse(
                _trace_event(
                    "orchestrator", "done", f"Agent trace ended; continuing report generation: {e}"
                )
            )

    yield _sse(_trace_event("orchestrator", "running", "Generating the scored shoot plan..."))
    pipeline = [
        sys.executable, "-m",
        "app.location.pipeline", "data/screenplay.json", region,
    ]
    if AGENT_REPORT_PATH.exists():
        pipeline.extend(["--agent-report", "data/agent_report.json"])
    try:
        completed = await asyncio.to_thread(
            subprocess.run,
            pipeline,
            cwd=AGENT_DIR,
            capture_output=True,
            text=True,
            timeout=900,
        )
    except Exception as error:
        yield _sse(_trace_event("orchestrator", "done", f"Pipeline failed: {error}"))
        yield _sse({"done": True, "error": "Recommendation generation failed."})
        return
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()[-500:]
        yield _sse(_trace_event("orchestrator", "done", f"Pipeline failed: {detail}"))
        yield _sse({"done": True, "error": "Recommendation generation failed."})
        return

    yield _sse(_trace_event("orchestrator", "done", "Shoot plan is ready."))
    yield _sse({"done": True})


@app.post("/api/upload")
async def upload_screenplay(
    file: UploadFile,
    prompt: str = Form(default=""),
    region: str | None = Form(default=None),
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported.")
    pdf_bytes = await file.read()
    return StreamingResponse(
        _run_and_stream(
            pdf_bytes, file.filename or "screenplay.pdf", prompt, region
        ),
        media_type="text/event-stream",
    )


@app.get("/api/upload")
def upload_help() -> dict[str, str]:
    return {"message": "Use POST /api/upload with a PDF multipart field named 'file'."}


# Mount this last so API routes take precedence over the React single-page app.
app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
