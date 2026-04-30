"""Add validation_queue table for unstructured pipeline

Revision ID: validation_queue_001
Revises: 9a2e81360415
Create Date: 2026-04-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'validation_queue_001'
down_revision: Union[str, None] = '9a2e81360415'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create validation_queue table for human-in-the-loop workflow"""
    
    # Create validation_queue table
    op.create_table(
        'validation_queue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dataset_id', sa.Integer(), nullable=True),
        sa.Column('stage', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending_review'),
        sa.Column('assigned_to', sa.Integer(), nullable=True),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('validation_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('idx_validation_status', 'validation_queue', ['status'], unique=False)
    op.create_index('idx_validation_stage', 'validation_queue', ['stage'], unique=False)
    op.create_index('idx_validation_assigned', 'validation_queue', ['assigned_to'], unique=False)
    op.create_index('idx_validation_created', 'validation_queue', ['created_at'], unique=False)
    
    # Add comment to table
    op.execute("""
        COMMENT ON TABLE validation_queue IS 'Human validation queue for unstructured data (OCR + NER results)'
    """)
    op.execute("""
        COMMENT ON COLUMN validation_queue.validation_data IS 'JSONB containing document metadata, extracted text, and medical entities'
    """)
    op.execute("""
        COMMENT ON COLUMN validation_queue.stage IS 'Pipeline stage: ocr_complete, ner_complete, validated, rejected'
    """)
    op.execute("""
        COMMENT ON COLUMN validation_queue.status IS 'Review status: pending_review, in_review, approved, rejected'
    """)


def downgrade() -> None:
    """Drop validation_queue table"""
    
    # Drop indexes
    op.drop_index('idx_validation_created', table_name='validation_queue')
    op.drop_index('idx_validation_assigned', table_name='validation_queue')
    op.drop_index('idx_validation_stage', table_name='validation_queue')
    op.drop_index('idx_validation_status', table_name='validation_queue')
    
    # Drop table
    op.drop_table('validation_queue')
