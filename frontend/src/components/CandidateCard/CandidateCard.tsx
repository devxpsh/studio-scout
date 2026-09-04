import type { ScoredCandidate } from "../../lib/types";
import { ScoreBars } from "../ScoreBars/ScoreBars";

export function CandidateCard({
  scored,
  isRecommended,
}: {
  scored: ScoredCandidate;
  isRecommended: boolean;
}) {
  const { candidate, score, composite_score } = scored;

  return (
    <div
      className={`rounded-sm border bg-[var(--color-paper)] p-4 text-[var(--color-ink)] ${
        isRecommended
          ? "border-2 border-[var(--color-amber)]"
          : "border-[var(--color-meta)]/40"
      }`}
    >
      <div className="mb-1 flex items-start justify-between gap-3">
        <h4 className="font-display text-lg leading-tight">{candidate.name}</h4>
        <span className="shrink-0 rounded-full bg-[var(--color-ink)] px-2 py-0.5 font-mono text-xs text-[var(--color-amber)]">
          {composite_score.toFixed(1)}
        </span>
      </div>

      {isRecommended && (
        <span className="font-mono text-[10px] uppercase tracking-widest text-[var(--color-flag)]">
          Recommended
        </span>
      )}

      <p className="mt-1 text-xs text-(--color-meta)">
        {candidate.address_or_area}
      </p>
      <p className="mt-2 text-sm">{candidate.description}</p>

      <div className="mt-3">
        <ScoreBars score={score} />
      </div>

      {candidate.evidence.length > 0 ? (
        <ul className="mt-3 space-y-1">
          {candidate.evidence.map((e, i) => (
            <li key={i}>
              <a
                href={e.source_url}
                target="_blank"
                rel="noreferrer"
                className="font-mono text-[10px] text-(--color-meta) underline hover:text-[var(--color-ink)]"
              >
                {e.source_title}
              </a>
            </li>
          ))}
        </ul>
      ) : (
        // Per the Phase 4 data contract: empty evidence isn't a red flag on its
        // own — evidence_confidence in the bars above already reflects it.
        <p className="mt-3 font-mono text-[10px] text-(--color-meta)">
          No cited source — see evidence confidence above.
        </p>
      )}
    </div>
  );
}
