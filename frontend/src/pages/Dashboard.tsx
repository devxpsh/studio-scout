import { useState } from "react";
import {
  allUniqueConflicts,
  needsManualSourcing,
  type ShootPlan,
} from "../lib/types";
import { ContactSheet } from "../components/ContactSheet/ContactSheet";
import { ConflictsPanel } from "../components/ConflictsPanel/ConflictsPanel";
import { CandidateCard } from "../components/CandidateCard/CandidateCard";

export function Dashboard({
  plan,
  onPlanRefresh,
}: {
  plan: ShootPlan;
  onPlanRefresh?: () => void;
}) {
  const [selectedScene, setSelectedScene] = useState<number | null>(
    plan.scenes[0]?.scene_number ?? null,
  );

  const conflicts = allUniqueConflicts(plan);
  const uniqueLocations = new Set(plan.scenes.map((s) => s.location)).size;
  const scene =
    plan.scenes.find((s) => s.scene_number === selectedScene) ?? null;

  return (
    <main className="min-h-screen max-w-5xl mx-auto px-6 py-10">
      <div className="mb-4 flex items-center justify-between gap-4">
        <p className="font-mono text-xs uppercase tracking-widest text-[var(--color-meta)]">
          Shoot Plan
        </p>
        {onPlanRefresh && (
          <button
            type="button"
            onClick={onPlanRefresh}
            className="rounded-sm border border-[var(--color-meta)]/40 px-3 py-1.5 font-mono text-[10px] uppercase tracking-widest text-[var(--color-paper)] transition-colors hover:border-[var(--color-amber)] hover:text-[var(--color-amber)]"
          >
            Refresh plan
          </button>
        )}
      </div>
      <h1 className="mb-4 font-display text-4xl text-[var(--color-paper)]">
        {plan.title}
      </h1>

      <div className="mb-8 flex flex-wrap gap-x-6 gap-y-2 font-mono text-xs text-[var(--color-meta)]">
        <span>{plan.scenes.length} scenes</span>
        <span>{uniqueLocations} unique locations</span>
        <span>{plan.shoot_plan_notes}</span>
      </div>

      <div className="mb-8">
        <ConflictsPanel conflicts={conflicts} />
      </div>

      <p className="mb-3 font-mono text-xs uppercase tracking-widest text-(--color-meta)">
        Scenes
      </p>
      <ContactSheet
        scenes={plan.scenes}
        selectedScene={selectedScene}
        onSelect={setSelectedScene}
      />

      {scene && (
        <div className="mt-10">
          <div className="mb-1 flex items-baseline gap-3">
            <span className="font-mono text-xs text-(--color-meta)">
              #{String(scene.scene_number).padStart(2, "0")}
            </span>
            <h2 className="font-display text-2xl text-[var(--color-paper)]">
              {scene.location}
            </h2>
          </div>

          {needsManualSourcing(scene) ? (
            <div className="mt-3 rounded-sm border border-[var(--color-flag)] p-4">
              <p className="mb-1 font-mono text-xs uppercase text-[var(--color-flag)]">
                Needs manual sourcing
              </p>
              <p className="text-sm text-[var(--color-paper)]">
                No grounded candidates were found for this scene — see the
                conflict below for details.
              </p>
            </div>
          ) : (
            <>
              <p className="mb-4 mt-1 text-sm italic text-[var(--color-paper)]/80">
                {scene.rationale}
              </p>
              <div className="grid gap-4 md:grid-cols-2">
                {scene.top_candidates.map((sc, i) => (
                  <CandidateCard
                    key={i}
                    scored={sc}
                    isRecommended={sc.candidate.name === scene.recommended}
                  />
                ))}
              </div>
            </>
          )}

          {scene.conflicts.length > 0 && (
            <div className="mt-4">
              <ConflictsPanel conflicts={scene.conflicts} />
            </div>
          )}
        </div>
      )}
    </main>
  );
}
