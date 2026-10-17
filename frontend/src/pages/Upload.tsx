import { useState } from "react";

const REGION_SUGGESTIONS = [
  "New Jersey",
  "Bay Area, California",
  "Los Angeles, California",
  "New York City, New York",
  "Atlanta, Georgia",
  "Chicago, Illinois",
  "London, UK",
  "Mumbai, India",
  "Vancouver, Canada",
];

const PROMPT_PRESETS = [
  "Prioritize low-permit-friction locations and easy crew parking",
  "Focus on gritty industrial warehouses with loading dock access",
  "Prefer historic / period-authentic interiors with controlled acoustics",
  "Optimize for tight indie budget and minimal company moves",
];

const PREVIEW_SCENES = [
  {
    number: "01",
    slugline: "INT. SUBSTATION CONTROL ROOM — NIGHT",
    meta: "Industrial · Fluorescent hum · High voltage",
    candidate: " Mare Island Historic Power Plant",
    area: "Vallejo, Bay Area, CA",
    score: "86.5",
    risk: "Permit lead time: 14 days",
    evidence: "Solano County Film Office Directory",
  },
  {
    number: "02",
    slugline: "EXT. EMBARKADERO PIER 14 — DAWN",
    meta: "Waterfront · Heavy fog · Long telephoto lens",
    candidate: "Pier 14 Public Promenade & Breakwater",
    area: "San Francisco Embarcadero, CA",
    score: "91.2",
    risk: "Port of SF commercial permit + pedestrian hold",
    evidence: "Film SF Port Property Guidelines",
  },
  {
    number: "03",
    slugline: "INT. LATE-NIGHT DINER BOOTH — NIGHT",
    meta: "Neon spill · Vinyl booths · Rain on plate glass",
    candidate: "Orphan Andy's 24-Hour Diner",
    area: "Castro District, San Francisco, CA",
    score: "84.0",
    risk: "Night buyout required after 22:00",
    evidence: "SF Location Scout Registry",
  },
];

const PIPELINE_UNITS = [
  {
    unit: "UNIT 01",
    name: "ScriptBreakdownAgent",
    role: "PDF Scene Extraction & Beat Tagging",
    tech: "Gemini 2.5 Pro · Structured JSON Schema",
    description:
      "Reads uploaded screenplay PDFs and extracts every distinct scene slugline, INT/EXT setting, time-of-day lighting cue, visual atmosphere, budget tier, and physical staging constraint.",
  },
  {
    unit: "UNIT 02",
    name: "LocationGrounder",
    role: "Live Regional Web Grounding",
    tech: "Google ADK ParallelAgent · ToolParallelAiSearch",
    description:
      "Executes live regional web searches across film commission registries, historic preservation listings, and architectural directories to surface verifiable venues with cited URLs.",
  },
  {
    unit: "UNIT 03",
    name: "LogisticsRiskAssessor",
    role: "Permit, Curfew & Access Auditing",
    tech: "Google ADK ParallelAgent · Municipal Rules",
    description:
      "Runs concurrently with location grounding to evaluate municipal film permit lead times, noise ordinances, basecamp parking, weather exposure, and company move distances.",
  },
  {
    unit: "UNIT 04",
    name: "6-Axis Scorer & Conflict Solver",
    role: "Deterministic Ranking & Call-Sheet Synthesis",
    tech: "Parallel ThreadPool · Weighted Rubric",
    description:
      "Scores every candidate across 6 weighted production dimensions, selects the primary and backup venue per scene, and compiles a cross-scene Risk Register.",
  },
];

const RUBRIC_AXES = [
  {
    label: "Visual Match",
    weight: "30%",
    bar: 92,
    detail:
      "Architectural period accuracy, texture, natural light orientation, and camera sightlines matching the script's visual beats.",
  },
  {
    label: "Production Feasibility",
    weight: "20%",
    bar: 85,
    detail:
      "Power availability, sound isolation, ceiling grid height, rain/night control, and ability to accommodate art department dressing.",
  },
  {
    label: "Crew & Truck Logistics",
    weight: "15%",
    bar: 78,
    detail:
      "Basecamp staging, grip/lighting truck load-in, company move proximity to adjacent scenes, and local crew accessibility.",
  },
  {
    label: "Cost & Budget Fit",
    weight: "15%",
    bar: 80,
    detail:
      "Alignment between the scene's estimated budget tier and typical location rental fees, buyouts, or municipal day rates.",
  },
  {
    label: "Permit Ease",
    weight: "10%",
    bar: 74,
    detail:
      "Film office turnaround time, traffic control requirements, neighborhood signature thresholds, and curfew restrictions.",
  },
  {
    label: "Evidence Confidence",
    weight: "10%",
    bar: 88,
    detail:
      "Strength and specificity of grounded web citations, official film commission listings, and verifiable street addresses.",
  },
];

export function Upload({
  onSubmit,
  onOpenSample,
}: {
  onSubmit: (file: File, prompt: string, region: string) => void;
  onOpenSample?: () => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [region, setRegion] = useState("");
  const [prompt, setPrompt] = useState("");
  const [isDragging, setIsDragging] = useState(false);

  return (
    <main className="mx-auto max-w-6xl px-5 sm:px-8">
      {/* HERO & INTAKE TERMINAL */}
      <section
        id="intake"
        className="grid gap-12 py-12 lg:grid-cols-[1fr_1.08fr] lg:items-start lg:py-20"
      >
        <div className="lg:pt-2">
          <div className="inline-flex items-center gap-2 rounded-sm border border-(--color-amber)/40 bg-(--color-amber)/10 px-3 py-1 font-mono text-[10px] uppercase tracking-[0.2em] text-(--color-amber)">
            <span>●</span> 01 / New Production Brief
          </div>

          <h1
            className="balance-text mt-5 font-display leading-[0.98] text-(--color-paper)"
            style={{ fontSize: "clamp(2.5rem, 1.6rem + 3.2vw, 4.25rem)" }}
          >
            Find every real-world location your script demands.
          </h1>

          <p className="pretty-text mt-6 max-w-xl text-base leading-7 text-(--color-meta)">
            Upload a screenplay PDF and target shooting region. Studio Scout
            dispatches a 4-unit multi-agent desk that extracts every scene,
            grounds real venues via live web search, scores candidates across 6
            production axes, and flags permit or scheduling risks before you
            roll.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-3">
            <a
              href="#intake-form"
              className="rounded-sm bg-(--color-amber) px-4 py-2.5 font-mono text-[11px] font-medium uppercase tracking-widest text-(--color-ink) transition-colors hover:bg-(--color-paper)"
            >
              Upload Screenplay ↓
            </a>
            {onOpenSample && (
              <button
                type="button"
                onClick={onOpenSample}
                className="rounded-sm border border-(--color-line) bg-(--color-surface)/80 px-4 py-2.5 font-mono text-[11px] uppercase tracking-widest text-(--color-paper) transition-colors hover:border-(--color-amber) hover:text-(--color-amber)"
              >
                Explore Sample Dossier →
              </button>
            )}
          </div>

          <div className="mt-10 grid grid-cols-2 gap-px border border-(--color-line) bg-(--color-line) sm:grid-cols-4">
            <div className="bg-(--color-surface) p-4">
              <strong className="block font-display text-2xl text-(--color-paper)">
                PDF → JSON
              </strong>
              <span className="mt-1 block font-mono text-[10px] uppercase tracking-widest text-(--color-meta)">
                Scene Breakdown
              </span>
            </div>
            <div className="bg-(--color-surface) p-4">
              <strong className="block font-display text-2xl text-(--color-amber)">
                4 Units
              </strong>
              <span className="mt-1 block font-mono text-[10px] uppercase tracking-widest text-(--color-meta)">
                Parallel ADK Desk
              </span>
            </div>
            <div className="bg-(--color-surface) p-4">
              <strong className="block font-display text-2xl text-(--color-paper)">
                6 Axes
              </strong>
              <span className="mt-1 block font-mono text-[10px] uppercase tracking-widest text-(--color-meta)">
                Weighted Rubric
              </span>
            </div>
            <div className="bg-(--color-surface) p-4">
              <strong className="block font-display text-2xl text-(--color-paper)">
                100% Cited
              </strong>
              <span className="mt-1 block font-mono text-[10px] uppercase tracking-widest text-(--color-meta)">
                Live Web Grounded
              </span>
            </div>
          </div>

          <div className="mt-8 border-l-2 border-(--color-amber)/60 pl-4">
            <p className="font-mono text-[10px] uppercase tracking-widest text-(--color-amber)">
              Zero Hallucinated Venues
            </p>
            <p className="mt-1 max-w-lg text-xs leading-5 text-(--color-meta)">
              Every recommended location includes verifiable evidence URLs, one-click
              Google Maps coordinates, and explicit fallback flags when a scene
              requires manual physical scouting.
            </p>
          </div>
        </div>

        {/* INTAKE FORM TERMINAL */}
        <form
          id="intake-form"
          className="border border-(--color-line) bg-(--color-surface)/90 p-5 shadow-2xl sm:p-7"
          onSubmit={(e) => {
            e.preventDefault();
            if (file) onSubmit(file, prompt, region);
          }}
        >
          <div className="mb-5 flex items-center justify-between border-b border-(--color-line) pb-4">
            <div>
              <p className="font-mono text-[11px] uppercase tracking-widest text-(--color-paper)">
                Scout Intake Terminal
              </p>
              <p className="mt-1 font-mono text-[10px] text-(--color-meta)">
                Attach screenplay PDF &amp; configure regional parameters
              </p>
            </div>
            <span className="rounded-sm border border-(--color-amber)/40 bg-(--color-amber)/10 px-2 py-1 font-mono text-[10px] text-(--color-amber)">
              REEL / 01
            </span>
          </div>

          <label
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setIsDragging(false);
              const dropped = e.dataTransfer.files?.[0];
              if (dropped && dropped.type === "application/pdf") {
                setFile(dropped);
              }
            }}
            className={`group flex min-h-40 cursor-pointer flex-col items-center justify-center border border-dashed px-5 py-6 text-center transition-all ${
              isDragging
                ? "border-(--color-amber) bg-(--color-amber)/10"
                : file
                  ? "border-(--color-amber)/80 bg-(--color-amber)/5"
                  : "border-(--color-meta)/60 hover:border-(--color-amber)"
            }`}
          >
            <span className="mb-3 flex h-11 w-11 items-center justify-center border border-(--color-line) bg-(--color-ink) font-mono text-lg text-(--color-amber) transition-transform group-hover:scale-105">
              {file ? "✓" : "+"}
            </span>
            {file ? (
              <>
                <span className="font-mono text-sm font-medium text-(--color-amber)">
                  {file.name}
                </span>
                <span className="mt-1.5 font-mono text-[10px] uppercase tracking-widest text-(--color-meta)">
                  {(file.size / 1024).toFixed(1)} KB · PDF Ready for Breakdown
                </span>
              </>
            ) : (
              <>
                <span className="font-mono text-sm text-(--color-paper)">
                  Drop a screenplay PDF here, or click to browse
                </span>
                <span className="mt-1.5 font-mono text-[10px] uppercase tracking-widest text-(--color-meta)">
                  Standard Fountain / Final Draft PDF · Multi-scene extraction
                </span>
              </>
            )}
            <input
              type="file"
              name="file"
              accept="application/pdf"
              className="hidden"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </label>

          <div className="mt-5">
            <div className="flex items-center justify-between">
              <label
                htmlFor="region-input"
                className="font-mono text-[10px] uppercase tracking-widest text-(--color-meta)"
              >
                Target Shooting Region
              </label>
              {region && (
                <button
                  type="button"
                  onClick={() => setRegion("")}
                  className="font-mono text-[10px] text-(--color-meta) hover:text-(--color-paper)"
                >
                  Clear
                </button>
              )}
            </div>
            <input
              id="region-input"
              type="text"
              name="region"
              list="region-suggestions"
              value={region}
              onChange={(e) => setRegion(e.target.value)}
              placeholder="e.g. New Jersey, Bay Area, London, or Mumbai"
              className="mt-2 w-full rounded-sm border border-(--color-line) bg-(--color-ink)/70 px-3 py-2.5 font-mono text-sm text-(--color-paper) outline-none placeholder:text-(--color-meta)/70 focus:border-(--color-amber)"
            />
            <datalist id="region-suggestions">
              {REGION_SUGGESTIONS.map((item) => (
                <option key={item} value={item} />
              ))}
            </datalist>

            <div className="mt-2.5 flex flex-wrap gap-1.5">
              {REGION_SUGGESTIONS.slice(0, 6).map((presetRegion) => {
                const active = region === presetRegion;
                return (
                  <button
                    key={presetRegion}
                    type="button"
                    onClick={() => setRegion(presetRegion)}
                    className={`rounded-sm border px-2 py-1 font-mono text-[10px] transition-colors ${
                      active
                        ? "border-(--color-amber) bg-(--color-amber)/15 text-(--color-amber)"
                        : "border-(--color-line) text-(--color-meta) hover:border-(--color-meta) hover:text-(--color-paper)"
                    }`}
                  >
                    {presetRegion.split(",")[0]}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="mt-5">
            <label
              htmlFor="prompt-input"
              className="font-mono text-[10px] uppercase tracking-widest text-(--color-meta)"
            >
              Director / Location Manager Notes (Optional)
            </label>
            <textarea
              id="prompt-input"
              name="prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Example: prioritize gritty industrial warehouses and low-permit-friction exteriors"
              rows={2}
              className="mt-2 w-full rounded-sm border border-(--color-line) bg-(--color-ink)/70 px-3 py-2.5 font-mono text-sm text-(--color-paper) outline-none placeholder:text-(--color-meta)/70 focus:border-(--color-amber)"
            />
            <div className="mt-2 flex flex-wrap gap-1.5">
              {PROMPT_PRESETS.map((preset) => (
                <button
                  key={preset}
                  type="button"
                  onClick={() => setPrompt(preset)}
                  className="rounded-sm border border-(--color-line) bg-(--color-ink)/40 px-2 py-1 text-left font-mono text-[10px] text-(--color-meta) transition-colors hover:border-(--color-amber)/60 hover:text-(--color-paper)"
                >
                  + {preset}
                </button>
              ))}
            </div>
          </div>

          <button
            type="submit"
            disabled={!file}
            className="mt-6 flex w-full items-center justify-between rounded-sm bg-(--color-amber) px-4 py-3.5 font-mono text-[11px] font-medium uppercase tracking-widest text-(--color-ink) transition-colors hover:bg-(--color-paper) disabled:cursor-not-allowed disabled:opacity-40"
          >
            <span>
              {file
                ? `Launch Location Scout (${region || "Auto Region"})`
                : "Select a Screenplay PDF to Begin"}
            </span>
            <span aria-hidden="true">↗</span>
          </button>
        </form>
      </section>

      {/* SECTION 2: CONTACT SHEET PREVIEW */}
      <section
        id="contact-preview"
        className="border-t border-(--color-line) py-16"
      >
        <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="section-kicker">02 / Sample Output Preview</p>
            <h2 className="mt-2 font-display text-3xl text-(--color-paper) sm:text-4xl">
              From raw slugline to grounded contact sheet.
            </h2>
          </div>
          {onOpenSample && (
            <button
              type="button"
              onClick={onOpenSample}
              className="rounded-sm border border-(--color-amber)/60 px-3.5 py-2 font-mono text-[10px] uppercase tracking-widest text-(--color-amber) transition-colors hover:bg-(--color-amber) hover:text-(--color-ink)"
            >
              Open Full Interactive Sample Report →
            </button>
          )}
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          {PREVIEW_SCENES.map((item) => (
            <div
              key={item.number}
              className="flex flex-col justify-between border border-(--color-line) bg-(--color-surface)/75 p-5 transition-colors hover:border-(--color-amber)/50"
            >
              <div>
                <div className="flex items-center justify-between border-b border-(--color-line) pb-3">
                  <span className="font-mono text-[10px] uppercase tracking-widest text-(--color-amber)">
                    SCENE #{item.number}
                  </span>
                  <span className="rounded-full bg-(--color-ink) px-2.5 py-0.5 font-mono text-xs text-(--color-amber)">
                    {item.score} composite
                  </span>
                </div>
                <p className="mt-4 font-mono text-xs font-medium text-(--color-paper)">
                  {item.slugline}
                </p>
                <p className="mt-1 font-mono text-[10px] text-(--color-meta)">
                  {item.meta}
                </p>

                <div className="mt-4 rounded-sm border border-(--color-line) bg-(--color-paper) p-3.5 text-(--color-ink)">
                  <span className="font-mono text-[9px] uppercase tracking-widest text-(--color-flag)">
                    Top Grounded Pick
                  </span>
                  <h3 className="mt-0.5 font-display text-lg leading-snug">
                    {item.candidate}
                  </h3>
                  <p className="mt-0.5 font-mono text-[11px] text-(--color-meta)">
                    {item.area}
                  </p>
                </div>
              </div>

              <div className="mt-4 border-t border-(--color-line) pt-3 font-mono text-[10px] text-(--color-meta)">
                <p className="text-(--color-amber)">⚑ {item.risk}</p>
                <p className="mt-1 truncate">Source: {item.evidence}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* SECTION 3: 4-UNIT MULTI-AGENT PIPELINE */}
      <section id="pipeline" className="border-t border-(--color-line) py-16">
        <div className="max-w-2xl">
          <p className="section-kicker">03 / Multi-Agent Architecture</p>
          <h2 className="mt-2 font-display text-3xl text-(--color-paper) sm:text-4xl">
            Four specialized units working in parallel.
          </h2>
          <p className="mt-3 text-sm leading-6 text-(--color-meta)">
            Built on Google Agent Development Kit (ADK), Gemini 2.5 Pro, and
            Parallel Web Search. Each screenplay run executes in an isolated
            workspace with real-time Server-Sent Events (SSE) telemetry.
          </p>
        </div>

        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          {PIPELINE_UNITS.map((u) => (
            <div
              key={u.unit}
              className="border border-(--color-line) bg-(--color-surface)/60 p-6"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-[10px] uppercase tracking-widest text-(--color-amber)">
                  {u.unit}
                </span>
                <span className="rounded-sm border border-(--color-line) px-2 py-0.5 font-mono text-[10px] text-(--color-meta)">
                  {u.tech}
                </span>
              </div>
              <h3 className="mt-3 font-display text-2xl text-(--color-paper)">
                {u.name}
              </h3>
              <p className="mt-1 font-mono text-xs text-(--color-amber)/90">
                {u.role}
              </p>
              <p className="mt-3 text-sm leading-6 text-(--color-meta)">
                {u.description}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* SECTION 4: 6-AXIS SCORING RUBRIC */}
      <section id="rubric" className="border-t border-(--color-line) py-16">
        <div className="grid gap-10 lg:grid-cols-[0.85fr_1.15fr] lg:items-start">
          <div>
            <p className="section-kicker">04 / Deterministic Evaluation</p>
            <h2 className="mt-2 font-display text-3xl text-(--color-paper) sm:text-4xl">
              6-Axis Production Scoring Matrix
            </h2>
            <p className="mt-4 text-sm leading-6 text-(--color-meta)">
              Rather than returning generic AI prose, Studio Scout evaluates
              every grounded candidate on a 0–100 scale across six production
              dimensions and computes a weighted composite score.
            </p>
            <div className="mt-6 rounded-sm border border-(--color-line) bg-(--color-surface) p-4 font-mono text-xs">
              <p className="text-(--color-amber)">AUTOMATIC CONFLICT TRIGGERS</p>
              <ul className="mt-2.5 space-y-2 text-[11px] text-(--color-meta)">
                <li>
                  <strong className="text-(--color-flag)">BLOCKER:</strong> Zero
                  grounded candidates or composite score &lt; 45
                </li>
                <li>
                  <strong className="text-(--color-amber)">WARNING:</strong>{" "}
                  Permit ease &lt; 40 or cost fit &lt; 45 for scene budget tier
                </li>
                <li>
                  <strong className="text-(--color-paper)">INFO:</strong>{" "}
                  Cross-scene company move &amp; shared location consolidation
                </li>
              </ul>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            {RUBRIC_AXES.map((axis) => (
              <div
                key={axis.label}
                className="border border-(--color-line) bg-(--color-surface)/70 p-4"
              >
                <div className="flex items-baseline justify-between">
                  <h3 className="font-display text-lg text-(--color-paper)">
                    {axis.label}
                  </h3>
                  <span className="font-mono text-xs font-semibold text-(--color-amber)">
                    {axis.weight}
                  </span>
                </div>
                <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-(--color-line)">
                  <div
                    className="h-full rounded-full bg-(--color-amber)"
                    style={{ width: `${axis.bar}%` }}
                  />
                </div>
                <p className="mt-3 text-xs leading-5 text-(--color-meta)">
                  {axis.detail}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SECTION 5: PRODUCTION FAQ */}
      <section id="specs" className="border-t border-(--color-line) py-16">
        <p className="section-kicker">05 / Specifications &amp; FAQ</p>
        <h2 className="mt-2 font-display text-3xl text-(--color-paper)">
          Pre-Production Operational Notes
        </h2>

        <div className="mt-6 divide-y divide-(--color-line) border border-(--color-line) bg-(--color-surface)/50">
          <details className="group p-5" open>
            <summary className="flex cursor-pointer list-none items-center justify-between font-display text-lg text-(--color-paper)">
              <span>How does Studio Scout prevent hallucinated filming locations?</span>
              <span className="font-mono text-xs text-(--color-amber) transition-transform group-open:rotate-45">
                +
              </span>
            </summary>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-(--color-meta)">
              Every scene query is grounded through live web search
              (ToolParallelAiSearch) against municipal film directories, venue
              listings, and regional databases. If no verifiable real-world
              candidate exists, the scene is explicitly flagged as{" "}
              <code className="text-(--color-flag)">NEEDS MANUAL SOURCING</code>{" "}
              rather than fabricating a venue.
            </p>
          </details>

          <details className="group p-5">
            <summary className="flex cursor-pointer list-none items-center justify-between font-display text-lg text-(--color-paper)">
              <span>Can I re-scout the same screenplay across multiple regions?</span>
              <span className="font-mono text-xs text-(--color-amber) transition-transform group-open:rotate-45">
                +
              </span>
            </summary>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-(--color-meta)">
              Yes. Screenplay PDF breakdowns are cached by SHA-256 content hash,
              so switching your target region from New Jersey to Atlanta or
              Vancouver skips redundant PDF parsing and immediately dispatches
              regional grounding.
            </p>
          </details>

          <details className="group p-5">
            <summary className="flex cursor-pointer list-none items-center justify-between font-display text-lg text-(--color-paper)">
              <span>What export formats are supported for physical production?</span>
              <span className="font-mono text-xs text-(--color-amber) transition-transform group-open:rotate-45">
                +
              </span>
            </summary>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-(--color-meta)">
              From the Scouting Dossier dashboard, you can export the full
              multi-scene ranking and 6-axis breakdown as a spreadsheet-ready{" "}
              <strong>CSV</strong> or structured <strong>JSON</strong> payload,
              with direct Google Maps links for every candidate venue.
            </p>
          </details>
        </div>
      </section>
    </main>
  );
}
