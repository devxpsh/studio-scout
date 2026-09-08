import { useState } from "react";
import {
  allUniqueConflicts,
  needsManualSourcing,
  type ShootPlan,
} from "../lib/types";
import { ContactSheet } from "../components/ContactSheet/ContactSheet";
import { ConflictsPanel } from "../components/ConflictsPanel/ConflictsPanel";
import { CandidateCard } from "../components/CandidateCard/CandidateCard";
import type { StudioScoutReport } from "../lib/types";

export function Dashboard({
  plan,
  agentReport,
  onPlanRefresh,
}: {
  plan: ShootPlan;
  agentReport?: StudioScoutReport | null;
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
    <main
      id="overview"
      className="mx-auto max-w-6xl px-5 py-12 sm:px-8 lg:py-16"
    >
      <div className="mb-8 flex items-end justify-between gap-4 border-b border-(--color-line) pb-5">
        <div>
          <p className="section-kicker">03 / Scouting report</p>
          <h1 className="mt-3 font-display text-4xl text-(--color-paper) sm:text-5xl">
            {plan.title}
          </h1>
        </div>
        {onPlanRefresh && (
          <button
            type="button"
            onClick={onPlanRefresh}
            className="rounded-sm border border-(--color-line) px-3 py-2 font-mono text-[10px] uppercase tracking-widest text-(--color-paper) transition-colors hover:border-(--color-amber) hover:text-(--color-amber)"
          >
            Refresh plan
          </button>
        )}
      </div>

      <div className="mb-8 grid gap-px border border-(--color-line) bg-(--color-line) sm:grid-cols-3">
        <div className="bg-(--color-surface) p-4">
          <span className="font-mono text-[10px] uppercase tracking-widest text-(--color-meta)">
            Scenes
          </span>
          <strong className="mt-2 block font-display text-3xl text-(--color-paper)">
            {plan.scenes.length}
          </strong>
        </div>
        <div className="bg-(--color-surface) p-4">
          <span className="font-mono text-[10px] uppercase tracking-widest text-(--color-meta)">
            Locations
          </span>
          <strong className="mt-2 block font-display text-3xl text-(--color-paper)">
            {uniqueLocations}
          </strong>
        </div>
        <div className="bg-(--color-surface) p-4">
          <span className="font-mono text-[10px] uppercase tracking-widest text-(--color-meta)">
            Plan status
          </span>
          <strong className="mt-2 block font-mono text-xs uppercase text-(--color-amber)">
            Grounded / ready
          </strong>
        </div>
      </div>

      {agentReport && (
        <section className="mb-8 border border-(--color-amber)/50 bg-(--color-surface)/60 p-5">
          <div className="mb-3 flex flex-wrap items-baseline justify-between gap-3">
            <p className="font-mono text-xs uppercase tracking-widest text-(--color-amber)">
              Agent synthesis
            </p>
            <span className="font-mono text-xs text-(--color-meta)">
              {agentReport.region_used} ·{" "}
              {agentReport.region_source.replaceAll("_", " ")}
            </span>
          </div>
          <p className="max-w-3xl text-sm leading-6 text-[var(--color-paper)]/85">
            {agentReport.overall_summary}
          </p>
        </section>
      )}

      <section className="mb-8">
        <div className="mb-3 flex items-baseline justify-between">
          <p className="section-kicker">Risk register</p>
          <span className="font-mono text-[10px] uppercase text-(--color-meta)">
            {conflicts.length} flagged
          </span>
        </div>
        <ConflictsPanel conflicts={conflicts} />
      </section>

      <p className="mb-3 section-kicker">Scene contact sheet</p>
      <ContactSheet
        scenes={plan.scenes}
        selectedScene={selectedScene}
        onSelect={setSelectedScene}
      />

      {scene && (
        <section className="mt-10 border-t border-(--color-line) pt-8">
          <div className="mb-1 flex items-baseline gap-3">
            <span className="font-mono text-xs text-(--color-meta)">
              #{String(scene.scene_number).padStart(2, "0")}
            </span>
            <h2 className="font-display text-2xl text-(--color-paper)">
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
        </section>
      )}
    </main>
  );
}
