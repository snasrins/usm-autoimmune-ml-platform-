"""Evolve validation_queue for unstructured pipeline (expand-contract pattern)

Revision ID: validation_queue_002
Revises: 9a2e81360415
Create Date: 2026-04-03 21:00:00.000000

MIGRATION STRATEGY: Expand-Contract Pattern
- EXPAND: Add new columns (id, reviewed_by, rejection_reason, created_at, updated_at)
- EXPAND: Widen status VARCHAR(20) → VARCHAR(50)
- BACKWARD COMPAT: Keep validation_id, submitted_at, reviewer_comments for 2 versions
- FUTURE CONTRACT: Remove legacy columns in validation_queue_003 (deprecation period)

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'validation_queue_002'
down_revision: Union[str, None] = '9a2e81360415'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Evolve validation_queue for unstructured pipeline
    
    EXPAND PHASE (this migration):
    - Add id SERIAL for new unstructured pipeline code
    - Add reviewed_by INTEGER (separate from assigned_to)
    - Add rejection_reason TEXT (complement to reviewer_comments)
    - Add created_at, updated_at TIMESTAMP
    - Widen status VARCHAR(20) → VARCHAR(50)
    - Add stage index
    - Keep validation_id UUID for backward compatibility
    """
    
    # 1. Create sequence FIRST before referencing it
    op.execute("CREATE SEQUENCE IF NOT EXISTS validation_queue_id_seq")
    
    # 2. Add new id column (SERIAL, will become primary key candidate)
    op.add_column('validation_queue', 
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, 
                  server_default=sa.text("nextval('validation_queue_id_seq'::regclass)"))
    )
    
    # 3. Set sequence ownership and initial value
    op.execute("ALTER SEQUENCE validation_queue_id_seq OWNED BY validation_queue.id")
    op.execute("SELECT setval('validation_queue_id_seq', COALESCE((SELECT MAX(id) FROM validation_queue), 0) + 1, false)")
    
    # 2. Add reviewed_by column (separate from assigned_to)
    op.add_column('validation_queue',
        sa.Column('reviewed_by', sa.Integer(), nullable=True)
    )
    
    # 3. Add rejection_reason column (complement to reviewer_comments)
    op.add_column('validation_queue',
        sa.Column('rejection_reason', sa.Text(), nullable=True)
    )
    
    # 4. Add created_at column (sync with submitted_at via trigger)
    op.add_column('validation_queue',
        sa.Column('created_at', sa.DateTime(timezone=True), 
                  server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True)
    )
    
    # 5. Add updated_at column
    op.add_column('validation_queue',
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                  server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True)
    )
    
    # 6. Backfill created_at from submitted_at (data migration)
    op.execute("""
        UPDATE validation_queue 
        SET created_at = submitted_at 
        WHERE created_at IS NULL AND submitted_at IS NOT NULL
    """)
    
    # 7. Widen status column VARCHAR(20) → VARCHAR(50)
    op.alter_column('validation_queue', 'status',
                    existing_type=sa.VARCHAR(length=20),
                    type_=sa.VARCHAR(length=50),
                    existing_nullable=True,
                    existing_server_default=sa.text("'Pending'::character varying"))
    
    # 8. Update existing status values to new convention
    #    'Pending' → 'pending_review', 'Approved' → 'approved', 'Rejected' → 'rejected'
    op.execute("""
        UPDATE validation_queue 
        SET status = CASE 
            WHEN status = 'Pending' THEN 'pending_review'
            WHEN status = 'Approved' THEN 'approved'
            WHEN status = 'Rejected' THEN 'rejected'
            ELSE LOWER(status)
        END
    """)
    
    # 9. Update default for new rows
    op.alter_column('validation_queue', 'status',
                    existing_type=sa.VARCHAR(length=50),
                    server_default=sa.text("'pending_review'::character varying"))
    
    # 10. Make validation_data NOT NULL (safe if all rows have data)
    #     First check if any NULL exists
    op.execute("""
        UPDATE validation_queue 
        SET validation_data = '{}'::jsonb 
        WHERE validation_data IS NULL
    """)
    
    op.alter_column('validation_queue', 'validation_data',
                    existing_type=postgresql.JSONB(astext_type=sa.Text()),
                    nullable=False)
    
    # 11. Create additional indexes for performance
    op.create_index('idx_validation_stage', 'validation_queue', ['stage'], unique=False)
    op.create_index('idx_validation_created', 'validation_queue', ['created_at'], unique=False)
    op.create_index('idx_validation_id', 'validation_queue', ['id'], unique=True)  # Unique index on new id
    
    # 12. Create trigger to sync created_at ↔ submitted_at for backward compatibility
    op.execute("""
        CREATE OR REPLACE FUNCTION sync_validation_queue_timestamps()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Sync created_at → submitted_at (when created_at changes)
            IF NEW.created_at IS DISTINCT FROM OLD.created_at THEN
                NEW.submitted_at = NEW.created_at;
            END IF;
            
            -- Sync submitted_at → created_at (when submitted_at changes)
            IF NEW.submitted_at IS DISTINCT FROM OLD.submitted_at THEN
                NEW.created_at = NEW.submitted_at;
            END IF;
            
            -- Sync rejection_reason → reviewer_comments (when rejection_reason changes)
            IF NEW.rejection_reason IS DISTINCT FROM OLD.rejection_reason THEN
                NEW.reviewer_comments = NEW.rejection_reason;
            END IF;
            
            -- Sync reviewer_comments → rejection_reason (when reviewer_comments changes)
            IF NEW.reviewer_comments IS DISTINCT FROM OLD.reviewer_comments THEN
                NEW.rejection_reason = NEW.reviewer_comments;
            END IF;
            
            -- Always update updated_at
            NEW.updated_at = CURRENT_TIMESTAMP;
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        
        CREATE TRIGGER validation_queue_sync_timestamps
        BEFORE UPDATE ON validation_queue
        FOR EACH ROW
        EXECUTE FUNCTION sync_validation_queue_timestamps();
    """)
    
    # 13. Add comments for new columns
    op.execute("""
        COMMENT ON COLUMN validation_queue.id IS 'New SERIAL primary key for unstructured pipeline (v2.0+)';
        COMMENT ON COLUMN validation_queue.reviewed_by IS 'User ID who reviewed (separate from assigned_to)';
        COMMENT ON COLUMN validation_queue.rejection_reason IS 'Reason for rejection (synced with reviewer_comments)';
        COMMENT ON COLUMN validation_queue.created_at IS 'Record creation timestamp (synced with submitted_at)';
        COMMENT ON COLUMN validation_queue.updated_at IS 'Last update timestamp';
        COMMENT ON COLUMN validation_queue.validation_id IS 'Legacy UUID primary key (deprecated, use id instead)';
        COMMENT ON COLUMN validation_queue.submitted_at IS 'Legacy timestamp (deprecated, use created_at instead)';
        COMMENT ON COLUMN validation_queue.reviewer_comments IS 'Legacy comments field (deprecated, use rejection_reason instead)';
    """)


def downgrade() -> None:
    """
    Rollback validation_queue evolution
    
    IMPORTANT: This removes new columns and restores old schema.
    Data in new columns (id, reviewed_by, rejection_reason, created_at, updated_at) will be LOST.
    """
    
    # 1. Drop trigger
    op.execute("DROP TRIGGER IF EXISTS validation_queue_sync_timestamps ON validation_queue")
    op.execute("DROP FUNCTION IF EXISTS sync_validation_queue_timestamps()")
    
    # 2. Drop indexes
    op.drop_index('idx_validation_id', table_name='validation_queue')
    op.drop_index('idx_validation_created', table_name='validation_queue')
    op.drop_index('idx_validation_stage', table_name='validation_queue')
    
    # 3. Restore status values to old convention
    op.execute("""
        UPDATE validation_queue 
        SET status = CASE 
            WHEN status = 'pending_review' THEN 'Pending'
            WHEN status = 'approved' THEN 'Approved'
            WHEN status = 'rejected' THEN 'Rejected'
            ELSE status
        END
    """)
    
    # 4. Restore status default
    op.alter_column('validation_queue', 'status',
                    existing_type=sa.VARCHAR(length=50),
                    server_default=sa.text("'Pending'::character varying"))
    
    # 5. Restore status column width VARCHAR(50) → VARCHAR(20)
    op.alter_column('validation_queue', 'status',
                    existing_type=sa.VARCHAR(length=50),
                    type_=sa.VARCHAR(length=20),
                    existing_nullable=True)
    
    # 6. Make validation_data nullable again
    op.alter_column('validation_queue', 'validation_data',
                    existing_type=postgresql.JSONB(astext_type=sa.Text()),
                    nullable=True)
    
    # 7. Drop new columns
    op.drop_column('validation_queue', 'updated_at')
    op.drop_column('validation_queue', 'created_at')
    op.drop_column('validation_queue', 'rejection_reason')
    op.drop_column('validation_queue', 'reviewed_by')
    op.drop_column('validation_queue', 'id')
    
    # 8. Drop sequence
    op.execute("DROP SEQUENCE IF EXISTS validation_queue_id_seq")
