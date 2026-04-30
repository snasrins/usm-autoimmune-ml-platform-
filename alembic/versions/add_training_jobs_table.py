"""Add training_jobs table for persistent storage

Revision ID: add_training_jobs_table
Revises: 9a2e81360415
Create Date: 2026-04-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_training_jobs_table'
down_revision: Union[str, None] = '9a2e81360415'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create training_jobs table for persistent ML training job storage"""
    
    # Create job_type enum
    op.execute("""
        CREATE TYPE jobtype AS ENUM (
            'dataset_generation',
            'feature_selection',
            'base_model',
            'ensemble',
            'full_pipeline'
        )
    """)
    
    # Create job_status enum
    op.execute("""
        CREATE TYPE jobstatus AS ENUM (
            'pending',
            'running',
            'completed',
            'failed'
        )
    """)
    
    # Create training_jobs table
    op.create_table(
        'training_jobs',
        sa.Column('job_id', sa.String(length=36), nullable=False),
        sa.Column('job_type', sa.Enum('dataset_generation', 'feature_selection', 'base_model', 'ensemble', 'full_pipeline', name='jobtype'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'running', 'completed', 'failed', name='jobstatus'), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('params', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('result', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('artifact_paths', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('oof_predictions_path', sa.String(length=500), nullable=True),
        sa.Column('model_name', sa.String(length=100), nullable=True),
        sa.Column('dataset_id', sa.String(length=36), nullable=True),
        sa.Column('oof_auc', sa.Float(), nullable=True),
        sa.Column('test_auc', sa.Float(), nullable=True),
        sa.Column('test_f1', sa.Float(), nullable=True),
        sa.Column('training_time_seconds', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('job_id')
    )
    
    # Create indexes for common queries
    op.create_index(op.f('ix_training_jobs_job_id'), 'training_jobs', ['job_id'], unique=False)
    op.create_index(op.f('ix_training_jobs_job_type'), 'training_jobs', ['job_type'], unique=False)
    op.create_index(op.f('ix_training_jobs_status'), 'training_jobs', ['status'], unique=False)
    op.create_index(op.f('ix_training_jobs_user_id'), 'training_jobs', ['user_id'], unique=False)
    op.create_index(op.f('ix_training_jobs_model_name'), 'training_jobs', ['model_name'], unique=False)
    op.create_index(op.f('ix_training_jobs_dataset_id'), 'training_jobs', ['dataset_id'], unique=False)


def downgrade() -> None:
    """Drop training_jobs table"""
    op.drop_index(op.f('ix_training_jobs_dataset_id'), table_name='training_jobs')
    op.drop_index(op.f('ix_training_jobs_model_name'), table_name='training_jobs')
    op.drop_index(op.f('ix_training_jobs_user_id'), table_name='training_jobs')
    op.drop_index(op.f('ix_training_jobs_status'), table_name='training_jobs')
    op.drop_index(op.f('ix_training_jobs_job_type'), table_name='training_jobs')
    op.drop_index(op.f('ix_training_jobs_job_id'), table_name='training_jobs')
    op.drop_table('training_jobs')
    
    # Drop enums
    op.execute('DROP TYPE jobstatus')
    op.execute('DROP TYPE jobtype')
