// Primary dashboard data contract: mirrors data/recommendations.json (ShootPlan),
// produced by app/location/pipeline.py (Phase 4). This is the file the
// dashboard actually reads — confirmed explicitly in the Phase 4 context doc
// ("This is the file the frontend reads... do not re-invoke the pipeline live
// from the UI"). Field names kept snake_case to match Pydantic's JSON output.

export type ConflictType =
  | "continuity"
  | "budget"
  | "permit"
  | "low_confidence";
export type ConflictSeverity = "info" | "warning" | "blocker";

export interface Evidence {
  source_url: string;
  source_title: string;
  snippet: string;
}

export interface Candidate {
  name: string;
  address_or_area: string;
  description: string;
  evidence: Evidence[]; // can legitimately be [] — don't treat as untrustworthy, check score.evidence_confidence instead
}

export interface ScoreBreakdown {
  visual_match: number; // 0-100, weight 30%
  feasibility: number; // 0-100, weight 25%
  logistics: number; // 0-100, weight 15%
  cost_fit: number; // 0-100, weight 15%
  permit_ease: number; // 0-100, weight 10%
  evidence_confidence: number; // 0-100, weight 5%
}

export interface ScoredCandidate {
  candidate: Candidate;
  score: ScoreBreakdown;
  composite_score: number; // pre-computed weighted total — never recompute in the frontend
}

export interface Conflict {
  type: ConflictType;
  affected_scenes: number[];
  description: string;
  severity: ConflictSeverity;
  suggested_resolution: string;
}

export interface SceneRecommendation {
  scene_number: number;
  location: string;
  top_candidates: ScoredCandidate[]; // up to 5, ranked best-first, can be []
  recommended: string; // matches top_candidates[0].candidate.name, or "none found"
  rationale: string;
  conflicts: Conflict[]; // conflicts affecting only this scene, plus this scene's share of global ones
}

export interface ShootPlan {
  title: string;
  scenes: SceneRecommendation[];
  global_conflicts: Conflict[]; // only conflicts with affected_scenes.length > 1
  shoot_plan_notes: string; // deterministic summary string, e.g. "3 conflicts detected: 1 blocker(s)..."
}

// A scene needing manual attention is NOT "top_candidates === []" checked
// directly — it's reliably detected via a low_confidence/blocker conflict.
// Mirrors the Python-side guarantee described in the Phase 4 doc.
export function needsManualSourcing(scene: SceneRecommendation): boolean {
  return scene.conflicts.some(
    (c) => c.type === "low_confidence" && c.severity === "blocker",
  );
}

// Dedupe global_conflicts against per-scene conflicts by object identity
// (type + affected_scenes + description), since a global conflict also
// appears inside each affected scene's own conflicts array.
export function allUniqueConflicts(plan: ShootPlan): Conflict[] {
  const seen = new Set<string>();
  const result: Conflict[] = [];
  const consider = (c: Conflict) => {
    const key = `${c.type}|${c.affected_scenes.join(",")}|${c.description}`;
    if (!seen.has(key)) {
      seen.add(key);
      result.push(c);
    }
  };
  plan.global_conflicts.forEach(consider);
  plan.scenes.forEach((s) => s.conflicts.forEach(consider));
  return result;
}

// --- Phase 2 screenplay enums (app/screenplay/schema.py) ---
// Not part of ShootPlan itself — SceneRecommendation only carries `location`,
// not slugline/setting/time_of_day. Useful only if the dashboard later
// cross-references data/screenplay.json by scene_number for richer headers.
export type Setting = "interior" | "exterior" | "interior/exterior";
export type TimeOfDay =
  | "dawn"
  | "morning"
  | "day"
  | "afternoon"
  | "sunset"
  | "evening"
  | "night"
  | "continuous"
  | "unknown";

// --- Phase 3 orchestrator output (app/agents/report_schema.py) ---
// Kept for reference — relationship to ShootPlan above is unconfirmed (see
// chat note). Not used by the dashboard build below.
export type RiskLevel = "low" | "medium" | "high" | "unknown";
export type RegionSource = "user_specified" | "inferred_from_screenplay";

export interface EvidenceSource {
  title: string;
  url: string;
}

export interface LocationCandidate {
  name: string;
  sub_region: string | null;
  summary: string;
  evidence: EvidenceSource[];
  risk_level: RiskLevel;
  risk_justification: string;
  logistics_notes: string;
}

export interface SceneReport {
  scene_number: number;
  slugline: string;
  setting: Setting;
  time_of_day: TimeOfDay;
  location_description: string;
  scene_summary: string;
  candidates: LocationCandidate[];
}

export interface StudioScoutReport {
  screenplay_title: string;
  region_used: string;
  region_source: RegionSource;
  overall_summary: string;
  scenes: SceneReport[];
}

// Not part of report_schema.py — a separate conversational branch. Per
// architecture rule 5: the orchestrator may stop and ask the user to
// clarify region instead of guessing.
export interface RegionClarificationRequest {
  question: string;
  suggestedRegions?: string[];
}

// --- Agent trace (live processing view) — unaffected by either schema above ---

export type AgentId =
  | "orchestrator"
  | "script_breakdown"
  | "location_grounding"
  | "logistics_risk";
export type AgentStatus = "pending" | "running" | "done";

export interface TraceEvent {
  id: string;
  agent: AgentId;
  status: AgentStatus;
  message: string;
  timestamp: string;
}

export const AGENT_LABELS: Record<AgentId, string> = {
  orchestrator: "Studio Scout Orchestrator",
  script_breakdown: "Script Breakdown Agent",
  location_grounding: "Location & Permit Grounding",
  logistics_risk: "Logistics & Risk Engine",
};
