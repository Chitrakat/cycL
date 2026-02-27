"""Seed workout templates into the database.

This script loads workout templates from the JSON file into the PostgreSQL database.
Run this after running `alembic upgrade head` to create the database tables.

Usage:
    python -m app.scripts.seed_templates
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import SessionLocal, engine
from app.db.models import WorkoutTemplate


def load_templates_from_json(file_path: str) -> list[dict]:
    """Load templates from JSON file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Templates file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    templates = []
    
    # Handle dict structure: {workout_type: {duration: {...}, ...}, ...}
    if isinstance(data, dict) and 'templates' in data:
        templates_data = data['templates']
    elif isinstance(data, list):
        return data
    else:
        templates_data = data
    
    # Flatten the nested structure
    if isinstance(templates_data, dict):
        for workout_type, durations in templates_data.items():
            if isinstance(durations, dict):  # {duration: {...}, ...}
                for duration, template_data in durations.items():
                    if isinstance(template_data, dict):
                        # Ensure workout_type is set in the template data
                        if 'workout_type' not in template_data:
                            template_data['workout_type'] = workout_type
                        templates.append(template_data)
            else:
                # If it's not a dict, it might be a direct template
                if isinstance(durations, dict):
                    if 'workout_type' not in durations:
                        durations['workout_type'] = workout_type
                    templates.append(durations)
    elif isinstance(templates_data, list):
        return templates_data
    else:
        raise ValueError("Invalid template file format")
    
    return templates


def seed_templates() -> None:
    """Seed workout templates into the database."""
    # Determine the path to workout_templates.json
    # It should be at ../../data/templates/workout_templates.json from this file
    script_dir = Path(__file__).parent
    template_file = script_dir.parent.parent.parent / "data" / "templates" / "workout_templates.json"
    
    print(f"Loading templates from: {template_file}")
    
    try:
        templates_data = load_templates_from_json(str(template_file))
    except (FileNotFoundError, ValueError) as e:
        print(f"Error loading templates: {e}")
        sys.exit(1)
    
    # Connect to database
    db: Session = SessionLocal()
    
    try:
        # Count existing templates
        existing_count = db.query(WorkoutTemplate).count()
        print(f"Found {existing_count} existing templates in database")
        
        if existing_count > 0:
            print("Database already seeded. Skipping.")
            return
        
        # Seed templates
        now = datetime.utcnow()
        added_count = 0
        
        for template_data in templates_data:
            workout_type = template_data.get('workout_type', 'Unknown')
            duration = template_data.get('duration_minutes', 60)
            
            # Check if template already exists (using both type and duration)
            existing = db.query(WorkoutTemplate).filter(
                WorkoutTemplate.workout_type == workout_type,
                WorkoutTemplate.duration_minutes == duration
            ).first()
            
            if existing:
                print(f"  Skipping {workout_type} {duration}m (already exists)")
                continue
            
            # Generate name if not provided
            name = template_data.get('name') or f"{workout_type} {duration}m"
            
            # Create template object
            template = WorkoutTemplate(
                workout_type=workout_type,
                name=name,
                description=template_data.get('description'),
                duration_minutes=duration,
                ftp_percentage=template_data.get('ftp_percentage', 1.0),
                power_profile=template_data.get('power_profile', []),
                power_by_zone=template_data.get('power_by_zone', {}),
                structure=template_data.get('structure', []),
                scaling_factors=template_data.get('scaling_factors'),
                version=template_data.get('version', 2),
                created_at=now,
                updated_at=now,
            )
            
            db.add(template)
            added_count += 1
            print(f"  Added {template.workout_type} {duration}m")
        
        # Commit all templates
        if added_count > 0:
            db.commit()
            print(f"\nSuccessfully seeded {added_count} templates")
        else:
            print("No new templates to add")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding templates: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed_templates()
