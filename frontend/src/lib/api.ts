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
  onComplete: () => void,
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
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error("No response body");
    }

    const decoder = new TextDecoder();
    let buffer = "";

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

          if (data.done) {
            onComplete();
            return;
          }

          if (data.region_required && typeof data.question === "string") {
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

    onComplete();
  } catch (error) {
    onError(error instanceof Error ? error : new Error(String(error)));
  }
}

export async function fetchRecommendations(): Promise<ShootPlan> {
  const response = await fetch(`${API_BASE}/api/recommendations`, {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch recommendations: ${response.statusText}`);
  }

  return response.json() as Promise<ShootPlan>;
}
