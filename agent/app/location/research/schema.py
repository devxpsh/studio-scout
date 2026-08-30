from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    source_url: str = Field(..., description="URL the claim is grounded in. Must come from the provided grounded text; never invented.")
    source_title: str = Field(..., description="Title or domain of the source.")
    snippet: str = Field(..., description="Short excerpt explaining why this source supports the candidate.")


class Candidate(BaseModel):
    name: str = Field(..., description="Name of the candidate location.")
    address_or_area: str = Field(..., description="Best-known address, neighborhood, or area.")
    description: str = Field(..., description="Short description of the location and why it fits the scene.")
    evidence: List[Evidence] = Field(default_factory=list, description="Supporting sources for this candidate.")


class SceneCandidates(BaseModel):
    scene_number: int = Field(..., ge=1, description="Matches SceneRequirements.scene_number.")
    location: str = Field(..., description="Carried from SceneRequirements.location.")
    candidates: List[Candidate] = Field(default_factory=list, description="Candidate real-world locations for this scene, ranked best-first.")