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
| `run_pipeline` (phase 4) | merges grounded candidates, skips redundant `ToolParallelAiSearch` calls when a scene already has $\ge 2$ grounded candidates, scores candidates concurrently across 6 weighted dimensions, and synthesizes cross-scene conflicts |

### performance & concurrency optimizations

1. **sha-256 screenplay extraction cache** (`agent/data/cache/<sha256>.json`): re-running the same screenplay pdf with different target regions or instructions reuses the cached `ScreenPlay` breakdown immediately.
2. **token-efficient adk orchestration**: raw pdf bytes are not re-sent inline to the orchestrator llm since the structured breakdown is already extracted and bound via `CURRENT_SCREENPLAY_JSON_PATH`.
3. **per-run workspace isolation** (`agent/data/runs/<run_id>/`): eliminates global file lock contention so concurrent requests do not overwrite shared state.
4. **parallel scene research & scoring**: `research_screenplay` and `score_screenplay` execute scene evaluations concurrently using `ThreadPoolExecutor(max_workers=3)`.

## frontend & seo

- **5-section editorial intake desk** (`Upload.tsx`): drag-and-drop pdf terminal, one-click regional and director-note presets, sample contact-sheet preview, 4-unit pipeline architecture overview, 6-axis scoring matrix, and operational faq.
- **interactive scouting dossier** (`Dashboard.tsx`, `ContactSheet.tsx`, `CandidateCard.tsx`): 4-column telemetry strip, instant scene search and status filtering (`All`, `Ready`, `Flagged`, `Manual Sourcing`), prev/next scene navigation, rank badges, evidence quote snippets, google maps deep links, and one-click csv/json exports.
- **seo & brand assets**: custom 35mm viewfinder `favicon.svg`, `og-cover.svg` social preview card, open graph / twitter card metadata, `JSON-LD` (`WebApplication`) structured data, `site.webmanifest`, `robots.txt`, and `sitemap.xml`.

## deployment

the web application runs on google cloud run in `asia-south1` (`https://studio-scout-922011529524.asia-south1.run.app`). cloud build compiles the multi-stage `dockerfile` into artifact registry, serving both fastapi and the static react bundle from a single container.
