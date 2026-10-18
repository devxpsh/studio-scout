import type { ShootPlan, StudioScoutReport, TraceEvent } from "./types";

// Use same-origin in the production container while preserving the local Vite
// development workflow, where the API normally runs on port 8000.
const API_BASE = import.meta.env.VITE_API_BASE ?? (import.meta.env.DEV ? "http://localhost:8000" : "");

export async function uploadScreenplay(
  file: File,
  prompt: string,
  region: string | undefined,
  onEvent: (event: TraceEvent) => void,
  onRegionRequired: (question: string) => void,
  onAgentReport: (report: StudioScoutReport) => void,
  onComplete: (plan?: ShootPlan, runId?: string) => void,
  onError: (error: Error) => void,
  signal?: AbortSignal,
): Promise<void> {
  try {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("prompt", prompt);
    if (region) formData.append("region", region);

    const response = await fetch(`${API_BASE}/api/upload`, {
      method: "POST",
      body: formData,
      signal,
    });

    if (!response.ok) {
      throw new Error(
        `Upload failed (HTTP ${response.status}${response.statusText ? `: ${response.statusText}` : ""})`,
      );
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error("No response body");
    }

    const decoder = new TextDecoder();
    let buffer = "";
    let streamedPlan: ShootPlan | undefined;
    let streamedRunId: string | undefined;
    let regionPrompted = false;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");

      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          let data: Record<string, unknown>;
          try {
            data = JSON.parse(line.slice(6)) as Record<string, unknown>;
          } catch {
            continue;
          }

          if (typeof data.error === "string") {
            throw new Error(data.error);
          }

          if (typeof data.run_id === "string") {
            streamedRunId = data.run_id;
          }

          if (data.shoot_plan) {
            streamedPlan = data.shoot_plan as ShootPlan;
            continue;
          }

          if (data.done) {
            if (!regionPrompted) {
              onComplete(streamedPlan, streamedRunId);
            }
            return;
          }

          if (data.region_required && typeof data.question === "string") {
            regionPrompted = true;
            onRegionRequired(data.question);
            continue;
          }

          if (data.agent_report) {
            onAgentReport(data.agent_report as StudioScoutReport);
            continue;
          }

          if (data.id && data.agent && data.status !== undefined) {
            onEvent(data as unknown as TraceEvent);
          }
        }
      }
    }

    if (regionPrompted) {
      return;
    }
    if (!streamedPlan && !streamedRunId) {
      throw new Error(
        "The scouting stream closed before finishing. Please click Run again.",
      );
    }
    onComplete(streamedPlan, streamedRunId);
  } catch (error) {
    onError(error instanceof Error ? error : new Error(String(error)));
  }
}

export async function fetchRecommendations(runId?: string): Promise<ShootPlan> {
  const query = runId ? `?run_id=${encodeURIComponent(runId)}` : "";
  const response = await fetch(`${API_BASE}/api/recommendations${query}`, {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error(
      `Failed to fetch recommendations (HTTP ${response.status}${response.statusText ? `: ${response.statusText}` : ""})`,
    );
  }

  return response.json() as Promise<ShootPlan>;
}
