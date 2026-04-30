"""
Column Mapper Service
Maps dataset columns to lab test definitions
"""
import re
from typing import Dict, List, Tuple, Optional, Any
from sqlalchemy.orm import Session


class ColumnMapper:
    """Maps Excel/CSV columns to lab_test_definitions"""
    
    def __init__(self, db: Session):
        self.db = db
        self.known_tests = self._load_known_tests()
        
    def _load_known_tests(self) -> Dict[str, Dict]:
        """Load all known test definitions from database"""
        from app.models.lab_test import LabTestDefinition
        
        tests = {}
        for test in self.db.query(LabTestDefinition).all():
            tests[test.test_code] = {
                "test_id": test.test_id,
                "test_name": test.test_name,
                "test_code": test.test_code,
                "category": test.test_category,
                "unit": test.unit,
                "data_type": test.data_type
            }
        return tests
    
    def normalize_column_name(self, col_name: str) -> str:
        """Normalize column name to test_code format"""
        # Convert to lowercase
        normalized = col_name.lower()
        
        # Replace special characters
        normalized = re.sub(r'[^\w\s]', '', normalized)  # Remove punctuation
        normalized = re.sub(r'\s+', '_', normalized)  # Replace spaces with underscore
        normalized = re.sub(r'%', '_percent', normalized)  # Handle percentages
        normalized = re.sub(r'β', 'beta', normalized)  # Handle Greek letters
        normalized = re.sub(r'[_]+', '_', normalized)  # Remove double underscores
        normalized = normalized.strip('_')  # Remove leading/trailing underscores
        
        # Common abbreviations
        abbrev_map = {
            'twenty_four': '24',
            '24_hour': '24h',
            'quantification': 'quant',
            'antibody': 'ab',
            'immunoglobulin': 'ig',
        }
        
        for old, new in abbrev_map.items():
            normalized = normalized.replace(old, new)
        
        return normalized
    
    def map_column(self, col_name: str) -> Tuple[Optional[str], float]:
        """
        Map a column name to a test_code
        Returns: (test_code, confidence_score)
        """
        normalized = self.normalize_column_name(col_name)
        
        # Direct match
        if normalized in self.known_tests:
            return (normalized, 1.0)
        
        # Try fuzzy matching
        best_match = None
        best_score = 0.0
        
        for test_code, test_info in self.known_tests.items():
            # Check against test_code
            score = self._similarity(normalized, test_code)
            if score > best_score:
                best_score = score
                best_match = test_code
            
            # Check against test_name
            test_name_norm = self.normalize_column_name(test_info['test_name'])
            score = self._similarity(normalized, test_name_norm)
            if score > best_score:
                best_score = score
                best_match = test_code
        
        # Only return if confidence > 70%
        if best_score > 0.7:
            return (best_match, best_score)
        
        return (None, 0.0)
    
    def _similarity(self, s1: str, s2: str) -> float:
        """Calculate string similarity (simple ratio)"""
        if s1 == s2:
            return 1.0
        
        # Check if one contains the other
        if s1 in s2 or s2 in s1:
            return 0.8
        
        # Levenshtein-like simple comparison
        # Count matching characters
        set1 = set(s1.split('_'))
        set2 = set(s2.split('_'))
        
        if len(set1) == 0 or len(set2) == 0:
            return 0.0
        
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        
        return len(intersection) / len(union)
    
    def map_columns(self, columns: List[str]) -> Dict[str, Any]:
        """
        Map all columns in a dataset
        Returns mapping results with statistics
        """
        mapped = {}
        unmapped = []
        low_confidence = []
        
        for col in columns:
            test_code, confidence = self.map_column(col)
            
            if test_code:
                test_info = self.known_tests[test_code]
                mapped[col] = {
                    "test_code": test_code,
                    "test_id": test_info["test_id"],
                    "test_name": test_info["test_name"],
                    "category": test_info["category"],
                    "confidence": confidence
                }
                
                if confidence < 0.9:
                    low_confidence.append({
                        "original": col,
                        "mapped_to": test_code,
                        "confidence": confidence
                    })
            else:
                unmapped.append(col)
        
        return {
            "mapped": mapped,
            "unmapped": unmapped,
            "low_confidence": low_confidence,
            "stats": {
                "total_columns": len(columns),
                "mapped_count": len(mapped),
                "unmapped_count": len(unmapped),
                "low_confidence_count": len(low_confidence)
            }
        }
    
    def suggest_new_tests(self, unmapped_columns: List[str]) -> List[Dict]:
        """
        Suggest test definitions for unmapped columns
        """
        suggestions = []
        
        for col in unmapped_columns:
            normalized = self.normalize_column_name(col)
            
            # Try to categorize
            category = self._guess_category(col)
            data_type = self._guess_data_type(col)
            
            suggestions.append({
                "original_column": col,  # Fixed: was "original_name"
                "test_code": normalized,  # Fixed: was "suggested_code"
                "test_name": col,  # Original column name as test name
                "suggested_category": category,
                "suggested_data_type": data_type,
                "requires_admin_approval": True
            })
        
        return suggestions
    
    def _guess_category(self, col_name: str) -> str:
        """Guess test category from column name"""
        col_lower = col_name.lower()
        
        if any(word in col_lower for word in ['il-', 'interleukin', 'ifn', 'interferon', 'tnf', 'ccl', 'cxcl']):
            return 'Cytokine'
        elif any(word in col_lower for word in ['cd', 'lymph', 'cell']):
            return 'Immune_Cells'
        elif any(word in col_lower for word in ['anti', 'antibody', 'ab']):
            return 'Autoantibody'
        elif any(word in col_lower for word in ['wbc', 'hgb', 'plt', 'blood']):
            return 'Hematology'
        elif any(word in col_lower for word in ['crp', 'esr', 'inflammation']):
            return 'Inflammation'
        elif any(word in col_lower for word in ['protein', 'urine', 'kidney']):
            return 'Kidney_Function'
        elif any(word in col_lower for word in ['ig', 'immunoglobulin']):
            return 'Immunoglobulin'
        else:
            return 'Biomarker'
    
    def _guess_data_type(self, col_name: str) -> str:
        """Guess data type from column name"""
        col_lower = col_name.lower()
        
        # Qualitative indicators
        if any(word in col_lower for word in ['positive', 'negative', 'ana', 'anti']):
            return 'qualitative'
        elif '%' in col_name:
            return 'numeric'
        else:
            return 'numeric'  # Default to numeric


# Usage example
if __name__ == "__main__":
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    mapper = ColumnMapper(db)
    
    # Test with SLE columns
    sle_columns = ["WBC", "NEU%", "HGB", "C3", "C4", "ANA", "dsDNA", "SLEDAI"]
    
    results = mapper.map_columns(sle_columns)
    
    print(f"Mapped: {results['stats']['mapped_count']}/{results['stats']['total_columns']}")
    print(f"Unmapped: {results['unmapped']}")
    
    for col, mapping in results['mapped'].items():
        print(f"  {col} → {mapping['test_code']} ({mapping['confidence']:.2f})")
    
    db.close()
