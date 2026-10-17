import { useState } from "react";
import {
  allUniqueConflicts,
  needsManualSourcing,
  type ShootPlan,
  type StudioScoutReport,
} from "../lib/types";
import { ContactSheet } from "../components/ContactSheet/ContactSheet";
import { ConflictsPanel } from "../components/ConflictsPanel/ConflictsPanel";
import { CandidateCard } from "../components/CandidateCard/CandidateCard";

type SceneFilter = "all" | "ready" | "flagged" | "manual";

function downloadBlob(content: string, filename: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function exportPlanAsJson(plan: ShootPlan) {
  const slug =
    plan.title.toLowerCase().replace(/[^a-z0-9]+/g, "-") || "shoot-plan";
  downloadBlob(
    JSON.stringify(plan, null, 2),
    `${slug}-shoot-plan.json`,
    "application/json",
  );
}

function exportPlanAsCsv(plan: ShootPlan) {
  const slug =
    plan.title.toLowerCase().replace(/[^a-z0-9]+/g, "-") || "shoot-plan";
  const headers = [
    "scene_number",
    "scene_location",
    "recommended_candidate",
    "candidate_rank",
    "candidate_name",
    "address_or_area",
    "composite_score",
    "visual_match",
    "feasibility",
    "logistics",
    "cost_fit",
    "permit_ease",
    "evidence_confidence",
    "rationale",
  ];
  const escapeCsv = (val: unknown) =>
    `"${String(val ?? "").replaceAll('"', '""')}"`;

  const rows = [headers.join(",")];
  for (const scene of plan.scenes) {
    if (scene.top_candidates.length === 0) {
      rows.push(
        [
          scene.scene_number,
          escapeCsv(scene.location),
          escapeCsv(scene.recommended),
          "",
          "",
          "",
          "",
          "",
          "",
          "",
          "",
          "",
          "",
          escapeCsv(scene.rationale),
        ].join(","),
      );
      continue;
    }
    scene.top_candidates.forEach((sc, idx) => {
      rows.push(
        [
          scene.scene_number,
          escapeCsv(scene.location),
          escapeCsv(scene.recommended),
          idx + 1,
          escapeCsv(sc.candidate.name),
          escapeCsv(sc.candidate.address_or_area),
          sc.composite_score.toFixed(1),
          sc.score.visual_match,
          sc.score.feasibility,
          sc.score.logistics,
          sc.score.cost_fit,
          sc.score.permit_ease,
          sc.score.evidence_confidence,
          escapeCsv(scene.rationale),
        ].join(","),
      );
    });
  }
  downloadBlob(
    rows.join("\n"),
    `${slug}-shoot-plan.csv`,
    "text/csv;charset=utf-8",
  );
}

export function Dashboard({
  plan,
  agentReport,
  onPlanRefresh,
  onNewScout,
}: {
  plan: ShootPlan;
  agentReport?: StudioScoutReport | null;
  onPlanRefresh?: () => void;
  onNewScout?: () => void;
}) {
  const [selectedScene, setSelectedScene] = useState<number | null>(
    plan.scenes[0]?.scene_number ?? null,
  );
  const [filter, setFilter] = useState<SceneFilter>("all");
  const [searchQuery, setSearchQuery] = useState("");

  const conflicts = allUniqueConflicts(plan);
  const uniqueLocations = new Set(plan.scenes.map((s) => s.location)).size;

  const topScores = plan.scenes
    .map((s) => s.top_candidates[0]?.composite_score)
    .filter((v): v is number => typeof v === "number");
  const avgScore =
    topScores.length > 0
      ? (topScores.reduce((a, b) => a + b, 0) / topScores.length).toFixed(1)
      : "—";

  const filteredScenes = plan.scenes.filter((s) => {
    const matchesSearch =
      !searchQuery.trim() ||
      s.location.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (s.recommended ?? "").toLowerCase().includes(searchQuery.toLowerCase());
    if (!matchesSearch) return false;
    if (filter === "manual") return needsManualSourcing(s);
    if (filter === "flagged") return s.conflicts.length > 0;
    if (filter === "ready")
      return !needsManualSourcing(s) && s.conflicts.length === 0;
    return true;
  });

  const scene =
    plan.scenes.find((s) => s.scene_number === selectedScene) ??
    filteredScenes[0] ??
    null;

  const currentIndex = scene
    ? plan.scenes.findIndex((s) => s.scene_number === scene.scene_number)
    : -1;
  const prevScene = currentIndex > 0 ? plan.scenes[currentIndex - 1] : null;
  const nextScene =
    currentIndex >= 0 && currentIndex < plan.scenes.length - 1
      ? plan.scenes[currentIndex + 1]
      : null;

  return (
    <main
      id="overview"
      className="mx-auto max-w-6xl px-5 py-10 sm:px-8 lg:py-14"
    >
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4 border-b border-(--color-line) pb-6">
        <div>
          <p className="section-kicker">03 / Scouting Dossier</p>
          <h1 className="mt-2 font-display text-4xl text-(--color-paper) sm:text-5xl">
            {plan.title}
          </h1>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => exportPlanAsCsv(plan)}
            className="rounded-sm bg-(--color-amber) px-3.5 py-2 font-mono text-[10px] font-medium uppercase tracking-widest text-(--color-ink) transition-colors hover:bg-(--color-paper)"
          >
            Export CSV ↓
          </button>
          <button
            type="button"
            onClick={() => exportPlanAsJson(plan)}
            className="rounded-sm border border-(--color-line) bg-(--color-surface) px-3.5 py-2 font-mono text-[10px] uppercase tracking-widest text-(--color-paper) transition-colors hover:border-(--color-amber) hover:text-(--color-amber)"
          >
            Export JSON ↓
          </button>
          {onPlanRefresh && (
            <button
              type="button"
              onClick={onPlanRefresh}
              className="rounded-sm border border-(--color-line) px-3 py-2 font-mono text-[10px] uppercase tracking-widest text-(--color-paper) transition-colors hover:border-(--color-amber) hover:text-(--color-amber)"
            >
              Refresh Plan
            </button>
          )}
          {onNewScout && (
            <button
              type="button"
              onClick={onNewScout}
              className="rounded-sm border border-(--color-line) px-3 py-2 font-mono text-[10px] uppercase tracking-widest text-(--color-meta) transition-colors hover:border-(--color-paper) hover:text-(--color-paper)"
            >
              Upload Another PDF
            </button>
          )}
        </div>
      </div>

      {/* 4-COLUMN TELEMETRY STRIP */}
      <div className="mb-8 grid gap-px border border-(--color-line) bg-(--color-line) sm:grid-cols-2 lg:grid-cols-4">
        <div className="bg-(--color-surface) p-4">
          <span className="font-mono text-[10px] uppercase tracking-widest text-(--color-meta)">
            Total Scenes
          </span>
          <strong className="mt-2 block font-display text-3xl text-(--color-paper)">
            {plan.scenes.length}
          </strong>
        </div>
        <div className="bg-(--color-surface) p-4">
          <span className="font-mono text-[10px] uppercase tracking-widest text-(--color-meta)">
            Unique Sets / Locations
          </span>
          <strong className="mt-2 block font-display text-3xl text-(--color-paper)">
            {uniqueLocations}
          </strong>
        </div>
        <div className="bg-(--color-surface) p-4">
          <span className="font-mono text-[10px] uppercase tracking-widest text-(--color-meta)">
            Avg Top Composite
          </span>
          <strong className="mt-2 block font-display text-3xl text-(--color-amber)">
            {avgScore}
          </strong>
        </div>
        <div className="bg-(--color-surface) p-4">
          <span className="font-mono text-[10px] uppercase tracking-widest text-(--color-meta)">
            Risk Register Flags
          </span>
          <strong className="mt-2 block font-display text-3xl text-(--color-paper)">
            {conflicts.length}
          </strong>
        </div>
      </div>

      {agentReport ? (
        <section className="mb-8 border border-(--color-amber)/50 bg-(--color-surface)/70 p-5">
          <div className="mb-3 flex flex-wrap items-baseline justify-between gap-3">
            <p className="font-mono text-xs uppercase tracking-widest text-(--color-amber)">
              Executive Agent Synthesis
            </p>
            <span className="rounded-sm border border-(--color-line) px-2 py-0.5 font-mono text-[11px] text-(--color-meta)">
              Region: {agentReport.region_used} ·{" "}
              {agentReport.region_source.replaceAll("_", " ")}
            </span>
          </div>
          <p className="max-w-4xl text-sm leading-6 text-[var(--color-paper)]/90">
            {agentReport.overall_summary}
          </p>
        </section>
      ) : (
        plan.shoot_plan_notes && (
          <section className="mb-8 border border-(--color-line) bg-(--color-surface)/60 p-5">
            <p className="mb-2 font-mono text-xs uppercase tracking-widest text-(--color-amber)">
              Production Shoot Plan Notes
            </p>
            <p className="max-w-4xl text-sm leading-6 text-[var(--color-paper)]/85">
              {plan.shoot_plan_notes}
            </p>
          </section>
        )
      )}

      <section className="mb-10">
        <div className="mb-3 flex items-baseline justify-between">
          <p className="section-kicker">Cross-Scene Risk Register</p>
          <span className="font-mono text-[10px] uppercase text-(--color-meta)">
            {conflicts.length} flagged across production
          </span>
        </div>
        <ConflictsPanel conflicts={conflicts} />
      </section>

      {/* CONTACT SHEET FILTER & SEARCH BAR */}
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="mr-2 section-kicker">Scene Contact Sheet</span>
          {(
            [
              ["all", `All (${plan.scenes.length})`],
              ["ready", "Ready"],
              ["flagged", "Flagged"],
              ["manual", "Manual Sourcing"],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              type="button"
              onClick={() => setFilter(key)}
              className={`rounded-sm border px-2.5 py-1 font-mono text-[10px] uppercase tracking-wider transition-colors ${
                filter === key
                  ? "border-(--color-amber) bg-(--color-amber)/15 text-(--color-amber)"
                  : "border-(--color-line) text-(--color-meta) hover:text-(--color-paper)"
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        <input
          type="search"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Filter by scene or venue..."
          className="w-full rounded-sm border border-(--color-line) bg-(--color-surface) px-3 py-1.5 font-mono text-xs text-(--color-paper) outline-none placeholder:text-(--color-meta) focus:border-(--color-amber) sm:w-60"
        />
      </div>

      <ContactSheet
        scenes={filteredScenes}
        selectedScene={scene?.scene_number ?? null}
        onSelect={setSelectedScene}
      />

      {scene && (
        <section className="mt-10 border-t border-(--color-line) pt-8">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-baseline gap-3">
              <span className="rounded-sm bg-(--color-amber)/15 px-2 py-0.5 font-mono text-xs text-(--color-amber)">
                SCENE #{String(scene.scene_number).padStart(2, "0")}
              </span>
              <h2 className="font-display text-2xl text-(--color-paper) sm:text-3xl">
                {scene.location}
              </h2>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                disabled={!prevScene}
                onClick={() =>
                  prevScene && setSelectedScene(prevScene.scene_number)
                }
                className="rounded-sm border border-(--color-line) px-2.5 py-1 font-mono text-[10px] uppercase text-(--color-paper) transition-colors hover:border-(--color-amber) disabled:opacity-35"
              >
                ← Prev Scene
              </button>
              <button
                type="button"
                disabled={!nextScene}
                onClick={() =>
                  nextScene && setSelectedScene(nextScene.scene_number)
                }
                className="rounded-sm border border-(--color-line) px-2.5 py-1 font-mono text-[10px] uppercase text-(--color-paper) transition-colors hover:border-(--color-amber) disabled:opacity-35"
              >
                Next Scene →
              </button>
            </div>
          </div>

          {needsManualSourcing(scene) ? (
            <div className="mt-3 rounded-sm border border-[var(--color-flag)] bg-[var(--color-flag)]/5 p-5">
              <p className="mb-1 font-mono text-xs uppercase tracking-widest text-[var(--color-flag)]">
                Needs Manual Physical Scouting
              </p>
              <p className="text-sm text-[var(--color-paper)]">
                No verifiable real-world candidates met the grounding threshold
                for this scene — review the conflict notes below for scouting
                guidance.
              </p>
            </div>
          ) : (
            <>
              <p className="mb-5 max-w-3xl border-l-2 border-(--color-amber) pl-3 text-sm italic text-[var(--color-paper)]/85">
                {scene.rationale}
              </p>
              <div className="grid gap-5 md:grid-cols-2">
                {scene.top_candidates.map((sc, i) => (
                  <CandidateCard
                    key={i}
                    rank={i + 1}
                    scored={sc}
                    isRecommended={sc.candidate.name === scene.recommended}
                  />
                ))}
              </div>
            </>
          )}

          {scene.conflicts.length > 0 && (
            <div className="mt-6">
              <ConflictsPanel conflicts={scene.conflicts} />
            </div>
          )}
        </section>
      )}
    </main>
  );
}
