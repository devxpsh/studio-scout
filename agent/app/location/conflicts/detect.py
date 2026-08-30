from __future__ import annotations

from collections import defaultdict

from app.location.requirements.schema import ScreenplayRequirements
from app.location.conflicts.schema import Conflict, ConflictType, Severity
from app.location.scoring.schema import SceneScores

LOW_CONFIDENCE_THRESHOLD = 50
LOW_PERMIT_EASE_THRESHOLD = 40
HIGH_BUDGET_CONCENTRATION_RATIO = 0.4


def detect_low_confidence(scene_scores: list[SceneScores]) -> list[Conflict]:
    conflicts = []
    for scene in scene_scores:
        if not scene.scored_candidates:
            conflicts.append(Conflict(
                type=ConflictType.LOW_CONFIDENCE,
                affected_scenes=[scene.scene_number],
                description=f"No candidates found for '{scene.location}'.",
                severity=Severity.BLOCKER,
                suggested_resolution="Broaden the search query or manually source a location for this scene.",
            ))
        elif scene.scored_candidates[0].composite_score < LOW_CONFIDENCE_THRESHOLD:
            conflicts.append(Conflict(
                type=ConflictType.LOW_CONFIDENCE,
                affected_scenes=[scene.scene_number],
                description=f"Best candidate for '{scene.location}' scored below {LOW_CONFIDENCE_THRESHOLD}.",
                severity=Severity.WARNING,
                suggested_resolution="Review candidates manually; consider a wider search region.",
            ))
    return conflicts


def detect_continuity(requirements: ScreenplayRequirements, scene_scores: list[SceneScores]) -> list[Conflict]:
    by_location: dict[str, list[SceneScores]] = defaultdict(list)
    for scene in scene_scores:
        by_location[scene.location].append(scene)

    conflicts = []
    for location, scenes in by_location.items():
        if len(scenes) < 2:
            continue
        top_names = {
            scene.scored_candidates[0].candidate.name
            for scene in scenes
            if scene.scored_candidates
        }
        if len(top_names) > 1:
            conflicts.append(Conflict(
                type=ConflictType.CONTINUITY,
                affected_scenes=[s.scene_number for s in scenes],
                description=f"Scenes sharing location '{location}' have different top-ranked candidates: {', '.join(top_names)}.",
                severity=Severity.WARNING,
                suggested_resolution="Pick one candidate for all scenes at this location to preserve continuity.",
            ))
    return conflicts


def detect_permit(scene_scores: list[SceneScores]) -> list[Conflict]:
    conflicts = []
    for scene in scene_scores:
        if not scene.scored_candidates:
            continue
        top = scene.scored_candidates[0]
        if top.score.permit_ease < LOW_PERMIT_EASE_THRESHOLD:
            conflicts.append(Conflict(
                type=ConflictType.PERMIT,
                affected_scenes=[scene.scene_number],
                description=f"Top candidate for '{scene.location}' has low permit ease ({top.score.permit_ease}).",
                severity=Severity.WARNING,
                suggested_resolution="Start permit inquiries early or evaluate the next-ranked candidate.",
            ))
    return conflicts


def detect_budget(scene_scores: list[SceneScores]) -> list[Conflict]:
    scenes_with_top = [s for s in scene_scores if s.scored_candidates]
    if not scenes_with_top:
        return []

    low_cost_fit_count = sum(
        1 for s in scenes_with_top if s.scored_candidates[0].score.cost_fit < LOW_PERMIT_EASE_THRESHOLD
    )
    ratio = low_cost_fit_count / len(scenes_with_top)

    if ratio >= HIGH_BUDGET_CONCENTRATION_RATIO:
        affected = [s.scene_number for s in scenes_with_top if s.scored_candidates[0].score.cost_fit < LOW_PERMIT_EASE_THRESHOLD]
        return [Conflict(
            type=ConflictType.BUDGET,
            affected_scenes=affected,
            description=f"{low_cost_fit_count}/{len(scenes_with_top)} scenes have top candidates with poor cost fit.",
            severity=Severity.WARNING,
            suggested_resolution="Review overall budget assumptions or reconsider candidates for these scenes.",
        )]
    return []


def detect_conflicts(requirements: ScreenplayRequirements, scene_scores: list[SceneScores]) -> list[Conflict]:
    conflicts = []
    conflicts.extend(detect_low_confidence(scene_scores))
    conflicts.extend(detect_continuity(requirements, scene_scores))
    conflicts.extend(detect_permit(scene_scores))
    conflicts.extend(detect_budget(scene_scores))
    return conflicts