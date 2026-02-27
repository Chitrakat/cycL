"""SQLAlchemy database models for cycling workouts."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import declarative_base

from app.db.database import Base


class WorkoutTemplate(Base):
    """Workout template model."""

    __tablename__ = "workout_templates"

    id = Column(Integer, primary_key=True, index=True)
    workout_type = Column(String(50), index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    duration_minutes = Column(Integer, nullable=False)
    ftp_percentage = Column(Float, nullable=False)
    power_profile = Column(JSON, nullable=False)  # List of power levels by interval
    power_by_zone = Column(JSON, nullable=False)  # Power by zone type
    structure = Column(JSON, nullable=False)  # Workout segments
    scaling_factors = Column(JSON, nullable=True)  # Scaling config for HIIT, Zone2, etc.
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        """String representation."""
        return f"<WorkoutTemplate(id={self.id}, workout_type={self.workout_type})>"


class GeneratedWorkout(Base):
    """Generated (personalized) workout model."""

    __tablename__ = "generated_workouts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), index=True, nullable=True)  # Optional user FK
    template_id = Column(Integer, index=True, nullable=False)
    workout_type = Column(String(50), index=True, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    ftp = Column(Integer, nullable=False)  # User's FTP in watts
    fitness_level = Column(String(20), nullable=False)  # beginner, intermediate, advanced
    scaling_type = Column(String(50), nullable=True)  # HIIT, Zone2, SweetSpot, etc.
    power_profile = Column(JSON, nullable=False)  # Personalized power levels
    segments = Column(JSON, nullable=False)  # Workout segments with power/cadence/intensity
    workout_metadata = Column(JSON, nullable=True)  # Additional workout info
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        """String representation."""
        return f"<GeneratedWorkout(id={self.id}, user_id={self.user_id}, workout_type={self.workout_type})>"
