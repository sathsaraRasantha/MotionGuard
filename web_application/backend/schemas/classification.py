from pydantic import BaseModel, Field
from typing import Dict


class ClassifyRequest(BaseModel):
    video_path: str = Field(..., description="Absolute local path to the exercise video file")


class ClassifyResponse(BaseModel):
    exercise: str
    confidence: float
    total_frames: int
    valid_frames: int
    votes: Dict[str, int]
