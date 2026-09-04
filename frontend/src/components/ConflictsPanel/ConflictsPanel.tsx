import type { Conflict, ConflictSeverity } from "../../lib/types";

const SEVERITY_ORDER: ConflictSeverity[] = ["blocker", "warning", "info"];
const SEVERITY_COLOR: Record<ConflictSeverity, string> = {
  blocker: "var(--color-flag)",
  warning: "var(--color-amber)",
  info: "var(--color-meta)",
};

export function ConflictsPanel({ conflicts }: { conflicts: Conflict[] }) {
  if (conflicts.length === 0) return null;

  const ordered = SEVERITY_ORDER.flatMap((sev) =>
    conflicts.filter((c) => c.severity === sev),
  );

  return (
    <div className="rounded-sm border border-[var(--color-meta)]/40">
      <div className="border-b border-[var(--color-meta)]/40 px-4 py-2">
        <span className="font-mono text-xs uppercase tracking-widest text-(--color-meta)">
          Conflicts &amp; Flags
        </span>
      </div>
      <div className="divide-y divide-[var(--color-meta)]/20">
        {ordered.map((c, i) => (
          <div key={i} className="px-4 py-3">
            <div className="mb-1 flex flex-wrap items-center gap-2">
              <span
                className="rounded-full px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest"
                style={{
                  color: SEVERITY_COLOR[c.severity],
                  border: `1px solid ${SEVERITY_COLOR[c.severity]}`,
                }}
              >
                {c.severity}
              </span>
              <span className="font-mono text-[10px] uppercase text-(--color-meta)">
                {c.type.replace("_", " ")}
              </span>
              <span className="font-mono text-[10px] text-(--color-meta)">
                scene{c.affected_scenes.length > 1 ? "s" : ""}{" "}
                {c.affected_scenes.join(", ")}
              </span>
            </div>
            <p className="text-sm text-[var(--color-paper)]">{c.description}</p>
            <p className="mt-1 text-xs text-(--color-meta)">
              → {c.suggested_resolution}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
