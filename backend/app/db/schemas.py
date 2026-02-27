"""Pydantic schemas for API request/response validation."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class WorkoutSegment(BaseModel):
    """Segment within a workout."""

    zone: str | None = None
    duration: int  # seconds
    power_level: float | None = None
    cadence: int | None = None
    intensity: str | None = None

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "zone": "Zone2",
                "duration": 300,
                "power_level": 250,
                "cadence": 90,
                "intensity": "moderate",
            }
        }


class PowerByZone(BaseModel):
    """Power levels by zone type."""

    warmup: float | None = None
    main_set: float | None = None
    recovery: float | None = None
    cooldown: float | None = None


class ScalingFactors(BaseModel):
    """Workout scaling configuration."""

    hiit: dict[str, Any] | None = None
    zone2: dict[str, Any] | None = None
    sweetspot: dict[str, Any] | None = None
    vo2max: dict[str, Any] | None = None
    power: dict[str, Any] | None = None
    cadence: dict[str, Any] | None = None


class WorkoutTemplateCreate(BaseModel):
    """Request schema for creating a workout template."""

    workout_type: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    duration_minutes: int = Field(..., gt=0)
    ftp_percentage: float = Field(..., gt=0, le=100)
    power_profile: list[float] = Field(..., min_length=1)
    power_by_zone: dict[str, float | None] = Field(...)
    structure: list[dict[str, Any]] = Field(..., min_length=1)
    scaling_factors: dict[str, Any] | None = None

    @field_validator("workout_type")
    @classmethod
    def validate_workout_type(cls, v: str) -> str:
        """Validate workout type format."""
        if not v.replace("_", "").isalnum():
            raise ValueError("Workout type must contain only alphanumeric characters and underscores")
        return v.lower()

    @field_validator("ftp_percentage")
    @classmethod
    def validate_ftp_percentage(cls, v: float) -> float:
        """Validate FTP percentage."""
        if not (0 < v <= 100):
            raise ValueError("FTP percentage must be between 0 and 100")
        return v


class WorkoutTemplateResponse(WorkoutTemplateCreate):
    """Response schema for workout templates."""

    id: int
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class GeneratedWorkoutCreate(BaseModel):
    """Request schema for generating a personalized workout."""

    template_id: int = Field(..., gt=0)
    ftp: int = Field(..., gt=0, le=500)  # User's FTP in watts
    fitness_level: str = Field("intermediate", pattern="^(beginner|intermediate|advanced)$")
    scaling_type: str | None = None
    user_id: str | None = None

    @field_validator("ftp")
    @classmethod
    def validate_ftp(cls, v: int) -> int:
        """Validate FTP value."""
        if not (50 <= v <= 500):
            raise ValueError("FTP must be between 50 and 500 watts")
        return v


class GeneratedWorkoutResponse(BaseModel):
    """Response schema for generated workouts."""

    id: int
    user_id: str | None
    template_id: int
    workout_type: str
    duration_minutes: int
    ftp: int
    fitness_level: str
    scaling_type: str | None
    power_profile: list[float]
    segments: list[dict[str, Any]]
    workout_metadata: dict[str, Any] | None
    created_at: datetime
    generated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class TemplateListResponse(BaseModel):
    """Response for listing templates."""

    total: int
    templates: list[WorkoutTemplateResponse]


class WorkoutListResponse(BaseModel):
    """Response for listing generated workouts."""

    total: int
    limit: int
    offset: int
    workouts: list[GeneratedWorkoutResponse]
