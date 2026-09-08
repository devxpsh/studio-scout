# studio scout implementation summary

## product outcome

studio scout converts a screenplay pdf into a production-oriented location research package: ranked real-world candidates, evidence links, feasibility signals, and conflicts that need human review.

## workflow

```text
pdf upload -> gemini extraction -> structured scene requirements
-> adk orchestration and parallel-grounded research
-> candidate merge -> deterministic scoring and conflict detection
-> shoot plan dashboard
```

fastapi streams server-sent events for extraction, agent activity, scoring, and completion, making the workflow inspectable rather than a black box.

## agent design

the root `studio_scout_orchestrator` uses google adk `agenttool` to call three specialized agents in order:

| agent | responsibility |
| --- | --- |
| script breakdown | converts screenplay content into structured scene requirements |
| location grounding | researches real locations with parallel evidence |
| logistics and risk | identifies operational constraints and risks for each scene |

the orchestrator requires a region, infers one only from clear cues, and otherwise asks the user. bounded retries address transient vertex ai quota responses.

## grounded research and ranking

parallel is active in two paths: the grounding agent calls the official `parallel-web` sdk, while the deterministic research stage configures gemini's `toolparallelaisearch`. the final pipeline merges non-duplicate agent and research candidates, calculates scoring dimensions, detects continuity/budget/permit/low-confidence conflicts, and returns a `shootplan`. the browser does not calculate composite scores.

## deployment

the web application runs on google cloud run in `asia-south1`. cloud build builds the root `dockerfile`; the final image contains fastapi, python dependencies, and built react assets, but no node runtime or local secret file. a dedicated runtime service account has vertex ai access, and secret manager injects `PARALLEL_API_KEY`. requests may run for 900 seconds to accommodate the research workflow.

## validation

- frontend production build.
- api python syntax validation.
- local container build and in-container health check.
- cloud build publication to artifact registry.
- cloud run deployment plus public `/` and `/api/health` checks.

see the [judge guide](judge-verification-adk-parallel.md) for repeatable source and runtime validation.
