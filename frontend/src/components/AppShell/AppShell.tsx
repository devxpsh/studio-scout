import type { ReactNode } from "react";

type Screen = "upload" | "processing" | "dashboard";

export function AppShell({
  children,
  screen,
  onNewScout,
}: {
  children: ReactNode;
  screen: Screen;
  onNewScout?: () => void;
}) {
  const isDashboard = screen === "dashboard";

  return (
    <div className="min-h-screen">
      <header className="border-b border-(--color-line) bg-(--color-ink)/95 backdrop-blur">
        <div className="mx-auto flex min-h-18 max-w-6xl items-center justify-between gap-6 px-5 sm:px-8">
          <div className="flex items-center gap-3">
            <div className="brand-mark" aria-hidden="true">
              <span />
              <span />
              <span />
            </div>
            <div>
              <p className="font-display text-lg leading-none text-(--color-paper)">
                Studio Scout
              </p>
              <p className="mt-1 font-mono text-[9px] uppercase tracking-[0.22em] text-(--color-meta)">
                Location intelligence desk
              </p>
            </div>
          </div>

          <nav
            className="hidden items-center gap-7 sm:flex"
            aria-label="Primary"
          >
            <a
              className={`shell-link ${screen === "upload" ? "shell-link-active" : ""}`}
              href="#intake"
            >
              Intake
            </a>
            <a
              className={`shell-link ${screen === "processing" ? "shell-link-active" : ""}`}
              href="#run"
            >
              Live run
            </a>
            <a
              className={`shell-link ${isDashboard ? "shell-link-active" : ""}`}
              href={isDashboard ? "#overview" : "#intake"}
            >
              Report
            </a>
          </nav>

          <div className="flex items-center gap-3">
            <span className="hidden items-center gap-2 font-mono text-[9px] uppercase tracking-widest text-(--color-meta) md:flex">
              <span className="status-dot" />
              System ready
            </span>
            {onNewScout && (
              <button
                type="button"
                onClick={onNewScout}
                className="rounded-sm border border-(--color-line) px-3 py-2 font-mono text-[9px] uppercase tracking-widest text-(--color-paper) transition-colors hover:border-(--color-amber) hover:text-(--color-amber)"
              >
                New scout
              </button>
            )}
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-6xl px-5 py-3 sm:px-8">
        <div className="flex items-center justify-between border-b border-(--color-line)/60 pb-3 font-mono text-[9px] uppercase tracking-[0.18em] text-(--color-meta)">
          <span>Production intelligence / 01</span>
          <span>ADK + Parallel grounded</span>
        </div>
      </div>

      {children}

      <footer className="mx-auto flex max-w-6xl items-center justify-between px-5 pb-8 pt-10 font-mono text-[9px] uppercase tracking-widest text-(--color-meta) sm:px-8">
        <span>Studio Scout</span>
        <span>Research before roll</span>
      </footer>
    </div>
  );
}
