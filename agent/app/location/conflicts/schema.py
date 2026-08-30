from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class ConflictType(str, Enum):
    CONTINUITY = "continuity"
    BUDGET = "budget"
    PERMIT = "permit"
    LOW_CONFIDENCE = "low_confidence"


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    BLOCKER = "blocker"


class Conflict(BaseModel):
    type: ConflictType
    affected_scenes: List[int] = Field(..., description="scene_number values affected by this conflict.")
    description: str = Field(..., description="Human-readable explanation of the conflict.")
    severity: Severity
    suggested_resolution: str = Field(..., description="Short suggestion for how to resolve or investigate this conflict.")