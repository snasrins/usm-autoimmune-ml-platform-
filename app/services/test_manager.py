"""
Test Manager Service
Handles lab test definition management and approval workflows
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_

from app.models import (
    LabTestDefinition,
    UploadedFile
)


class TestManager:
    """Manage lab test definitions and approval workflows"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_pending_tests(
        self,
        file_id: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get unmapped columns from uploaded files that need approval
        
        Args:
            file_id: Filter by specific file (optional)
            limit: Maximum results
            
        Returns:
            List of pending test suggestions with metadata
        """
        query = self.db.query(UploadedFile).filter(
            UploadedFile.upload_status == 'completed'
        )
        
        if file_id:
            query = query.filter(UploadedFile.file_id == file_id)
        
        files = query.order_by(UploadedFile.uploaded_at.desc()).limit(limit).all()
        
        pending_tests = []
        seen_columns = set()
        
        for file in files:
            if not file.column_mapping:
                continue
            
            unmapped = file.column_mapping.get('unmapped', [])
            
            for col in unmapped:
                # Deduplicate by column name
                if col in seen_columns:
                    continue
                seen_columns.add(col)
                
                # Get suggestions if available
                suggestions = file.column_mapping.get('suggestions', [])
                suggestion = next(
                    (s for s in suggestions if s.get('original_column') == col),
                    None
                )
                
                pending_tests.append({
                    'original_column': col,
                    'file_id': file.file_id,
                    'filename': file.original_filename,
                    'upload_date': file.uploaded_at.isoformat(),
                    'suggested_code': suggestion.get('test_code') if suggestion else None,
                    'suggested_name': suggestion.get('display_name') if suggestion else None,
                    'suggested_category': suggestion.get('category') if suggestion else None,
                    'confidence': suggestion.get('confidence_score') if suggestion else None
                })
        
        return pending_tests
    
    def create_test(
        self,
        test_code: str,
        test_name: str,
        test_category: str,
        data_type: str = 'mixed',
        unit: Optional[str] = None,
        default_reference_range: Optional[Dict] = None,
        description: Optional[str] = None,
        specimen_type: Optional[str] = None,
        methodology: Optional[str] = None,
        created_by: int = 1
    ) -> LabTestDefinition:
        """
        Create new lab test definition
        
        Args:
            test_code: Unique test code (e.g., 'ana', 'esr')
            test_name: Human-readable name
            test_category: Test category
            data_type: 'numeric', 'qualitative', or 'mixed'
            unit: Measurement unit (optional)
            default_reference_range: JSONB reference range (optional)
            description: Test description (optional)
            specimen_type: e.g., 'serum', 'plasma' (optional)
            methodology: e.g., 'ELISA', 'IF' (optional)
            created_by: User ID
            
        Returns:
            Created LabTestDefinition instance
            
        Raises:
            ValueError: If test code already exists
        """
        # Check if test code exists
        existing = self.db.query(LabTestDefinition).filter(
            LabTestDefinition.test_code == test_code
        ).first()
        
        if existing:
            raise ValueError(f"Test code '{test_code}' already exists")
        
        # Validate data type
        if data_type not in ['numeric', 'qualitative', 'mixed']:
            raise ValueError(f"Invalid data_type: {data_type}")
        
        # Create test
        test = LabTestDefinition(
            test_code=test_code,
            test_name=test_name,
            test_category=test_category,
            data_type=data_type,
            unit=unit,
            default_reference_range=default_reference_range,
            description=description,
            is_active=True
        )
        
        self.db.add(test)
        self.db.commit()
        self.db.refresh(test)
        
        return test
    
    def update_test(
        self,
        test_id: int,
        updates: Dict[str, Any],
        updated_by: int = 1
    ) -> LabTestDefinition:
        """
        Update lab test definition
        
        Args:
            test_id: Test ID
            updates: Dict of fields to update
            updated_by: User ID
            
        Returns:
            Updated LabTestDefinition instance
            
        Raises:
            ValueError: If test not found
        """
        test = self.db.query(LabTestDefinition).filter(
            LabTestDefinition.test_id == test_id
        ).first()
        
        if not test:
            raise ValueError(f"Test ID {test_id} not found")
        
        # Allowed fields
        allowed_fields = {
            'test_name', 'test_category', 'data_type', 'unit',
            'default_reference_range', 'description', 'is_active'
        }
        
        # Update fields
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(test, field, value)
        
        self.db.commit()
        self.db.refresh(test)
        
        return test
    
    def deactivate_test(
        self,
        test_id: int,
        updated_by: int = 1
    ) -> LabTestDefinition:
        """
        Deactivate lab test (soft delete)
        
        Args:
            test_id: Test ID
            updated_by: User ID
            
        Returns:
            Deactivated LabTestDefinition instance
        """
        return self.update_test(
            test_id=test_id,
            updates={'is_active': False},
            updated_by=updated_by
        )
    
    def get_tests(
        self,
        test_category: Optional[str] = None,
        data_type: Optional[str] = None,
        is_active: bool = True,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict:
        """
        Get lab tests with filters and pagination
        
        Args:
            test_category: Filter by category
            data_type: Filter by data type
            is_active: Filter by active status
            search: Search in test_code or test_name
            limit: Results per page
            offset: Page offset
            
        Returns:
            Dict with 'tests' list and 'total' count
        """
        query = self.db.query(LabTestDefinition)
        
        # Filters
        if is_active is not None:
            query = query.filter(LabTestDefinition.is_active == is_active)
        
        if test_category:
            query = query.filter(LabTestDefinition.test_category == test_category)
        
        if data_type:
            query = query.filter(LabTestDefinition.data_type == data_type)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    LabTestDefinition.test_code.ilike(search_term),
                    LabTestDefinition.test_name.ilike(search_term)
                )
            )
        
        # Count total
        total = query.count()
        
        # Pagination
        tests = query.order_by(
            LabTestDefinition.test_category,
            LabTestDefinition.test_name
        ).limit(limit).offset(offset).all()
        
        return {
            'tests': tests,
            'total': total,
            'limit': limit,
            'offset': offset
        }
    
    def get_test_by_id(self, test_id: int) -> Optional[LabTestDefinition]:
        """Get single test by ID"""
        return self.db.query(LabTestDefinition).filter(
            LabTestDefinition.test_id == test_id
        ).first()
    
    def get_test_by_code(self, test_code: str) -> Optional[LabTestDefinition]:
        """Get single test by code"""
        return self.db.query(LabTestDefinition).filter(
            LabTestDefinition.test_code == test_code
        ).first()
    
    def get_categories(self) -> List[str]:
        """Get list of all test categories"""
        categories = self.db.query(LabTestDefinition.test_category).distinct().all()
        return sorted([c[0] for c in categories if c[0]])
    
    def get_test_stats(self) -> Dict:
        """Get statistics about test definitions"""
        total = self.db.query(func.count(LabTestDefinition.test_id)).scalar()
        active = self.db.query(func.count(LabTestDefinition.test_id)).filter(
            LabTestDefinition.is_active == True
        ).scalar()
        
        categories = self.db.query(
            LabTestDefinition.test_category,
            func.count(LabTestDefinition.test_id)
        ).group_by(LabTestDefinition.test_category).all()
        
        return {
            'total_tests': total,
            'active_tests': active,
            'inactive_tests': total - active,
            'categories': [
                {'category': cat, 'count': count}
                for cat, count in categories
            ]
        }
