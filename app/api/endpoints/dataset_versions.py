"""
Dataset Versioning API Endpoints

JIRA: USMA-27 - Implement Dataset Versioning API

Provides endpoints for:
- Creating new dataset versions
- Listing all versions of a dataset
- Viewing version lineage (parent-child tree)
- Promoting versions to production
- Tagging versions with labels
- Comparing versions (diff metadata)
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter()


# ===============================
# Pydantic Models
# ===============================

class VersionCreate(BaseModel):
    """Request to create a new dataset version"""
    dataset_name: str = Field(..., description="Name of the dataset")
    file_type: str = Field(..., description="CSV, Excel, PDF, Image, etc.")
    parent_version_id: Optional[str] = Field(None, description="UUID of parent version")
    bump_type: str = Field("patch", description="major, minor, or patch")
    changelog: Optional[str] = Field(None, description="What changed in this version")
    tags: List[str] = Field(default_factory=list, description="Labels: stable, experimental, etc.")
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    file_size_mb: Optional[float] = None
    file_hash: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class VersionResponse(BaseModel):
    """Dataset version information"""
    dataset_id: str
    dataset_name: str
    semantic_version: str
    version: int  # Legacy
    file_type: str
    uploaded_by: str
    uploaded_at: datetime
    is_production: bool
    promoted_at: Optional[datetime]
    promoted_by: Optional[int]
    parent_dataset_id: Optional[str]
    row_count: Optional[int]
    column_count: Optional[int]
    file_size_mb: Optional[float]
    file_hash: Optional[str]
    status: str
    version_metadata: Dict[str, Any]
    version_tags: List[str]
    
    class Config:
        from_attributes = True


class VersionLineage(BaseModel):
    """Version tree structure - simplified to avoid circular refs"""
    dataset_id: str
    semantic_version: str
    is_production: bool
    uploaded_at: datetime
    parent_dataset_id: Optional[str] = None
    children_count: int = 0


class PromoteRequest(BaseModel):
    """Request to promote version to production"""
    notes: Optional[str] = Field(None, description="Reason for promotion")


# ===============================
# Endpoints
# ===============================

@router.post("/versions", response_model=VersionResponse, status_code=status.HTTP_201_CREATED)
async def create_dataset_version(
    version_data: VersionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new dataset version
    
    - Automatically generates semantic version (v1.0.0, v1.1.0, v2.0.0)
    - Links to parent version for lineage tracking
    - Stores changelog and tags
    
    Returns:
        Created dataset version with generated UUID and semantic_version
    """
    try:
        # Generate next semantic version
        query_version = text("""
            SELECT generate_next_semantic_version(:dataset_name, :bump_type) AS next_version
        """)
        
        result = db.execute(query_version, {
            "dataset_name": version_data.dataset_name,
            "bump_type": version_data.bump_type
        }).fetchone()
        
        next_version = result[0]
        
        # Parse version number (v1.0.0 → 1)
        major_version = int(next_version.split('.')[0][1:])  # Remove 'v' and convert
        
        # Build version_metadata
        version_metadata = {
            "changelog": version_data.changelog or "",
            "created_by": current_user.username,
            "created_at": datetime.utcnow().isoformat(),
            "bump_type": version_data.bump_type
        }
        version_metadata.update(version_data.metadata)
        
        # Insert new version
        query_insert = text("""
            INSERT INTO metadata_datasets (
                dataset_name, file_type, uploaded_by, version, semantic_version,
                parent_dataset_id, row_count, column_count, file_size_mb, file_hash,
                status, version_metadata, version_tags
            ) VALUES (
                :dataset_name, :file_type, :uploaded_by, :version, :semantic_version,
                :parent_dataset_id, :row_count, :column_count, :file_size_mb, :file_hash,
                'Uploaded', CAST(:version_metadata AS jsonb), CAST(:version_tags AS jsonb)
            )
            RETURNING dataset_id, uploaded_at
        """)
        
        result = db.execute(query_insert, {
            "dataset_name": version_data.dataset_name,
            "file_type": version_data.file_type,
            "uploaded_by": current_user.username,
            "version": major_version,
            "semantic_version": next_version,
            "parent_dataset_id": version_data.parent_version_id,
            "row_count": version_data.row_count,
            "column_count": version_data.column_count,
            "file_size_mb": version_data.file_size_mb,
            "file_hash": version_data.file_hash,
            "version_metadata": str(version_metadata).replace("'", '"'),
            "version_tags": str(version_data.tags).replace("'", '"')
        })
        
        row = result.fetchone()
        db.commit()
        
        return VersionResponse(
            dataset_id=str(row[0]),
            dataset_name=version_data.dataset_name,
            semantic_version=next_version,
            version=major_version,
            file_type=version_data.file_type,
            uploaded_by=current_user.username,
            uploaded_at=row[1],
            is_production=False,
            promoted_at=None,
            promoted_by=None,
            parent_dataset_id=version_data.parent_version_id,
            row_count=version_data.row_count,
            column_count=version_data.column_count,
            file_size_mb=version_data.file_size_mb,
            file_hash=version_data.file_hash,
            status="Uploaded",
            version_metadata=version_metadata,
            version_tags=version_data.tags
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create version: {str(e)}"
        )


@router.get("/datasets/{dataset_name}/versions", response_model=List[VersionResponse])
async def list_dataset_versions(
    dataset_name: str,
    include_deprecated: bool = Query(False, description="Include deprecated versions"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all versions of a dataset
    
    Returns versions in reverse chronological order (newest first)
    """
    try:
        tag_filter = "" if include_deprecated else "AND NOT version_tags @> '[\"deprecated\"]'::jsonb"
        
        query = text(f"""
            SELECT 
                dataset_id, dataset_name, semantic_version, version, file_type,
                uploaded_by, uploaded_at, is_production, promoted_at, promoted_by,
                parent_dataset_id, row_count, column_count, file_size_mb, file_hash,
                status, version_metadata, version_tags
            FROM metadata_datasets
            WHERE dataset_name = :dataset_name {tag_filter}
            ORDER BY uploaded_at DESC
        """)
        
        results = db.execute(query, {"dataset_name": dataset_name}).fetchall()
        
        return [
            VersionResponse(
                dataset_id=str(row[0]),
                dataset_name=row[1],
                semantic_version=row[2],
                version=row[3],
                file_type=row[4],
                uploaded_by=row[5],
                uploaded_at=row[6],
                is_production=row[7],
                promoted_at=row[8],
                promoted_by=row[9],
                parent_dataset_id=str(row[10]) if row[10] else None,
                row_count=row[11],
                column_count=row[12],
                file_size_mb=row[13],
                file_hash=row[14],
                status=row[15],
                version_metadata=row[16] or {},
                version_tags=row[17] or []
            )
            for row in results
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list versions: {str(e)}"
        )


@router.get("/datasets/{dataset_id}/lineage", response_model=Dict[str, Any])
async def get_version_lineage(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get version lineage (ancestors and descendants)
    
    Returns complete family tree as flat list with relationships
    """
    try:
        # Use two separate CTEs for ancestors and descendants
        query = text("""
            WITH RECURSIVE 
            -- Get all ancestors (parents, grandparents, etc.)
            ancestors AS (
                SELECT 
                    dataset_id, parent_dataset_id, semantic_version, 
                    is_production, uploaded_at, -1 AS depth
                FROM metadata_datasets
                WHERE dataset_id = (
                    SELECT parent_dataset_id 
                    FROM metadata_datasets 
                    WHERE dataset_id = CAST(:dataset_id AS UUID)
                )
                
                UNION ALL
                
                SELECT 
                    md.dataset_id, md.parent_dataset_id, md.semantic_version,
                    md.is_production, md.uploaded_at, a.depth - 1
                FROM metadata_datasets md
                INNER JOIN ancestors a ON md.dataset_id = a.parent_dataset_id
            ),
            -- Get all descendants (children, grandchildren, etc.)
            descendants AS (
                SELECT 
                    dataset_id, parent_dataset_id, semantic_version, 
                    is_production, uploaded_at, 1 AS depth
                FROM metadata_datasets
                WHERE parent_dataset_id = CAST(:dataset_id AS UUID)
                
                UNION ALL
                
                SELECT 
                    md.dataset_id, md.parent_dataset_id, md.semantic_version,
                    md.is_production, md.uploaded_at, d.depth + 1
                FROM metadata_datasets md
                INNER JOIN descendants d ON md.parent_dataset_id = d.dataset_id
            ),
            -- Combine: ancestors + current + descendants
            full_tree AS (
                SELECT * FROM ancestors
                
                UNION ALL
                
                SELECT 
                    dataset_id, parent_dataset_id, semantic_version, 
                    is_production, uploaded_at, 0 AS depth
                FROM metadata_datasets
                WHERE dataset_id = CAST(:dataset_id AS UUID)
                
                UNION ALL
                
                SELECT * FROM descendants
            )
            SELECT 
                dataset_id, parent_dataset_id, semantic_version, 
                is_production, uploaded_at, depth
            FROM full_tree
            ORDER BY depth, uploaded_at
        """)
        
        results = db.execute(query, {"dataset_id": dataset_id}).fetchall()
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset {dataset_id} not found"
            )
        
        # Build flat list of versions with relationships
        versions = []
        current_version = None
        
        for row in results:
            version_info = {
                "dataset_id": str(row[0]),
                "parent_dataset_id": str(row[1]) if row[1] else None,
                "semantic_version": row[2],
                "is_production": row[3],
                "uploaded_at": row[4].isoformat(),
                "depth": row[5],
                "relationship": "ancestor" if row[5] < 0 else ("current" if row[5] == 0 else "descendant")
            }
            
            versions.append(version_info)
            
            if row[5] == 0:  # Current version
                current_version = version_info
        
        return {
            "current": current_version,
            "all_versions": versions,
            "total_versions": len(versions),
            "ancestors_count": sum(1 for v in versions if v["depth"] < 0),
            "descendants_count": sum(1 for v in versions if v["depth"] > 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get lineage: {str(e)}"
        )


@router.post("/datasets/{dataset_id}/promote", response_model=Dict[str, str])
async def promote_to_production(
    dataset_id: str,
    promote_request: PromoteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Promote a dataset version to production
    
    - Demotes current production version (if any)
    - Marks this version as production
    - Records who promoted and when
    """
    try:
        # Get dataset info
        query_check = text("""
            SELECT dataset_name, is_production 
            FROM metadata_datasets 
            WHERE dataset_id = CAST(:dataset_id AS UUID)
        """)
        
        result = db.execute(query_check, {"dataset_id": dataset_id}).fetchone()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset {dataset_id} not found"
            )
        
        dataset_name = result[0]
        is_already_production = result[1]
        
        if is_already_production:
            return {
                "message": "Dataset is already marked as production",
                "dataset_id": dataset_id
            }
        
        # Demote current production version (if any)
        query_demote = text("""
            UPDATE metadata_datasets
            SET is_production = false
            WHERE dataset_name = :dataset_name AND is_production = true
        """)
        
        db.execute(query_demote, {"dataset_name": dataset_name})
        
        # Promote new version
        query_promote = text("""
            UPDATE metadata_datasets
            SET is_production = true,
                promoted_at = NOW(),
                promoted_by = :user_id,
                version_metadata = version_metadata || CAST(:promotion_notes AS jsonb)
            WHERE dataset_id = CAST(:dataset_id AS UUID)
            RETURNING semantic_version
        """)
        
        promotion_notes = {
            "promotion_notes": promote_request.notes or "",
            "promoted_by_username": current_user.username,
            "promoted_at": datetime.utcnow().isoformat()
        }
        
        result = db.execute(query_promote, {
            "dataset_id": dataset_id,
            "user_id": current_user.id,
            "promotion_notes": str(promotion_notes).replace("'", '"')
        })
        
        version = result.fetchone()[0]
        db.commit()
        
        return {
            "message": f"Version {version} promoted to production",
            "dataset_id": dataset_id,
            "version": version
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to promote version: {str(e)}"
        )


@router.post("/datasets/{dataset_id}/tag", response_model=Dict[str, str])
async def tag_version(
    dataset_id: str,
    tags: List[str] = Query(..., description="Tags to add: stable, experimental, deprecated"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add tags to a dataset version
    
    Common tags:
    - stable: Production-ready, tested
    - experimental: Under development
    - deprecated: No longer recommended
    - validated: Passed validation checks
    """
    try:
        # Add tags (merge with existing and deduplicate)
        query = text("""
            UPDATE metadata_datasets
            SET version_tags = (
                SELECT jsonb_agg(DISTINCT value)
                FROM jsonb_array_elements(
                    COALESCE(version_tags, '[]'::jsonb) || CAST(:new_tags AS jsonb)
                )
            )
            WHERE dataset_id = CAST(:dataset_id AS UUID)
            RETURNING semantic_version
        """)
        
        result = db.execute(query, {
            "dataset_id": dataset_id,
            "new_tags": str(tags).replace("'", '"')
        })
        
        row = result.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset {dataset_id} not found"
            )
        
        db.commit()
        
        return {
            "message": f"Tags added: {', '.join(tags)}",
            "dataset_id": dataset_id,
            "version": row[0]
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add tags: {str(e)}"
        )


@router.get("/production", response_model=List[VersionResponse])
async def list_production_datasets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all datasets currently marked as production
    
    Returns one version per dataset (the active production version)
    """
    try:
        query = text("""
            SELECT 
                dataset_id, dataset_name, semantic_version, version, file_type,
                uploaded_by, uploaded_at, is_production, promoted_at, promoted_by,
                parent_dataset_id, row_count, column_count, file_size_mb, file_hash,
                status, version_metadata, version_tags
            FROM metadata_datasets
            WHERE is_production = true
            ORDER BY dataset_name, promoted_at DESC
        """)
        
        results = db.execute(query).fetchall()
        
        return [
            VersionResponse(
                dataset_id=str(row[0]),
                dataset_name=row[1],
                semantic_version=row[2],
                version=row[3],
                file_type=row[4],
                uploaded_by=row[5],
                uploaded_at=row[6],
                is_production=row[7],
                promoted_at=row[8],
                promoted_by=row[9],
                parent_dataset_id=str(row[10]) if row[10] else None,
                row_count=row[11],
                column_count=row[12],
                file_size_mb=row[13],
                file_hash=row[14],
                status=row[15],
                version_metadata=row[16] or {},
                version_tags=row[17] or []
            )
            for row in results
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list production datasets: {str(e)}"
        )
