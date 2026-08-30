from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from app.screenplay.schema import Setting, TimeOfDay


class CrewFootprint(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class BudgetTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class PermitSensitivity(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    UNKNOWN = "unknown"


class SceneRequirements(BaseModel):
    scene_number: int = Field(..., ge=1, description="Matches Scene.scene_number.")
    location: str = Field(..., description="Carried from Scene.location.")
    setting: Setting = Field(..., description="Carried from Scene.setting.")
    time_of_day: TimeOfDay = Field(..., description="Carried from Scene.time_of_day.")
    visual_descriptors: List[str] = Field(default_factory=list, description="Short phrases describing what the location should look like, drawn from the scene description.")
    mood_tone: str = Field(..., description="One or two words capturing the emotional tone of the scene.")
    required_features: List[str] = Field(default_factory=list, description="Concrete physical elements the location must support.")
    cast_size: int = Field(..., ge=0, description="Number of distinct characters present in the scene.")
    crew_footprint: CrewFootprint = Field(..., description="Estimated crew/equipment footprint.")
    budget_tier: BudgetTier = Field(..., description="Inferred budget sensitivity for this scene's location.")
    permit_sensitivity: PermitSensitivity = Field(..., description="Public vs private property, affecting permit friction.")


class ScreenplayRequirements(BaseModel):
    title: str = Field(..., description="Matches ScreenPlay.title.")
    scenes: List[SceneRequirements] = Field(..., description="Ordered list of per-scene requirements, matching scene_number order.")

    def get(self, scene_number: int) -> Optional[SceneRequirements]:
        for scene in self.scenes:
            if scene.scene_number == scene_number:
                return scene
        return None