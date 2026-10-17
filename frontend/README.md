# studio scout frontend

react 19 + typescript + vite + tailwindcss v4 frontend for the studio scout location intelligence desk.

## design & aesthetic

modeled after a 35mm contact sheet and physical production call sheet:
- **palette**: near-black darkroom base (`#141311`), bone paper surfaces (`#ede6d6`), film-strip amber accents (`#e8a33d`), and grease-pencil conflict flags (`#c1443b`).
- **typography**: `Fraunces` (display headlines), `Inter` (body copy), and `IBM Plex Mono` (call-sheet telemetry and scores).

## screens & components

- **`Upload.tsx` (01 / intake desk & editorial landing page)**:
  - drag-and-drop screenplay pdf intake terminal with regional quick-select chips and director/location-manager constraint presets.
  - one-click **sample dossier** preview mode (`sampleShootPlan`).
  - live contact sheet preview strip, 4-unit multi-agent architecture breakdown, 6-axis production scoring rubric, and operational faq.
- **`Processing.tsx` & `AgentTrace.tsx` (02 / live dispatch)**:
  - real-time server-sent events (sse) call-sheet trace across `Orchestrator`, `ScriptBreakdownAgent`, `LocationGrounder`, and `LogisticsRiskAssessor`, with retry/back recovery controls.
- **`Dashboard.tsx`, `ContactSheet.tsx`, `CandidateCard.tsx`, `ConflictsPanel.tsx`, `ScoreBars.tsx` (03 / scouting dossier)**:
  - 4-column production telemetry bar (`Total Scenes`, `Unique Sets`, `Avg Top Composite`, `Risk Register Flags`).
  - instant scene search and filter pills (`All`, `Ready`, `Flagged`, `Manual Sourcing`) plus prev/next scene navigation.
  - candidate cards with rank badges (`#1 Primary Pick`, `#2 Backup Option`), 6-axis score bars, cited evidence snippets, and google maps search deep links.
  - one-click **export csv** and **export json** actions.

## seo & public assets

- `public/favicon.svg` — custom 35mm film-frame & viewfinder icon.
- `public/og-cover.svg` — 1200×630 open graph social preview card.
- `public/site.webmanifest`, `public/robots.txt`, `public/sitemap.xml`, and `JSON-LD` (`WebApplication`) structured data in `index.html`.

## commands

```bash
npm ci
npm run dev      # local development server
npm run build    # type-check (tsc -b) and build production bundle to dist/
```
