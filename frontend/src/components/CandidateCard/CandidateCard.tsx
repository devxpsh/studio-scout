import type { ScoredCandidate } from "../../lib/types";
import { ScoreBars } from "../ScoreBars/ScoreBars";

export function CandidateCard({
  scored,
  rank,
  isRecommended,
}: {
  scored: ScoredCandidate;
  rank?: number;
  isRecommended: boolean;
}) {
  const { candidate, score, composite_score } = scored;

  return (
    <div
      className={`flex flex-col justify-between rounded-sm border bg-[var(--color-paper)] p-5 text-[var(--color-ink)] transition-shadow hover:shadow-lg ${
        isRecommended
          ? "border-2 border-[var(--color-amber)]"
          : "border-[var(--color-meta)]/40"
      }`}
    >
      <div>
        <div className="mb-2 flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            {rank !== undefined && (
              <span className="rounded-sm bg-[var(--color-ink)]/10 px-1.5 py-0.5 font-mono text-[10px] font-semibold uppercase text-[var(--color-ink)]">
                #{rank}
              </span>
            )}
            {isRecommended ? (
              <span className="rounded-sm bg-[var(--color-flag)] px-2 py-0.5 font-mono text-[9px] font-medium uppercase tracking-widest text-[var(--color-paper)]">
                Primary Pick
              </span>
            ) : (
              <span className="font-mono text-[9px] uppercase tracking-widest text-(--color-meta)">
                Backup Option
              </span>
            )}
          </div>
          <span className="shrink-0 rounded-full bg-[var(--color-ink)] px-2.5 py-0.5 font-mono text-xs font-medium text-[var(--color-amber)]">
            {composite_score.toFixed(1)} / 100
          </span>
        </div>

        <h4 className="font-display text-xl leading-tight">{candidate.name}</h4>

        <div className="mt-1.5 flex items-center justify-between gap-2 border-b border-[var(--color-ink)]/10 pb-2.5">
          <p className="font-mono text-xs text-(--color-meta)">
            {candidate.address_or_area}
          </p>
          <a
            href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${candidate.name} ${candidate.address_or_area}`)}`}
            target="_blank"
            rel="noreferrer"
            className="shrink-0 rounded-sm border border-[var(--color-ink)]/25 px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider text-[var(--color-ink)] transition-colors hover:bg-[var(--color-ink)] hover:text-[var(--color-paper)]"
          >
            Google Maps ↗
          </a>
        </div>

        <p className="mt-3 text-sm leading-relaxed text-[var(--color-ink)]/90">
          {candidate.description}
        </p>

        <div className="mt-4 rounded-sm bg-[var(--color-ink)]/[0.04] p-3">
          <ScoreBars score={score} />
        </div>
      </div>

      <div className="mt-4 border-t border-[var(--color-ink)]/10 pt-3">
        <p className="mb-1.5 font-mono text-[9px] uppercase tracking-widest text-(--color-meta)">
          Grounded Evidence ({candidate.evidence.length})
        </p>
        {candidate.evidence.length > 0 ? (
          <ul className="space-y-1.5">
            {candidate.evidence.map((e, i) => (
              <li key={i} className="text-xs">
                <a
                  href={e.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="font-mono text-[11px] font-medium text-[var(--color-ink)] underline decoration-[var(--color-amber)] underline-offset-2 hover:text-[var(--color-flag)]"
                >
                  {e.source_title} ↗
                </a>
                {e.snippet && (
                  <p className="mt-0.5 line-clamp-2 text-[11px] text-(--color-meta)">
                    “{e.snippet}”
                  </p>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <p className="font-mono text-[10px] text-(--color-meta)">
            No external URL cited — reflected in Evidence Confidence score above.
          </p>
        )}
      </div>
    </div>
  );
}
