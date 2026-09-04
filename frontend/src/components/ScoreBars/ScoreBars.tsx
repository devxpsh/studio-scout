import type { ScoreBreakdown } from "../../lib/types";

const DIMENSIONS: { key: keyof ScoreBreakdown; label: string }[] = [
  { key: "visual_match", label: "Visual match" },
  { key: "feasibility", label: "Feasibility" },
  { key: "logistics", label: "Logistics" },
  { key: "cost_fit", label: "Cost fit" },
  { key: "permit_ease", label: "Permit ease" },
  { key: "evidence_confidence", label: "Evidence conf." },
];

export function ScoreBars({ score }: { score: ScoreBreakdown }) {
  return (
    <div className="space-y-1.5">
      {DIMENSIONS.map(({ key, label }) => (
        <div key={key} className="flex items-center gap-2">
          <span className="w-28 shrink-0 font-mono text-[10px] uppercase text-(--color-meta)">
            {label}
          </span>
          <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-[var(--color-meta)]/20">
            <div
              className="h-full rounded-full bg-[var(--color-amber)]"
              style={{ width: `${score[key]}%` }}
            />
          </div>
          <span className="w-6 shrink-0 text-right font-mono text-[10px] text-[var(--color-ink)]">
            {score[key]}
          </span>
        </div>
      ))}
    </div>
  );
}
