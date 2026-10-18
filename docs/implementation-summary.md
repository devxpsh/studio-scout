# studio scout implementation summary

## product outcome

studio scout converts a screenplay pdf into a production-oriented location research dossier: ranked real-world candidates, verifiable evidence citations, 6-axis feasibility scores, google maps deep links, and a cross-scene conflict register.

## workflow

```text
pdf upload -> sha-256 cache check / gemini extraction -> structured scene requirements
-> adk orchestration (script breakdown, parallel location grounding, logistics/risk)
-> smart candidate deduplication -> parallel 6-axis scoring & conflict detection
-> inline sse shoot_plan delivery -> interactive scouting dossier (csv/json export)
```

fastapi streams server-sent events for extraction, agent tool invocations, per-scene research/scoring progress, and final `shoot_plan` delivery, making the workflow transparent in real time.

## agent & pipeline architecture

the root `studio_scout_orchestrator` uses google adk `AgentTool` to coordinate specialized units:

| unit | responsibility |
| --- | --- |
| `ScriptBreakdownAgent` | loads structured scene requirements from the per-run `screenplay.json` bound via `ContextVar` (`CURRENT_SCREENPLAY_JSON_PATH`) |
| `LocationGrounder` | researches verifiable real-world filming venues with the official `parallel-web` sdk |
| `LogisticsRiskAssessor` | identifies permit lead times, curfews, staging constraints, and operational risks per scene |
| `run_pipeline` (phase 4) | grounds all scenes concurrently via `parallel-web`, batches candidate extraction and 6-axis rubric scoring across scenes (`4` llm calls total per 5-scene run), and synthesizes cross-scene conflicts |
| `genai_client` (`app/genai_client.py`) | unified client factory for `google-genai` and `google-adk` (`GEMINI_API_KEY`) with automatic multi-model flash fallback, 60s cooldown caching, and optional vertex ai support |

### performance & concurrency optimizations

1. **sha-256 screenplay extraction cache** (`agent/data/cache/<sha256>.json`): re-running the same screenplay pdf with different target regions or instructions reuses the cached `ScreenPlay` breakdown immediately.
2. **batched multi-scene extraction & scoring**: `research_screenplay` and `score_screenplay` execute `parallel-web` searches concurrently across scenes and batch structured candidate extraction and 6-axis scoring into single gemini calls (`~36s–3m` per 5-scene run).
3. **per-run workspace isolation** (`agent/data/runs/<run_id>/`): eliminates global file lock contention so concurrent requests do not overwrite shared state.
4. **sse keepalive streaming**: `POST /api/upload` emits `: keepalive` comments every 4 seconds alongside `X-Accel-Buffering: no` so reverse proxies never drop long-running scouting streams.

## frontend & seo

- **5-section editorial intake desk** (`Upload.tsx`): drag-and-drop pdf terminal with 5-scene / ~3-minute run guidance, one-click regional and director-note presets, sample contact-sheet preview, 4-unit pipeline architecture overview, 6-axis scoring matrix, and operational faq.
- **interactive scouting dossier** (`Dashboard.tsx`, `ContactSheet.tsx`, `CandidateCard.tsx`): 4-column telemetry strip, instant scene search and status filtering (`All`, `Ready`, `Flagged`, `Manual Sourcing`), prev/next scene navigation, rank badges, evidence quote snippets, google maps deep links, and one-click csv/json exports.
- **seo & brand assets**: custom 35mm viewfinder `favicon.svg`, `og-cover.svg` social preview card, open graph / twitter card metadata, `JSON-LD` (`WebApplication`) structured data, `site.webmanifest`, `robots.txt`, and `sitemap.xml`.

## deployment

studio scout is packaged as a single multi-stage [`Dockerfile`](../Dockerfile) (node 22 frontend build + python 3.13 / `uv` runtime) and deployed on render via [`render.yaml`](../render.yaml) at https://studio-scout-j78x.onrender.com/.

