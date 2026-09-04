import { useEffect, useRef, useState } from "react";
import { AgentTrace } from "../components/AgentTrace/AgentTrace";
import { sampleTraceEvents } from "../lib/fixtures/traceEvents";
import { uploadScreenplay, fetchRecommendations } from "../lib/api";
import type { ShootPlan, StudioScoutReport, TraceEvent } from "../lib/types";

const USE_FIXTURE = false;

export function Processing({
  file,
  prompt,
  onComplete,
}: {
  file: File | null;
  prompt: string;
  onComplete: (
    plan: ShootPlan | null,
    agentReport: StudioScoutReport | null,
  ) => void;
}) {
  const [events, setEvents] = useState<TraceEvent[]>([]);
  const [visualDone, setVisualDone] = useState(false);
  const [backendDone, setBackendDone] = useState(false);
  const [statusNote, setStatusNote] = useState<string | null>(null);
  const [regionQuestion, setRegionQuestion] = useState<string | null>(null);
  const [region, setRegion] = useState("");
  const [regionInput, setRegionInput] = useState("");
  const resultPlan = useRef<ShootPlan | null>(null);
  const agentReport = useRef<StudioScoutReport | null>(null);

  useEffect(() => {
    const interval = setInterval(() => {
      setEvents((prev) => {
        if (prev.length >= sampleTraceEvents.length) return prev;
        return [...prev, sampleTraceEvents[prev.length]];
      });
    }, 700);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
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
      try {
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
            resolve,
            reject,
            controller.signal,
          );
        });
        if (cancelled) return;

        setStatusNote(
          "Loading the latest recommendations for this screenplay...",
        );
        resultPlan.current = await fetchRecommendations();
      } catch (err) {
        if (
          cancelled ||
          (err instanceof DOMException && err.name === "AbortError")
        ) {
          return;
        }
        console.error("Backend pipeline failed:", err);
        resultPlan.current = null;
        setBackendDone(true);
        setStatusNote(
          `Backend run failed: ${err instanceof Error ? err.message : "unknown error"}. Retry after a short wait if Vertex AI is busy.`,
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
  }, [file, prompt, region]);

  useEffect(() => {
    if (visualDone && backendDone && !regionQuestion && resultPlan.current)
      onComplete(resultPlan.current, agentReport.current);
  }, [visualDone, backendDone, onComplete]);

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-6">
      <div className="w-full max-w-2xl">
        <p className="mb-4 font-mono text-xs tracking-widest uppercase text-(--color-meta)">
          Processing screenplay
        </p>
        <AgentTrace events={events} />
        {regionQuestion && (
          <form
            className="mt-5 flex flex-col gap-3 border border-(--color-amber)/60 p-4"
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
          <p className="mt-4 font-mono text-xs text-(--color-meta)">
            {statusNote}
          </p>
        )}
      </div>
    </main>
  );
}
