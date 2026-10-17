import type { ReactNode } from "react";

type Screen = "upload" | "processing" | "dashboard";

export function AppShell({
  children,
  screen,
  onNewScout,
  onOpenReport,
}: {
  children: ReactNode;
  screen: Screen;
  onNewScout?: () => void;
  onOpenReport?: () => void;
}) {
  const isDashboard = screen === "dashboard";

  return (
    <div className="flex min-h-screen flex-col">
      <div className="sprocket-strip" aria-hidden="true" />
      <header className="sticky top-0 z-30 border-b border-(--color-line) bg-(--color-ink)/92 backdrop-blur-md">
        <div className="mx-auto flex min-h-18 max-w-6xl items-center justify-between gap-6 px-5 sm:px-8">
          <button
            type="button"
            onClick={onNewScout}
            className="flex items-center gap-3.5 text-left transition-opacity hover:opacity-90"
          >
            <div className="brand-mark" aria-hidden="true">
              <span />
              <span />
              <span />
            </div>
            <div>
              <p className="font-display text-lg leading-none text-(--color-paper)">
                Studio Scout
              </p>
              <p className="mt-1 font-mono text-[10px] uppercase tracking-[0.22em] text-(--color-meta)">
                Location intelligence desk
              </p>
            </div>
          </button>

          <nav
            className="hidden items-center gap-7 md:flex"
            aria-label="Primary"
          >
            <button
              type="button"
              onClick={onNewScout}
              className={`shell-link ${screen === "upload" ? "shell-link-active" : ""}`}
            >
              01 / Intake
            </button>
            {screen === "upload" && (
              <>
                <a className="shell-link" href="#contact-preview">
                  Contact Sheet
                </a>
                <a className="shell-link" href="#pipeline">
                  4-Unit Pipeline
                </a>
                <a className="shell-link" href="#rubric">
                  6-Axis Rubric
                </a>
              </>
            )}
            {screen === "processing" && (
              <span className="shell-link shell-link-active">
                02 / Live Dispatch
              </span>
            )}
            <button
              type="button"
              onClick={onOpenReport}
              className={`shell-link ${isDashboard ? "shell-link-active" : ""}`}
            >
              03 / Scouting Dossier
            </button>
          </nav>

          <div className="flex items-center gap-3">
            <span className="hidden items-center gap-2 rounded-sm border border-(--color-line) bg-(--color-surface)/80 px-2.5 py-1.5 font-mono text-[10px] uppercase tracking-widest text-(--color-meta) lg:flex">
              <span className="status-dot" />
              ADK + Parallel Ready
            </span>
            {screen === "upload" && onOpenReport && (
              <button
                type="button"
                onClick={onOpenReport}
                className="rounded-sm border border-(--color-amber)/60 bg-(--color-amber)/10 px-3 py-2 font-mono text-[10px] uppercase tracking-widest text-(--color-amber) transition-colors hover:bg-(--color-amber) hover:text-(--color-ink)"
              >
                Sample Dossier
              </button>
            )}
            {screen !== "upload" && onNewScout && (
              <button
                type="button"
                onClick={onNewScout}
                className="rounded-sm border border-(--color-line) px-3 py-2 font-mono text-[10px] uppercase tracking-widest text-(--color-paper) transition-colors hover:border-(--color-amber) hover:text-(--color-amber)"
              >
                + New Scout
              </button>
            )}
          </div>
        </div>
      </header>

      <div className="mx-auto w-full max-w-6xl px-5 pt-3 sm:px-8">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-(--color-line)/60 pb-3 font-mono text-[10px] uppercase tracking-[0.18em] text-(--color-meta)">
          <span>UNIT 01 // PRE-PRODUCTION LOCATION INTELLIGENCE</span>
          <span className="hidden sm:inline">
            GEMINI 2.5 PRO · GOOGLE ADK · PARALLEL WEB SEARCH
          </span>
        </div>
      </div>

      <div className="flex-1">{children}</div>

      <footer className="mt-20 border-t border-(--color-line) bg-(--color-surface)/50">
        <div className="mx-auto grid max-w-6xl gap-10 px-5 py-12 sm:grid-cols-2 sm:px-8 lg:grid-cols-4">
          <div className="sm:col-span-2 lg:col-span-1">
            <div className="flex items-center gap-3">
              <div className="brand-mark" aria-hidden="true">
                <span />
                <span />
                <span />
              </div>
              <span className="font-display text-lg text-(--color-paper)">
                Studio Scout
              </span>
            </div>
            <p className="mt-3 max-w-xs text-xs leading-6 text-(--color-meta)">
              Source-backed location scouting desk for film &amp; episodic
              pre-production. Parses screenplay PDFs into grounded, 6-axis
              scored shooting plans.
            </p>
          </div>

          <div>
            <p className="font-mono text-[10px] uppercase tracking-widest text-(--color-amber)">
              Multi-Agent Units
            </p>
            <ul className="mt-3 space-y-2 font-mono text-xs text-(--color-meta)">
              <li>01 · ScriptBreakdownAgent</li>
              <li>02 · LocationGrounder</li>
              <li>03 · LogisticsRiskAssessor</li>
              <li>04 · 6-Axis Composite Scorer</li>
            </ul>
          </div>

          <div>
            <p className="font-mono text-[10px] uppercase tracking-widest text-(--color-amber)">
              Scoring Dimensions
            </p>
            <ul className="mt-3 space-y-2 font-mono text-xs text-(--color-meta)">
              <li>Visual Match (30%)</li>
              <li>Production Feasibility (20%)</li>
              <li>Crew &amp; Access Logistics (15%)</li>
              <li>Cost Fit &amp; Permit Ease (25%)</li>
            </ul>
          </div>

          <div>
            <p className="font-mono text-[10px] uppercase tracking-widest text-(--color-amber)">
              Deliverables
            </p>
            <ul className="mt-3 space-y-2 font-mono text-xs text-(--color-meta)">
              <li>Scene Contact Sheet</li>
              <li>Cited Venue Evidence URLs</li>
              <li>Google Maps Deep Links</li>
              <li>CSV &amp; JSON Call-Sheet Export</li>
            </ul>
          </div>
        </div>

        <div className="border-t border-(--color-line)/60">
          <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-5 py-5 font-mono text-[10px] uppercase tracking-widest text-(--color-meta) sm:px-8">
            <span>STUDIO SCOUT // RESEARCH BEFORE ROLL</span>
            <span>BUILT WITH GOOGLE ADK &amp; GEMINI</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
