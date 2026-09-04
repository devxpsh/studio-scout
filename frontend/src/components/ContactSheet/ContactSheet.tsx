import { needsManualSourcing, type SceneRecommendation } from "../../lib/types";

export function ContactSheet({
  scenes,
  selectedScene,
  onSelect,
}: {
  scenes: SceneRecommendation[];
  selectedScene: number | null;
  onSelect: (sceneNumber: number) => void;
}) {
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
      {scenes.map((scene) => {
        const flagged = needsManualSourcing(scene);
        const top = scene.top_candidates[0];
        const isSelected = selectedScene === scene.scene_number;

        return (
          <button
            key={scene.scene_number}
            onClick={() => onSelect(scene.scene_number)}
            className={`relative rounded-sm border p-3 text-left transition-colors ${
              isSelected
                ? "border-[var(--color-amber)]"
                : "border-[var(--color-meta)]/40 hover:border-[var(--color-meta)]"
            }`}
          >
            <div className="mb-2 flex items-center justify-between">
              <span className="font-mono text-[10px] text-(--color-meta)">
                #{String(scene.scene_number).padStart(2, "0")}
              </span>
              {flagged ? (
                <span className="rounded-full border border-[var(--color-flag)] px-1.5 py-0.5 font-mono text-[9px] uppercase text-[var(--color-flag)]">
                  needs sourcing
                </span>
              ) : scene.conflicts.length > 0 ? (
                <span className="rounded-full border border-[var(--color-amber)] px-1.5 py-0.5 font-mono text-[9px] uppercase text-[var(--color-amber)]">
                  flagged
                </span>
              ) : null}
            </div>

            <p className="mb-1 font-display text-base leading-snug text-[var(--color-paper)]">
              {scene.location}
            </p>

            {flagged ? (
              <p className="font-mono text-xs text-(--color-meta)">
                no candidates found
              </p>
            ) : (
              <>
                <p className="truncate font-mono text-xs text-[var(--color-paper)]">
                  {scene.recommended}
                </p>
                {top && (
                  <p className="font-mono text-[10px] text-(--color-meta)">
                    {top.composite_score.toFixed(1)} composite
                  </p>
                )}
              </>
            )}
          </button>
        );
      })}
    </div>
  );
}
