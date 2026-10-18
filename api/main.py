"""FastAPI bridge for screenplay uploads, progress events, and shoot plans."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import uuid
from asyncio import Lock

from fastapi import FastAPI, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

# AI dependencies are imported lazily so health and read-only endpoints remain available.

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENT_DIR = REPO_ROOT / "agent"
DATA_DIR = AGENT_DIR / "data"
RUNS_DIR = DATA_DIR / "runs"
CACHE_DIR = DATA_DIR / "cache"
RECOMMENDATIONS_PATH = DATA_DIR / "recommendations.json"
SCREENPLAY_PDF_PATH = DATA_DIR / "screenplay.pdf"
SCREENPLAY_JSON_PATH = DATA_DIR / "screenplay.json"
AGENT_REPORT_PATH = DATA_DIR / "agent_report.json"
FRONTEND_DIST = REPO_ROOT / "frontend" / "dist"
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
def get_recommendations(run_id: str | None = Query(default=None)) -> JSONResponse:
    """Returns recommendations.json (for a specific run_id if provided, or latest)."""
    target_path = (
        RUNS_DIR / run_id / "recommendations.json"
        if run_id
        else RECOMMENDATIONS_PATH
    )
    if not target_path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"{target_path} does not exist yet. Run: "
                "uv run python -m app.location.pipeline data/screenplay.json"
            ),
        )
    with open(target_path, encoding="utf-8") as f:
        return JSONResponse(content=json.load(f))


AGENT_NAME_MAP = {
    "studio_scout_orchestrator": "orchestrator",
    "script_breakdown_agent": "script_breakdown",
    "location_grounding_agent": "location_grounding",
    "logistics_risk_agent": "logistics_risk",
}

_GENERIC_PROMPT_WORDS = {
    "the pdf",
    "the screenplay",
    "this screenplay",
    "this script",
    "the script",
    "screenplay",
    "script",
}


def _region_from_prompt(prompt: str) -> str | None:
    """Extract target region from a preposition phrase or a direct location string."""
    cleaned = prompt.strip()
    if not cleaned:
        return None

    matches = re.findall(
        r"\b(?:in|around|near|within|across|for)\s+([^.!?\n]+)",
        cleaned,
        flags=re.IGNORECASE,
    )
    if matches:
        candidate = matches[-1].strip(" ,.")
        if candidate.lower() not in _GENERIC_PROMPT_WORDS:
            return candidate

    # If the user typed a short direct location name (e.g. "New Jersey" or "Mumbai, India")
    words = cleaned.split()
    action_verbs = {"find", "scout", "search", "look", "locate", "recommend", "analyze"}
    if 1 <= len(words) <= 5 and not ( {w.lower().strip(".,:") for w in words} & action_verbs ):
        if cleaned.lower() not in _GENERIC_PROMPT_WORDS:
            return cleaned.strip(" ,.")

    return None


def _trace_event(agent: str, status: str, message: str) -> dict:
    """Matches the frontend's TraceEvent shape exactly (src/lib/types.ts)."""
    return {
        "id": str(uuid.uuid4()),
        "agent": agent,
        "status": status,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
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
    """Runs screenplay extraction, ADK multi-agent research, and deterministic
    scoring in an isolated per-request workspace while streaming SSE events."""
    run_id = str(uuid.uuid4())
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    run_pdf_path = run_dir / "screenplay.pdf"
    run_screenplay_json = run_dir / "screenplay.json"
    run_agent_report_json = run_dir / "agent_report.json"
    run_recommendations_json = run_dir / "recommendations.json"

    region = (region or "").strip() or _region_from_prompt(prompt)
    if not region:
        yield _sse({
            "region_required": True,
            "question": "Which country, state, or city should location research focus on?",
        })
        yield _sse({"done": True})
        return

    pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()[:16]
    cached_screenplay_json = CACHE_DIR / f"{pdf_hash}.json"

    from app.genai_client import configure_genai_env, is_vertex_ai_enabled
    from app.screenplay.build_fixture import build_fixture
    from app.screenplay.schema import ScreenPlay
    import os

    configure_genai_env()
    run_pdf_path.write_bytes(pdf_bytes)

    if cached_screenplay_json.exists():
        yield _sse(
            _trace_event(
                "orchestrator",
                "done",
                f"Loaded cached screenplay breakdown for {filename}.",
            )
        )
        raw_json = cached_screenplay_json.read_text(encoding="utf-8")
        run_screenplay_json.write_text(raw_json, encoding="utf-8")
        SCREENPLAY_JSON_PATH.write_text(raw_json, encoding="utf-8")
        screenplay = ScreenPlay.model_validate_json(raw_json)
    else:
        yield _sse(
            _trace_event("orchestrator", "running", "Extracting screenplay scenes...")
        )
        try:
            async with EXTRACTION_LOCK:
                SCREENPLAY_PDF_PATH.parent.mkdir(parents=True, exist_ok=True)
                SCREENPLAY_PDF_PATH.write_bytes(pdf_bytes)
                extract_task = asyncio.create_task(
                    asyncio.to_thread(
                        build_fixture, str(run_pdf_path), str(run_screenplay_json)
                    )
                )
                while not extract_task.done():
                    try:
                        await asyncio.wait_for(
                            asyncio.shield(extract_task), timeout=4.0
                        )
                    except asyncio.TimeoutError:
                        yield ": keepalive\n\n"
                screenplay = await extract_task
                raw_json = run_screenplay_json.read_text(encoding="utf-8")
                cached_screenplay_json.write_text(raw_json, encoding="utf-8")
                SCREENPLAY_JSON_PATH.write_text(raw_json, encoding="utf-8")
            yield _sse(
                _trace_event(
                    "orchestrator",
                    "done",
                    f"Extracted {screenplay.scene_count()} scenes from {filename}.",
                )
            )
        except Exception as error:
            detail = str(error)
            yield _sse(
                _trace_event(
                    "orchestrator", "done", f"Screenplay extraction failed: {detail}"
                )
            )
            if "429" in detail or "RESOURCE_EXHAUSTED" in detail:
                err_msg = "Gemini API free-tier rate limit reached (429). Wait a minute and retry."
            else:
                err_msg = f"Could not extract scenes from this screenplay: {detail}"
            yield _sse({"done": True, "error": err_msg})
            return

    # On Google AI Studio Free Tier, skip the 19-turn recursive ADK pre-pass unless
    # FULL_ADK_TRACE=true or Vertex AI is active, and stream multi-agent traces +
    # StudioScoutReport directly from the parallelized pipeline stages.
    use_full_adk_runner = is_vertex_ai_enabled() or os.environ.get(
        "FULL_ADK_TRACE", ""
    ).strip().lower() in ("true", "1", "yes")

    adk_available = use_full_adk_runner
    runner = None
    types = None
    if adk_available:
        try:
            from google.genai import types
        except Exception as error:
            yield _sse(_trace_event("orchestrator", "done", f"GenAI trace unavailable: {error}"))
            yield _sse(_trace_event("orchestrator", "running", "Continuing with report generation."))
            adk_available = False

    if adk_available:
        try:
            from google.adk.runners import InMemoryRunner
        except Exception as error:
            yield _sse(
                _trace_event(
                    "script_breakdown",
                    "done",
                    f"ADK not available in this environment ({error}).",
                )
            )
            yield _sse(_trace_event("orchestrator", "done", "Continuing with report generation."))
            adk_available = False

    if adk_available:
        try:
            from app.agent import root_agent  # type: ignore
            runner = InMemoryRunner(agent=root_agent, app_name="studio_scout")
            user_id = f"user-{run_id[:8]}"
            session_id = str(uuid.uuid4())
            await runner.session_service.create_session(
                app_name="studio_scout", user_id=user_id, session_id=session_id
            )
        except Exception as error:
            yield _sse(_trace_event("orchestrator", "done", f"ADK unavailable: {error}"))
            yield _sse(_trace_event("orchestrator", "done", "Continuing with report generation."))
            runner = None

    parsed_agent_report = None
    if runner is not None:
        from app.agents.script_breakdown_agent import CURRENT_SCREENPLAY_JSON_PATH

        # Do not send raw pdf_bytes inline to the LLM here: screenplay.json is already
        # extracted and bound via CURRENT_SCREENPLAY_JSON_PATH, saving input tokens.
        message = types.Content(
            role="user",
            parts=[
                types.Part(
                    text=(
                        prompt.strip()
                        or "Find shooting locations for this screenplay."
                    )
                    + f"\nResearch region: {region}",
                ),
            ],
        )
        yield _sse(
            _trace_event(
                "script_breakdown",
                "running",
                "Loading structured screenplay breakdown...",
            )
        )
        token = CURRENT_SCREENPLAY_JSON_PATH.set(run_screenplay_json)
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
                                agent_key,
                                "running",
                                f"Calling {part.function_call.name}...",
                            )
                        )
                    elif part.function_response:
                        yield _sse(
                            _trace_event(
                                agent_key,
                                "done",
                                f"{part.function_response.name} returned",
                            )
                        )
                    elif part.text:
                        report_dict = _agent_report_from_text(part.text)
                        if report_dict is not None:
                            report_json = json.dumps(report_dict, indent=2)
                            run_agent_report_json.write_text(
                                report_json, encoding="utf-8"
                            )
                            AGENT_REPORT_PATH.write_text(
                                report_json, encoding="utf-8"
                            )
                            from app.agents.report_schema import StudioScoutReport

                            parsed_agent_report = StudioScoutReport.model_validate(
                                report_dict
                            )
                            yield _sse({"agent_report": report_dict})
                        yield _sse(_trace_event(agent_key, "done", part.text[:200]))

        except Exception as e:  # noqa: BLE001 — surface the failure and continue to Phase 4
            yield _sse(
                _trace_event(
                    "orchestrator",
                    "done",
                    f"Agent trace ended; continuing report generation: {e}",
                )
            )
        finally:
            CURRENT_SCREENPLAY_JSON_PATH.reset(token)

    yield _sse(
        _trace_event("orchestrator", "running", "Generating the scored shoot plan...")
    )
    from app.agents.report_schema import StudioScoutReport
    from app.location.pipeline import run_pipeline

    trace_queue: asyncio.Queue[tuple[str, str, str] | None] = asyncio.Queue()
    loop = asyncio.get_running_loop()
    out_report_holder: list[StudioScoutReport] = []

    def _on_trace(agent_name: str, status: str, msg: str) -> None:
        loop.call_soon_threadsafe(
            trace_queue.put_nowait, (agent_name, status, msg)
        )

    async def _execute_pipeline():
        try:
            return await asyncio.to_thread(
                run_pipeline,
                screenplay,
                region,
                str(run_agent_report_json) if run_agent_report_json.exists() else None,
                parsed_agent_report,
                None,
                _on_trace,
                out_report_holder,
            )
        finally:
            loop.call_soon_threadsafe(trace_queue.put_nowait, None)

    pipeline_task = asyncio.create_task(_execute_pipeline())
    while True:
        try:
            item = await asyncio.wait_for(trace_queue.get(), timeout=4.0)
        except asyncio.TimeoutError:
            yield ": keepalive\n\n"
            continue
        if item is None:
            break
        agent_name, status, step_msg = item
        yield _sse(_trace_event(agent_name, status, step_msg))

    try:
        shoot_plan = await pipeline_task
    except Exception as error:
        detail = str(error)
        yield _sse(_trace_event("orchestrator", "done", f"Pipeline failed: {detail}"))
        yield _sse({"done": True, "error": f"Recommendation generation failed: {detail}"})
        return

    if parsed_agent_report is None and out_report_holder:
        synthesized_report = out_report_holder[0]
        report_json = synthesized_report.model_dump_json(indent=2)
        run_agent_report_json.write_text(report_json, encoding="utf-8")
        AGENT_REPORT_PATH.write_text(report_json, encoding="utf-8")
        yield _sse({"agent_report": synthesized_report.model_dump()})

    plan_json = shoot_plan.model_dump_json(indent=2)
    run_recommendations_json.write_text(plan_json, encoding="utf-8")
    RECOMMENDATIONS_PATH.write_text(plan_json, encoding="utf-8")

    yield _sse(_trace_event("orchestrator", "done", "Shoot plan is ready."))
    yield _sse({"shoot_plan": shoot_plan.model_dump(), "run_id": run_id})
    yield _sse({"done": True, "run_id": run_id})


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
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/upload")
def upload_help() -> dict[str, str]:
    return {"message": "Use POST /api/upload with a PDF multipart field named 'file'."}


# Mount this last so API routes take precedence over the React single-page app.
app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
