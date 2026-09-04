from __future__ import annotations
from pydantic import BaseModel, Field, field_validator

from enum import Enum
from typing import List

from pydantic import BaseModel, Field

class Setting(str, Enum):
    INTERIOR = "interior"
    EXTERIOR = "exterior"
    INTERIOR_EXTERIOR = "interior/exterior"


class TimeOfDay(str, Enum):
    DAWN = "dawn"
    MORNING = "morning"
    DAY = "day"
    AFTERNOON = "afternoon"
    SUNSET = "sunset"
    EVENING = "evening"
    NIGHT = "night"
    CONTINUOUS = "continuous"
    UNKNOWN = "unknown"


class DialogueLine(BaseModel):
    character: str = Field(..., description="Character name as it appears in the scene, lowercased.")
    text: str = Field(..., description="The spoken dialogue line.")


class Scene(BaseModel):
    scene_number: int = Field(..., ge=1, description="1-indexed order of the scene in the screenplay.")
    slugline: str = Field(..., description="Raw slugline as written, e.g. 'EXT. MUMBAI STREET - NIGHT'.")
    setting: Setting = Field(..., description="Interior, exterior, or both.")
    location: str = Field(..., description="Normalized location name extracted from the slugline.")
    time_of_day: TimeOfDay = Field(..., description="Normalized time-of-day extracted from the slugline.")
    @field_validator("time_of_day", mode="before")
    @classmethod
    def _coerce_time_of_day(cls, v):
        valid = {m.value for m in TimeOfDay}
        return v if v in valid else TimeOfDay.UNKNOWN
    description: str = Field(..., description="Scene action/description text (non-dialogue prose).")
    characters: List[str] = Field(default_factory=list, description="Characters present in the scene, lowercased.")
    dialogue: List[DialogueLine] = Field(default_factory=list, description="Ordered dialogue lines in the scene.")



class ScreenPlay(BaseModel):
    title: str = Field(..., description="Title of the screenplay.")
    scenes: List[Scene] = Field(..., description="Ordered list of scenes, matching scene_number order.")

    def scene_count(self) -> int:
        return len(self.scenes)

    def locations(self) -> List[str]:
        """Unique locations across the screenplay, in first-appearance order."""
        seen: List[str] = []
        for scene in self.scenes:
            if scene.location not in seen:
                seen.append(scene.location)
        return seen



if __name__ == "__main__":
    sample = ScreenPlay(
        title="Sample Fixture",
        scenes=[
            Scene(
                scene_number=1,
                slugline="EXT. OLD RAILWAY STATION - DAWN",
                setting=Setting.EXTERIOR,
                location="old railway station",
                time_of_day=TimeOfDay.DAWN,
                description="A lone figure waits on an empty platform as fog rolls in.",
                characters=["arjun"],
                dialogue=[DialogueLine(character="arjun", text="...")],
            )
        ],
    )
    print(sample.model_dump_json(indent=2))
    print("scene_count:", sample.scene_count())
    print("locations:", sample.locations())