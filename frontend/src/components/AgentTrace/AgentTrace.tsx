import { AGENT_LABELS, type AgentId, type TraceEvent } from "../../lib/types";

const AGENT_ORDER: AgentId[] = [
  "orchestrator",
  "script_breakdown",
  "location_grounding",
  "logistics_risk",
];

function agentStatus(
  agent: AgentId,
  events: TraceEvent[],
): "pending" | "running" | "done" {
  const forAgent = events.filter((e) => e?.agent === agent);
  if (forAgent.length === 0) return "pending";
  if (forAgent.some((e) => e.status === "done")) return "done";
  return "running";
}

function StatusMark({ status }: { status: "pending" | "running" | "done" }) {
  if (status === "done") {
    return <span className="text-(--color-amber) font-mono">●</span>;
  }
  if (status === "running") {
    return (
      <span className="text-(--color-amber) font-mono animate-pulse">◐</span>
    );
  }
  return <span className="text-(--color-meta) font-mono">○</span>;
}

export function AgentTrace({ events }: { events: TraceEvent[] }) {
  return (
    <div className="border border-(--color-meta)/40 rounded-sm">
      <div className="border-b border-(--color-meta)/40 px-4 py-2 flex items-center justify-between">
        <span className="font-mono text-xs tracking-widest uppercase text-(--color-meta)">
          Call Sheet — Agent Trace
        </span>
        <span className="font-mono text-xs text-(--color-meta)">4 units</span>
      </div>

      <div className="divide-y divide-(--color-meta)/20">
        {AGENT_ORDER.map((agent) => {
          const status = agentStatus(agent, events);
          const messages = events.filter((e) => e && e.agent === agent);
          return (
            <div key={agent} className="px-4 py-3">
              <div className="flex items-center gap-3">
                <StatusMark status={status} />
                <span className="font-display text-lg text-(--color-paper)">
                  {AGENT_LABELS[agent]}
                </span>
                <span className="ml-auto font-mono text-xs uppercase text-(--color-meta)">
                  {status}
                </span>
              </div>
              {messages.length > 0 && (
                <ul className="mt-2 ml-7 space-y-1">
                  {messages.map((m) => (
                    <li
                      key={m.id}
                      className="font-mono text-xs text-(--color-meta)"
                    >
                      {m.message}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
