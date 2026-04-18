"""
Pydantic schemas for Smart Bin API.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ClassifyResponse(BaseModel):
    """Response from /classify endpoint."""
    waste_type: str
    confidence: float
    angle: int
    servo_success: bool
    image_path: str
    light_level: float
    all_scores: dict = Field(default_factory=dict)


class AutoClassifyRequest(BaseModel):
    """Request for /classify/auto endpoint."""
    distance_cm: float = Field(..., gt=0, description="Distance from sensor in cm")


class CaptureRequest(BaseModel):
    """Request for /capture endpoint."""
    image_b64: str = Field(..., description="Base64-encoded JPEG image")
    predicted: str = Field(..., description="Predicted waste type")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence")


class CaptureResponse(BaseModel):
    """Response from /capture endpoint."""
    image_path: str
    csv_row: int
    light_level: float


class LabelEntry(BaseModel):
    """Single label entry from labels.csv."""
    row_id: int
    img_path: str
    predicted_class: str
    user_label: str
    confidence: float
    timestamp: str
    angle: int
    light_level: float


class LabelsResponse(BaseModel):
    """Response from /labels endpoint."""
    labels: list[LabelEntry]
    total_count: int


class UpdateLabelRequest(BaseModel):
    """Request for PATCH /labels/{row_id}."""
    user_label: str = Field(..., min_length=1, description="Ground truth label")
