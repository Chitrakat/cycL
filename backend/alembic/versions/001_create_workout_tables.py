"""Create workout tables.

Revision ID: 001
Revises:
Create Date: 2026-02-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create workout_templates and generated_workouts tables."""
    # Create workout_templates table
    op.create_table(
        'workout_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workout_type', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('ftp_percentage', sa.Float(), nullable=False),
        sa.Column('power_profile', sa.JSON(), nullable=False),
        sa.Column('power_by_zone', sa.JSON(), nullable=False),
        sa.Column('structure', sa.JSON(), nullable=False),
        sa.Column('scaling_factors', sa.JSON(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workout_templates_id'), 'workout_templates', ['id'], unique=False)
    op.create_index(op.f('ix_workout_templates_workout_type'), 'workout_templates', ['workout_type'], unique=False)

    # Create generated_workouts table
    op.create_table(
        'generated_workouts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=True),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('workout_type', sa.String(length=50), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('ftp', sa.Integer(), nullable=False),
        sa.Column('fitness_level', sa.String(length=20), nullable=False),
        sa.Column('scaling_type', sa.String(length=50), nullable=True),
        sa.Column('power_profile', sa.JSON(), nullable=False),
        sa.Column('segments', sa.JSON(), nullable=False),
        sa.Column('workout_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_generated_workouts_id'), 'generated_workouts', ['id'], unique=False)
    op.create_index(op.f('ix_generated_workouts_user_id'), 'generated_workouts', ['user_id'], unique=False)
    op.create_index(op.f('ix_generated_workouts_template_id'), 'generated_workouts', ['template_id'], unique=False)
    op.create_index(op.f('ix_generated_workouts_workout_type'), 'generated_workouts', ['workout_type'], unique=False)


def downgrade() -> None:
    """Drop workout_templates and generated_workouts tables."""
    op.drop_index(op.f('ix_generated_workouts_workout_type'), table_name='generated_workouts')
    op.drop_index(op.f('ix_generated_workouts_template_id'), table_name='generated_workouts')
    op.drop_index(op.f('ix_generated_workouts_user_id'), table_name='generated_workouts')
    op.drop_index(op.f('ix_generated_workouts_id'), table_name='generated_workouts')
    op.drop_table('generated_workouts')
    
    op.drop_index(op.f('ix_workout_templates_workout_type'), table_name='workout_templates')
    op.drop_index(op.f('ix_workout_templates_id'), table_name='workout_templates')
    op.drop_table('workout_templates')
