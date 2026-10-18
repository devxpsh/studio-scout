import { useEffect, useRef, useState } from "react";
import { AgentTrace } from "../components/AgentTrace/AgentTrace";
import { sampleTraceEvents } from "../lib/fixtures/traceEvents";
import { uploadScreenplay, fetchRecommendations } from "../lib/api";
import type { ShootPlan, StudioScoutReport, TraceEvent } from "../lib/types";

const USE_FIXTURE = false;

export function Processing({
  file,
  prompt,
  initialRegion = "",
  onComplete,
  onBack,
}: {
  file: File | null;
  prompt: string;
  initialRegion?: string;
  onComplete: (
    plan: ShootPlan | null,
    agentReport: StudioScoutReport | null,
    runId?: string,
  ) => void;
  onBack?: () => void;
}) {
  const [events, setEvents] = useState<TraceEvent[]>([]);
  const [visualDone, setVisualDone] = useState(!USE_FIXTURE);
  const [backendDone, setBackendDone] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [statusNote, setStatusNote] = useState<string | null>(null);
  const [regionQuestion, setRegionQuestion] = useState<string | null>(null);
  const [region, setRegion] = useState(initialRegion);
  const [regionInput, setRegionInput] = useState(initialRegion);
  const resultPlan = useRef<ShootPlan | null>(null);
  const agentReport = useRef<StudioScoutReport | null>(null);
  const latestRunId = useRef<string | undefined>(undefined);

  useEffect(() => {
    if (!USE_FIXTURE) return;
    const interval = setInterval(() => {
      setEvents((prev) => {
        if (prev.length >= sampleTraceEvents.length) return prev;
        return [...prev, sampleTraceEvents[prev.length]];
      });
    }, 700);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!USE_FIXTURE) return;
    if (events.length === sampleTraceEvents.length && !visualDone) {
      const t = setTimeout(() => setVisualDone(true), 500);
      return () => clearTimeout(t);
    }
  }, [events.length, visualDone]);

  useEffect(() => {
    if (USE_FIXTURE || !file) {
      setBackendDone(true);
      return;
    }

    let cancelled = false;
    const controller = new AbortController();

    async function run() {
      setHasError(false);
      try {
        let streamedPlan: ShootPlan | undefined;
        let streamedRunId: string | undefined;

        await new Promise<void>((resolve, reject) => {
          uploadScreenplay(
            file!,
            prompt,
            region || undefined,
            (event) => setEvents((prev) => [...prev, event]),
            (question) => {
              setRegionQuestion(question);
              setStatusNote("Research is paused until a region is supplied.");
            },
            (report) => {
              agentReport.current = report;
              setStatusNote(
                "Agent synthesis received. Finalizing scored plan...",
              );
            },
            (plan, runId) => {
              streamedPlan = plan;
              streamedRunId = runId;
              resolve();
            },
            reject,
            controller.signal,
          );
        });
        if (cancelled) return;

        latestRunId.current = streamedRunId;

        if (streamedPlan) {
          resultPlan.current = streamedPlan;
        } else if (!regionQuestion) {
          setStatusNote(
            "Loading the latest recommendations for this screenplay...",
          );
          resultPlan.current = await fetchRecommendations(streamedRunId);
        }
      } catch (err) {
        if (
          cancelled ||
          (err instanceof DOMException && err.name === "AbortError")
        ) {
          return;
        }
        console.error("Backend pipeline failed:", err);
        resultPlan.current = null;
        setHasError(true);
        setBackendDone(true);
        setStatusNote(
          `Backend run failed: ${err instanceof Error ? err.message : "unknown error"}. Retry after a short wait, and keep uploads to 5 scenes at a time for best reliability.`,
        );
      } finally {
        if (!cancelled) setBackendDone(true);
      }
    }

    // React Strict Mode replays effects during development.
    const startTimer = setTimeout(() => {
      void run();
    }, 0);
    return () => {
      cancelled = true;
      clearTimeout(startTimer);
      controller.abort();
    };
  }, [file, prompt, region, retryCount]);

  useEffect(() => {
    if (visualDone && backendDone && !regionQuestion && resultPlan.current) {
      onComplete(
        resultPlan.current,
        agentReport.current,
        latestRunId.current,
      );
    }
  }, [visualDone, backendDone, regionQuestion, onComplete]);

  return (
    <main id="run" className="mx-auto max-w-6xl px-5 py-14 sm:px-8 lg:py-20">
      <div className="mx-auto max-w-3xl">
        <div className="mb-6 flex items-end justify-between gap-5 border-b border-(--color-line) pb-5">
          <div>
            <p className="section-kicker">02 / Live production run</p>
            <h1 className="mt-3 font-display text-4xl text-(--color-paper) sm:text-5xl">
              Reading the script.
            </h1>
          </div>
          <span className="hidden font-mono text-[10px] uppercase tracking-widest text-(--color-amber) sm:block">
            Live / SSE · ~1–3 Min Est.
          </span>
        </div>

        <div
          role="note"
          aria-label="Expected run duration and scene batching tip"
          className="mb-6 flex flex-wrap items-center justify-between gap-3 rounded-sm border border-(--color-amber)/35 bg-(--color-surface)/90 px-4 py-3"
        >
          <p className="text-xs leading-5 text-(--color-meta)">
            <span className="mr-2 font-mono text-[10px] uppercase tracking-widest text-(--color-amber)">
              ● Est. Runtime: ~3 Min
            </span>
            A standard 5-scene run takes ~1–3 minutes to extract, ground live venues, and score. Running <strong className="font-normal text-(--color-paper)">5 scenes at a time</strong> is recommended for optimal reliability.
          </p>
        </div>

        <AgentTrace events={events} />
        {regionQuestion && (
          <form
            className="mt-5 flex flex-col gap-3 border border-(--color-amber)/60 bg-(--color-surface) p-5"
            onSubmit={(e) => {
              e.preventDefault();
              const value = regionInput.trim();
              if (!value) return;
              setRegion(value);
              setRegionQuestion(null);
              setBackendDone(false);
              setStatusNote(null);
            }}
          >
            <p className="font-mono text-xs text-(--color-amber)">
              {regionQuestion}
            </p>
            <div className="flex gap-3">
              <input
                name="region"
                value={regionInput}
                onChange={(e) => setRegionInput(e.target.value)}
                placeholder="Country, state, city, or region"
                className="min-w-0 flex-1 border border-(--color-meta)/60 bg-transparent px-3 py-2 font-mono text-sm text-(--color-paper) outline-none focus:border-(--color-amber)"
                autoFocus
              />
              <button
                type="submit"
                className="border border-(--color-amber) px-3 font-mono text-xs uppercase text-(--color-amber)"
              >
                Continue
              </button>
            </div>
          </form>
        )}
        {statusNote && visualDone && (
          <div className="mt-4 border-l-2 border-(--color-amber) px-3">
            <p className="font-mono text-xs text-(--color-meta)">
              {statusNote}
            </p>
            {hasError && (
              <div className="mt-3 flex gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setEvents([]);
                    setBackendDone(false);
                    setStatusNote(null);
                    setRetryCount((c) => c + 1);
                  }}
                  className="rounded-sm border border-(--color-amber) px-3 py-1.5 font-mono text-[10px] uppercase tracking-widest text-(--color-amber) transition-colors hover:bg-(--color-amber) hover:text-(--color-ink)"
                >
                  Retry run
                </button>
                {onBack && (
                  <button
                    type="button"
                    onClick={onBack}
                    className="rounded-sm border border-(--color-line) px-3 py-1.5 font-mono text-[10px] uppercase tracking-widest text-(--color-paper) transition-colors hover:border-(--color-amber)"
                  >
                    Back to intake
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
