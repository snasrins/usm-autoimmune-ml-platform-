"""
Category Lookup Service - Dynamic Diagnosis Categorization
Uses database lookup tables instead of hardcoded logic
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional, Dict
import re


class CategoryLookupService:
    """
    Service for dynamic diagnosis categorization
    NO hardcoded categories - all from database
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_category_for_diagnosis(self, diagnosis_text: str) -> str:
        """
        Get category for a diagnosis using database lookup
        
        Args:
            diagnosis_text: The diagnosis string from patient data
        
        Returns:
            Category name (e.g., 'SLE_with_LN') or 'Unknown' if no match
        """
        if not diagnosis_text or diagnosis_text.strip() == '':
            return 'Unknown'
        
        # Use the PostgreSQL function for consistent logic
        try:
            result = self.db.execute(
                "SELECT get_diagnosis_category(:diagnosis)",
                {"diagnosis": diagnosis_text}
            ).scalar()
            
            return result if result else 'Unknown'
        
        except Exception as e:
            # Fallback to Python implementation if function not available
            return self._python_fallback_lookup(diagnosis_text)
    
    def _python_fallback_lookup(self, diagnosis_text: str) -> str:
        """
        Python implementation of category lookup (fallback if SQL function unavailable)
        """
        from app.models.disease_category import DiseaseCategory, DiagnosisCategoryMapping
        
        # Get all active mappings ordered by priority
        mappings = self.db.query(
            DiagnosisCategoryMapping,
            DiseaseCategory.category_name
        ).join(DiseaseCategory).filter(
            DiagnosisCategoryMapping.is_active == True,
            DiseaseCategory.is_active == True
        ).order_by(
            DiagnosisCategoryMapping.priority.desc(),
            DiagnosisCategoryMapping.created_at.asc()
        ).all()
        
        diagnosis_lower = diagnosis_text.lower().strip()
        
        # Try to match with each mapping
        for mapping, category_name in mappings:
            pattern_lower = mapping.diagnosis_pattern.lower().strip()
            
            # Check match type
            is_match = False
            
            if mapping.match_type == 'exact':
                is_match = (diagnosis_lower == pattern_lower)
            
            elif mapping.match_type == 'contains':
                is_match = (pattern_lower in diagnosis_lower)
            
            elif mapping.match_type == 'starts_with':
                is_match = diagnosis_lower.startswith(pattern_lower)
            
            elif mapping.match_type == 'regex':
                try:
                    is_match = bool(re.search(mapping.diagnosis_pattern, diagnosis_text, re.IGNORECASE))
                except re.error:
                    # Invalid regex, skip
                    continue
            
            # If matched, return this category
            if is_match:
                return category_name
        
        # No match found
        return 'Unknown'
    
    def categorize_batch(self, diagnosis_list: list) -> Dict[str, str]:
        """
        Categorize multiple diagnoses at once
        
        Args:
            diagnosis_list: List of diagnosis strings
        
        Returns:
            Dict mapping each diagnosis to its category
        """
        results = {}
        for diagnosis in diagnosis_list:
            category = self.get_category_for_diagnosis(diagnosis)
            results[diagnosis] = category
        
        return results
    
    def get_all_categories(self, active_only: bool = True) -> list:
        """
        Get all available categories
        
        Args:
            active_only: Only return active categories
        
        Returns:
            List of category dicts with {category_id, category_name, category_code, category_label}
        """
        from app.models.disease_category import DiseaseCategory
        
        query = self.db.query(DiseaseCategory)
        
        if active_only:
            query = query.filter(DiseaseCategory.is_active == True)
        
        categories = query.all()
        
        return [
            {
                'category_id': cat.category_id,
                'category_name': cat.category_name,
                'category_code': cat.category_code,
                'category_label': cat.category_label,
                'description': cat.description
            }
            for cat in categories
        ]
    
    def validate_category_coverage(self, diagnosis_samples: list) -> Dict:
        """
        Test category coverage for a set of diagnosis samples
        Useful for validating mapping rules
        
        Args:
            diagnosis_samples: List of diagnosis strings to test
        
        Returns:
            Dict with coverage statistics
        """
        categorized = self.categorize_batch(diagnosis_samples)
        
        category_counts = {}
        unknown_count = 0
        
        for diagnosis, category in categorized.items():
            if category == 'Unknown':
                unknown_count += 1
            else:
                category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            'total_samples': len(diagnosis_samples),
            'categorized': len(diagnosis_samples) - unknown_count,
            'unknown': unknown_count,
            'coverage_rate': round((len(diagnosis_samples) - unknown_count) / len(diagnosis_samples) * 100, 2) if diagnosis_samples else 0,
            'category_distribution': category_counts,
            'uncategorized_samples': [d for d, c in categorized.items() if c == 'Unknown']
        }
