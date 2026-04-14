"""Workout generation and management service."""

from __future__ import annotations

import logging
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import GeneratedWorkout, WorkoutTemplate
from app.db.schemas import GeneratedWorkoutResponse

# Add /src to Python path for importing generators
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Change working directory to project root so relative paths work
os.chdir(str(project_root))

from generators.workout_generator import WorkoutGenerator

logger = logging.getLogger(__name__)


class WorkoutService:
    """Service for generating and managing personalized workouts."""

    def __init__(self, db: Session) -> None:
        """Initialize the workout service.

        Args:
            db: SQLAlchemy session for database operations
        """
        self.db = db
        self.generator = WorkoutGenerator()

    def generate_workout(
        self,
        workout_type: str,
        duration_minutes: int,
        user_ftp: int,
        fitness_level: str = "intermediate",
        user_id: str | None = None,
        scaling_type: str | None = None,
    ) -> dict[str, Any]:
        """Generate a personalized workout from a template.

        Args:
            workout_type: Type of workout (e.g., "HIIT", "Zone 2")
            duration_minutes: Duration in minutes
            user_ftp: User's functional threshold power in watts
            fitness_level: Fitness level ("beginner", "intermediate", "advanced")
            user_id: Optional user identifier
            scaling_type: Optional scaling type for the workout

        Returns:
            Dictionary with generated workout data including:
            - workout_id: Database ID of the generated workout
            - workout_type: Type of workout
            - duration_minutes: Duration in minutes
            - power_profile: List of power levels
            - segments: Detailed workout segments
            - ftp: User's FTP used for generation

        Raises:
            ValueError: If template not found or generation fails
        """
        logger.info(
            f"Generating {workout_type} workout: {duration_minutes}m "
            f"(FTP: {user_ftp}W, Level: {fitness_level})"
        )

        # Get template from database
        template = self.db.query(WorkoutTemplate).filter(
            WorkoutTemplate.workout_type == workout_type,
            WorkoutTemplate.duration_minutes == duration_minutes,
        ).first()

        if not template:
            logger.warning(
                f"Template not found: {workout_type} {duration_minutes}m"
            )
            raise ValueError(
                f"No template found for {workout_type} {duration_minutes}m"
            )

        logger.debug(f"Found template: {template.name} (ID: {template.id})")

        try:
            # Generate workout using the generator
            generated_data = self.generator.generate(
                duration=duration_minutes,
                workout_type=workout_type,
                user_ftp=user_ftp,
                fitness_level=fitness_level,
            )

            logger.info(f"Workout generated successfully")

            # Extract power profile from intervals if available
            power_profile = []
            if "intervals" in generated_data:
                for interval in generated_data["intervals"]:
                    power_level = interval.get("power_level", 0)
                    # Convert string power levels like "6/10" to floats
                    if isinstance(power_level, str) and "/" in power_level:
                        parts = power_level.split("/")
                        power_profile.append(float(parts[0]) / float(parts[1]))
                    elif isinstance(power_level, str):
                        try:
                            power_profile.append(float(power_level))
                        except (ValueError, TypeError):
                            power_profile.append(0.0)
                    else:
                        power_profile.append(float(power_level) if power_level else 0.0)

            # Extract segments (intervals with metadata)
            segments = generated_data.get("intervals", [])

            # Save to database
            db_workout = GeneratedWorkout(
                user_id=user_id,
                template_id=template.id,
                workout_type=workout_type,
                duration_minutes=duration_minutes,
                ftp=user_ftp,
                fitness_level=fitness_level,
                scaling_type=scaling_type,
                power_profile=power_profile,
                segments=segments,
                workout_metadata={
                    "validation": generated_data.get("validation"),
                    "title": generated_data.get("title"),
                },
                created_at=datetime.utcnow(),
                generated_at=datetime.utcnow(),
            )

            self.db.add(db_workout)
            self.db.commit()
            self.db.refresh(db_workout)

            logger.info(
                f"Workout saved to database (ID: {db_workout.id})"
            )

            # Return the database object response
            return GeneratedWorkoutResponse.model_validate(db_workout).model_dump()

        except Exception as e:
            self.db.rollback()
            logger.error(f"Workout generation failed: {str(e)}", exc_info=True)
            raise

    def get_workout_by_id(self, workout_id: int) -> GeneratedWorkoutResponse:
        """Retrieve a generated workout by ID.

        Args:
            workout_id: Database ID of the workout

        Returns:
            GeneratedWorkoutResponse with full workout details

        Raises:
            ValueError: If workout not found
        """
        logger.info(f"Retrieving workout ID: {workout_id}")

        workout = self.db.query(GeneratedWorkout).filter(
            GeneratedWorkout.id == workout_id
        ).first()

        if not workout:
            logger.warning(f"Workout not found: {workout_id}")
            raise ValueError(f"Workout not found: {workout_id}")

        logger.debug(f"Found workout: {workout.workout_type}")
        return GeneratedWorkoutResponse.model_validate(workout)

    def get_available_types(self) -> list[str]:
        """Get list of available workout types from templates.

        Returns:
            Sorted list of unique workout types
        """
        logger.info("Fetching available workout types")

        types = self.db.query(WorkoutTemplate.workout_type).distinct().all()
        type_list = sorted(list(set(t[0] for t in types)))

        logger.debug(f"Available types: {type_list}")
        return type_list

    def get_available_durations(self, workout_type: str) -> list[int]:
        """Get available durations for a specific workout type.

        Args:
            workout_type: Type of workout to query

        Returns:
            Sorted list of available durations in minutes

        Raises:
            ValueError: If workout type not found
        """
        logger.info(f"Fetching available durations for: {workout_type}")

        # Verify workout type exists
        type_exists = self.db.query(WorkoutTemplate).filter(
            WorkoutTemplate.workout_type == workout_type
        ).first()

        if not type_exists:
            logger.warning(f"Workout type not found: {workout_type}")
            raise ValueError(f"Workout type not found: {workout_type}")

        # Get all durations for this type
        durations = self.db.query(WorkoutTemplate.duration_minutes).filter(
            WorkoutTemplate.workout_type == workout_type
        ).all()

        duration_list = sorted(list(set(d[0] for d in durations)))

        logger.debug(f"Available durations for {workout_type}: {duration_list}")
        return duration_list

    def get_user_workouts(
        self, user_id: str, limit: int = 10, offset: int = 0
    ) -> dict[str, Any]:
        """Get all workouts for a specific user.

        Args:
            user_id: User identifier
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Dictionary with total count and list of workouts
        """
        logger.info(
            f"Fetching workouts for user: {user_id} (limit={limit}, offset={offset})"
        )

        query = self.db.query(GeneratedWorkout).filter(
            GeneratedWorkout.user_id == user_id
        )

        total = query.count()
        workouts = query.limit(limit).offset(offset).all()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "workouts": [
                GeneratedWorkoutResponse.model_validate(w) for w in workouts
            ],
        }
