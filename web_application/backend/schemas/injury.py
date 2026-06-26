from pydantic import BaseModel, Field
from typing import List, Optional


class InjuryRequest(BaseModel):
    video_path: str = Field(..., description="Absolute local path to the exercise video file")
    exercise: str = Field(..., description="Exercise name from the classify endpoint")


class PhaseFeedback(BaseModel):
    phase: str
    injury_prone_frame_count: int
    violated_rules: str
    severity: str
    summary: str
    feedback: str
    cue: str
    source: str
    frame_image_url: Optional[str] = None


class InjuryResponse(BaseModel):
    exercise: str
    supported: bool
    total_frames: int
    valid_frames: int
    steady_phase_frames: int
    injury_prone_frames: int
    overall_severity: Optional[str]
    feedback: List[PhaseFeedback]
