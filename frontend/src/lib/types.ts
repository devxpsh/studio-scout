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
  evidence: Evidence[];
}

export interface ScoreBreakdown {
  visual_match: number;
  feasibility: number;
  logistics: number;
  cost_fit: number;
  permit_ease: number;
  evidence_confidence: number;
}

export interface ScoredCandidate {
  candidate: Candidate;
  score: ScoreBreakdown;
  composite_score: number;
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
  top_candidates: ScoredCandidate[];
  recommended: string;
  rationale: string;
  conflicts: Conflict[];
}

export interface ShootPlan {
  title: string;
  scenes: SceneRecommendation[];
  global_conflicts: Conflict[];
  shoot_plan_notes: string;
}

export function needsManualSourcing(scene: SceneRecommendation): boolean {
  return scene.conflicts.some(
    (c) => c.type === "low_confidence" && c.severity === "blocker",
  );
}

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

export interface RegionClarificationRequest {
  question: string;
  suggestedRegions?: string[];
}

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
