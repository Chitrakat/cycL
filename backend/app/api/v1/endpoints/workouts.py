"""Workout API endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.schemas import (
    GeneratedWorkoutCreate,
    GeneratedWorkoutResponse,
)
from app.services.workout_service import WorkoutService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.post("/generate", response_model=GeneratedWorkoutResponse, status_code=201)
async def generate_workout(
    request: GeneratedWorkoutCreate,
    db: Session = Depends(get_db),
) -> GeneratedWorkoutResponse:
    """Generate a personalized workout from a template.

    Args:
        request: GeneratedWorkoutCreate with:
            - template_id: ID of the template to use
            - ftp: User's functional threshold power (50-500 watts)
            - fitness_level: "beginner", "intermediate", or "advanced"
            - scaling_type: Optional scaling type
            - user_id: Optional user identifier
        db: Database session

    Returns:
        Generated workout with full interval details (201 Created)

    Raises:
        HTTPException 422: Invalid input parameters
        HTTPException 404: Template not found
        HTTPException 500: Generation failed
    """
    logger.info(f"POST /generate - Generating workout from template {request.template_id}")

    try:
        service = WorkoutService(db)

        # Generate workout
        result = service.generate_workout(
            template_id=request.template_id,
            duration_minutes=request.duration_minutes,
            user_ftp=request.ftp,
            fitness_level=request.fitness_level,
            user_id=request.user_id,
            scaling_type=request.scaling_type,
        )

        logger.info(f"Workout generated successfully: {result['id']}")
        return GeneratedWorkoutResponse(**result)

    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Generation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to generate workout"
        )


@router.get("/templates", status_code=200)
async def list_templates(
    workout_type: str | None = Query(None, description="Optional workout type filter"),
    duration_minutes: int | None = Query(None, description="Optional duration filter"),
    limit: int = Query(100, ge=1, le=500, description="Max templates to return"),
    db: Session = Depends(get_db),
) -> dict[str, list[dict[str, Any]]]:
    """List available templates for frontend selection."""
    logger.info(
        f"GET /templates - workout_type={workout_type} duration_minutes={duration_minutes}"
    )

    try:
        service = WorkoutService(db)
        templates = service.get_templates(
            workout_type=workout_type,
            duration_minutes=duration_minutes,
            limit=limit,
        )
        return {"templates": templates}
    except Exception as e:
        logger.error(f"Failed to list templates: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch templates")


@router.get("/templates/report", status_code=200)
async def template_quality_report(
    workout_type: str | None = Query(None, description="Optional workout type filter"),
    limit: int = Query(200, ge=1, le=1000, description="Max templates to evaluate"),
    include_templates: bool = Query(True, description="Include per-template detail"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return template quality report for scaling and duration-fit checks."""
    logger.info(
        f"GET /templates/report - workout_type={workout_type} limit={limit}"
    )

    try:
        service = WorkoutService(db)
        return service.get_template_quality_report(
            workout_type=workout_type,
            limit=limit,
            include_templates=include_templates,
        )
    except Exception as e:
        logger.error(f"Failed to build template report: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to build template report")


@router.get("/types", status_code=200)
async def get_workout_types(
    db: Session = Depends(get_db),
) -> dict[str, list[str]]:
    """Get all available workout types.

    Args:
        db: Database session

    Returns:
        Dictionary with list of workout types

    Example:
        {
            "types": ["HIIT", "Power", "Sweet Spot", "VO2max", "Zone 2"]
        }
    """
    logger.info("GET /types - Fetching available workout types")

    try:
        service = WorkoutService(db)
        types = service.get_available_types()
        logger.debug(f"Returning {len(types)} workout types")
        return {"types": types}
    except Exception as e:
        logger.error(f"Failed to fetch types: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to fetch workout types"
        )


@router.get("/durations", status_code=200)
async def get_workout_durations(
    workout_type: str = Query(..., description="Workout type"),
    db: Session = Depends(get_db),
) -> dict[str, list[int]]:
    """Get available durations for a specific workout type.

    Args:
        workout_type: Type of workout (required, query param)
        db: Database session

    Returns:
        Dictionary with list of available durations in minutes

    Raises:
        HTTPException 404: Workout type not found

    Example:
        GET /durations?workout_type=HIIT
        {
            "durations": [20, 25, 30, 40, 45, 50]
        }
    """
    logger.info(f"GET /durations - Fetching durations for {workout_type}")

    try:
        service = WorkoutService(db)
        durations = service.get_available_durations(workout_type)
        logger.debug(f"Found {len(durations)} durations for {workout_type}")
        return {"durations": durations}
    except ValueError as e:
        logger.warning(f"Workout type not found: {workout_type}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to fetch durations: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to fetch durations"
        )


@router.get("/{workout_id}", response_model=GeneratedWorkoutResponse, status_code=200)
async def get_workout(
    workout_id: int,
    db: Session = Depends(get_db),
) -> GeneratedWorkoutResponse:
    """Retrieve a generated workout by ID.

    Args:
        workout_id: Database ID of the workout
        db: Database session

    Returns:
        Full generated workout with all segments and power profile

    Raises:
        HTTPException 404: Workout not found
        HTTPException 500: Database error

    Example:
        GET /123
        {
            "id": 123,
            "workout_type": "HIIT",
            "duration_minutes": 30,
            "ftp": 250,
            "fitness_level": "intermediate",
            "power_profile": [0.5, 0.6, 0.8, ...],
            "segments": [...]
        }
    """
    logger.info(f"GET /{workout_id} - Fetching workout")

    try:
        service = WorkoutService(db)
        workout = service.get_workout_by_id(workout_id)
        logger.debug(f"Returning workout: {workout.id}")
        return workout
    except ValueError as e:
        logger.warning(f"Workout not found: {workout_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to fetch workout: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to fetch workout"
        )
