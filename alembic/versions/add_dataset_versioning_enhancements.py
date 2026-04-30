"""Add dataset versioning enhancements (semantic versioning + production tracking)

Revision ID: dataset_versioning_001
Revises: validation_queue_002
Create Date: 2026-04-03 22:00:00.000000

JIRA: USMA-84 - Implement Dataset Versioning System

ENHANCEMENTS:
- Add semantic_version (v1.0.0 format)
- Add is_production flag
- Add promoted_at timestamp
- Add promoted_by user tracking
- Add version_metadata JSONB (changelog, validation status)
- Add version_tags JSONB (labels: "stable", "experimental", etc.)
- Add indexes for version queries

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'dataset_versioning_001'
down_revision: Union[str, None] = 'validation_queue_002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Enhance metadata_datasets with production-grade versioning
    
    EXPAND PHASE:
    - Add semantic_version VARCHAR(20) (e.g., "v1.0.0", "v1.1.0")
    - Add is_production BOOLEAN (mark production versions)
    - Add promoted_at TIMESTAMP (when marked as production)
    - Add promoted_by INTEGER (who promoted it)
    - Add version_metadata JSONB (changelog, validation results)
    - Add version_tags JSONB (labels for filtering)
    - Keep existing 'version INT' for backward compatibility
    """
    
    # 1. Add semantic_version column
    op.add_column('metadata_datasets',
        sa.Column('semantic_version', sa.String(length=20), nullable=True)
    )
    
    # 2. Backfill semantic_version from existing version INT
    #    version=1 → "v1.0.0", version=2 → "v2.0.0"
    op.execute("""
        UPDATE metadata_datasets 
        SET semantic_version = 'v' || version || '.0.0'
        WHERE semantic_version IS NULL AND version IS NOT NULL
    """)
    
    # 3. Make semantic_version NOT NULL with default
    op.alter_column('metadata_datasets', 'semantic_version',
                    existing_type=sa.String(length=20),
                    nullable=False,
                    server_default='v1.0.0')
    
    # 4. Add is_production flag (default false)
    op.add_column('metadata_datasets',
        sa.Column('is_production', sa.Boolean(), 
                  nullable=False, server_default='false')
    )
    
    # 5. Add promoted_at timestamp
    op.add_column('metadata_datasets',
        sa.Column('promoted_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # 6. Add promoted_by user tracking
    op.add_column('metadata_datasets',
        sa.Column('promoted_by', sa.Integer(), nullable=True)
    )
    
    # 7. Add version_metadata JSONB
    op.add_column('metadata_datasets',
        sa.Column('version_metadata', postgresql.JSONB(astext_type=sa.Text()), 
                  nullable=True, server_default='{}')
    )
    
    # 8. Add version_tags JSONB (for labels like "stable", "experimental")
    op.add_column('metadata_datasets',
        sa.Column('version_tags', postgresql.JSONB(astext_type=sa.Text()), 
                  nullable=True, server_default='[]')
    )
    
    # 9. Create indexes for version queries
    op.create_index('idx_datasets_semantic_version', 
                    'metadata_datasets', ['semantic_version'], unique=False)
    op.create_index('idx_datasets_is_production', 
                    'metadata_datasets', ['is_production'], unique=False)
    op.create_index('idx_datasets_parent', 
                    'metadata_datasets', ['parent_dataset_id'], unique=False)
    op.create_index('idx_datasets_version_lineage',
                    'metadata_datasets', ['dataset_name', 'semantic_version'], 
                    unique=False)
    
    # 10. Add column comments
    op.execute("""
        COMMENT ON COLUMN metadata_datasets.semantic_version IS 'Semantic version (e.g., v1.0.0, v1.1.0)';
        COMMENT ON COLUMN metadata_datasets.is_production IS 'Whether this version is marked as production';
        COMMENT ON COLUMN metadata_datasets.promoted_at IS 'Timestamp when promoted to production';
        COMMENT ON COLUMN metadata_datasets.promoted_by IS 'User ID who promoted to production';
        COMMENT ON COLUMN metadata_datasets.version_metadata IS 'JSONB: changelog, validation_status, approval_notes';
        COMMENT ON COLUMN metadata_datasets.version_tags IS 'JSONB array: ["stable", "experimental", "deprecated"]';
        COMMENT ON COLUMN metadata_datasets.version IS 'Legacy integer version (deprecated, use semantic_version)';
    """)
    
    # 11. Create function to auto-increment semantic version
    op.execute("""
        CREATE OR REPLACE FUNCTION generate_next_semantic_version(
            p_dataset_name VARCHAR,
            p_bump_type VARCHAR DEFAULT 'patch'
        ) RETURNS VARCHAR AS $$
        DECLARE
            v_latest_version VARCHAR;
            v_major INT;
            v_minor INT;
            v_patch INT;
        BEGIN
            -- Get latest version for this dataset
            SELECT semantic_version INTO v_latest_version
            FROM metadata_datasets
            WHERE dataset_name = p_dataset_name
            ORDER BY uploaded_at DESC
            LIMIT 1;
            
            -- If no previous version, start with v1.0.0
            IF v_latest_version IS NULL THEN
                RETURN 'v1.0.0';
            END IF;
            
            -- Parse version (remove 'v' prefix)
            v_major := SPLIT_PART(SUBSTRING(v_latest_version FROM 2), '.', 1)::INT;
            v_minor := SPLIT_PART(SUBSTRING(v_latest_version FROM 2), '.', 2)::INT;
            v_patch := SPLIT_PART(SUBSTRING(v_latest_version FROM 2), '.', 3)::INT;
            
            -- Increment based on bump type
            IF p_bump_type = 'major' THEN
                v_major := v_major + 1;
                v_minor := 0;
                v_patch := 0;
            ELSIF p_bump_type = 'minor' THEN
                v_minor := v_minor + 1;
                v_patch := 0;
            ELSE  -- patch
                v_patch := v_patch + 1;
            END IF;
            
            RETURN 'v' || v_major || '.' || v_minor || '.' || v_patch;
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    """
    Rollback dataset versioning enhancements
    
    WARNING: This will remove version_metadata, version_tags, and production tracking.
    The legacy 'version INT' column will be preserved.
    """
    
    # 1. Drop function
    op.execute("DROP FUNCTION IF EXISTS generate_next_semantic_version(VARCHAR, VARCHAR)")
    
    # 2. Drop indexes
    op.drop_index('idx_datasets_version_lineage', table_name='metadata_datasets')
    op.drop_index('idx_datasets_parent', table_name='metadata_datasets')
    op.drop_index('idx_datasets_is_production', table_name='metadata_datasets')
    op.drop_index('idx_datasets_semantic_version', table_name='metadata_datasets')
    
    # 3. Drop new columns
    op.drop_column('metadata_datasets', 'version_tags')
    op.drop_column('metadata_datasets', 'version_metadata')
    op.drop_column('metadata_datasets', 'promoted_by')
    op.drop_column('metadata_datasets', 'promoted_at')
    op.drop_column('metadata_datasets', 'is_production')
    op.drop_column('metadata_datasets', 'semantic_version')
