"""
Flexible Preview & Staging Service
Handles CSV preview, editing, and validation before saving to database
100% flexible - NO hardcoded schema
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import uuid
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.flexible_data import ImportPreviewStaging, DatasetSchema


class FlexiblePreviewService:
    """Manage CSV preview and staging before final import"""
    
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
    
    @staticmethod
    def _convert_to_python_type(value: Any) -> Any:
        """
        Convert pandas/numpy types to Python native types for JSON serialization
        
        Args:
            value: Value from pandas DataFrame (could be numpy type)
        
        Returns:
            Python native type (int, float, bool, str, None)
        """
        # Handle pandas NA/NaN
        if pd.isna(value):
            return None
        
        # Handle numpy numeric types
        if isinstance(value, (np.integer, np.int64, np.int32, np.int16, np.int8)):
            return int(value)
        
        if isinstance(value, (np.floating, np.float64, np.float32)):
            return float(value)
        
        # Handle numpy bool
        if isinstance(value, (np.bool_, bool)):
            return bool(value)
        
        # Handle numpy datetime
        if isinstance(value, (np.datetime64, pd.Timestamp)):
            return value.isoformat() if hasattr(value, 'isoformat') else str(value)
        
        # Handle numpy string types
        if isinstance(value, (np.str_, np.bytes_)):
            return str(value)
        
        # Handle Series (edge case)
        if isinstance(value, pd.Series):
            return FlexiblePreviewService._convert_to_python_type(
                value.iloc[0] if len(value) > 0 else None
            )
        
        # Already a Python native type
        return value
    
    def create_preview_from_csv(
        self,
        file_path: str,
        dataset_type: str,
        dataset_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Parse CSV/Excel and create editable preview in staging table
        
        Args:
            file_path: Path to CSV or Excel file
            dataset_type: Dataset classification (e.g., 'SLE', 'Sjogren', 'Custom1')
            dataset_name: User-friendly dataset name
        
        Returns:
            Dict with session_id, preview data, and schema
        """
        # Generate session ID
        session_id = uuid.uuid4()
        
        # Read CSV or Excel based on file extension
        if file_path.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path, engine='openpyxl')
        else:
            df = pd.read_csv(file_path)
        
        # Clean column names (lowercase, strip spaces, replace spaces with underscores)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # Handle duplicate column names by adding suffixes
        cols = pd.Series(df.columns)
        for dup in cols[cols.duplicated()].unique():
            dup_indices = cols[cols == dup].index.tolist()
            for i, idx in enumerate(dup_indices[1:], start=1):
                cols.iloc[idx] = f"{dup}_{i}"
        df.columns = cols
        
        # Auto-detect schema
        schema = self._detect_schema(df, dataset_type)
        
        # Calculate expiration time (24 hours from now)
        expires_at = datetime.now() + timedelta(hours=24)
        
        # Insert rows into staging
        preview_records = []
        for idx, row in df.iterrows():
            # Convert row to dict and clean all values
            row_dict = row.to_dict()
            
            # Clean all values: convert numpy/pandas types to Python native types
            cleaned_dict = {
                k: self._convert_to_python_type(v)
                for k, v in row_dict.items()
            }
            
            # Basic validation
            validation_errors = self._validate_row(cleaned_dict, schema)
            validation_status = 'invalid' if validation_errors else 'valid'
            
            staging_record = ImportPreviewStaging(
                session_id=session_id,
                dataset_type=dataset_type,
                dataset_name=dataset_name,
                row_data=cleaned_dict,
                row_number=int(idx) + 1,  # 1-indexed for user
                validation_status=validation_status,
                validation_errors=validation_errors if validation_errors else None,
                expires_at=expires_at
            )
            preview_records.append(staging_record)
        
        # Bulk insert
        self.db.bulk_save_objects(preview_records)
        self.db.commit()
        
        # Register or update dataset schema
        self._register_schema(dataset_type, schema, dataset_name)
        
        return {
            'session_id': str(session_id),
            'dataset_type': dataset_type,
            'dataset_name': dataset_name,
            'row_count': len(df),
            'column_count': len(df.columns),
            'schema': schema,
            'expires_at': expires_at.isoformat(),
            'preview_url': f'/api/v1/preview/{session_id}'
        }
    
    def get_preview_data(
        self,
        session_id: uuid.UUID,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Get preview data for editing
        
        Args:
            session_id: Preview session ID
            page: Page number (1-indexed)
            page_size: Records per page
        
        Returns:
            Dict with paginated preview data
        """
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Query staging records
        query = self.db.query(ImportPreviewStaging).filter(
            and_(
                ImportPreviewStaging.session_id == session_id,
                ImportPreviewStaging.is_deleted == False
            )
        )
        
        total_count = query.count()
        records = query.order_by(ImportPreviewStaging.row_number).offset(offset).limit(page_size).all()
        
        # Format for frontend
        rows = []
        for record in records:
            rows.append({
                'staging_id': record.staging_id,
                'row_number': record.row_number,
                'data': record.row_data,
                'is_edited': record.is_edited,
                'validation_status': record.validation_status,
                'validation_errors': record.validation_errors
            })
        
        # Get schema if available
        first_record = records[0] if records else None
        schema = None
        if first_record:
            schema_record = self.db.query(DatasetSchema).filter(
                DatasetSchema.dataset_type == first_record.dataset_type
            ).first()
            if schema_record:
                schema = schema_record.schema_definition
        
        return {
            'session_id': str(session_id),
            'total_rows': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size,
            'rows': rows,
            'schema': schema
        }
    
    def edit_row(
        self,
        staging_id: int,
        field_name: str,
        new_value: Any
    ) -> Dict[str, Any]:
        """
        Edit a single field in preview
        
        Args:
            staging_id: Staging record ID
            field_name: Field to edit
            new_value: New value
        
        Returns:
            Updated row data
        """
        record = self.db.query(ImportPreviewStaging).filter(
            ImportPreviewStaging.staging_id == staging_id
        ).first()
        
        if not record:
            raise ValueError(f"Staging record {staging_id} not found")
        
        # Track edit history
        old_value = record.row_data.get(field_name)
        edit_entry = {
            'field': field_name,
            'old_value': old_value,
            'new_value': new_value,
            'edited_at': datetime.now().isoformat(),
            'edited_by': self.user_id
        }
        
        # Update edit history
        if record.edit_history:
            record.edit_history.append(edit_entry)
        else:
            record.edit_history = [edit_entry]
        
        # Update row data
        record.row_data[field_name] = new_value
        record.is_edited = True
        
        # Re-validate
        schema_record = self.db.query(DatasetSchema).filter(
            DatasetSchema.dataset_type == record.dataset_type
        ).first()
        
        if schema_record:
            validation_errors = self._validate_row(record.row_data, schema_record.schema_definition)
            record.validation_status = 'invalid' if validation_errors else 'valid'
            record.validation_errors = validation_errors if validation_errors else None
        
        self.db.commit()
        
        return {
            'staging_id': staging_id,
            'field': field_name,
            'new_value': new_value,
            'validation_status': record.validation_status,
            'validation_errors': record.validation_errors
        }
    
    def delete_row(self, staging_id: int) -> Dict[str, Any]:
        """
        Soft delete a row from preview
        
        Args:
            staging_id: Staging record ID
        
        Returns:
            Success confirmation
        """
        record = self.db.query(ImportPreviewStaging).filter(
            ImportPreviewStaging.staging_id == staging_id
        ).first()
        
        if not record:
            raise ValueError(f"Staging record {staging_id} not found")
        
        record.is_deleted = True
        self.db.commit()
        
        return {
            'staging_id': staging_id,
            'deleted': True
        }
    
    def auto_fill_missing(
        self,
        session_id: uuid.UUID,
        strategy: str = 'median'
    ) -> Dict[str, Any]:
        """
        Auto-fill missing values in preview
        
        Args:
            session_id: Preview session ID
            strategy: Fill strategy ('median', 'mean', 'mode', 'forward_fill')
        
        Returns:
            Summary of filled values
        """
        records = self.db.query(ImportPreviewStaging).filter(
            and_(
                ImportPreviewStaging.session_id == session_id,
                ImportPreviewStaging.is_deleted == False
            )
        ).all()
        
        if not records:
            return {'filled_count': 0, 'message': 'No records found'}
        
        # Convert to DataFrame for easier processing
        df = pd.DataFrame([r.row_data for r in records])
        
        # Identify columns with missing values
        missing_cols = df.columns[df.isna().any()].tolist()
        
        filled_summary = {}
        
        for col in missing_cols:
            if df[col].dtype in ['int64', 'float64']:
                # Numeric column
                if strategy == 'median':
                    fill_value = df[col].median()
                elif strategy == 'mean':
                    fill_value = df[col].mean()
                else:
                    fill_value = df[col].median()
                
                df[col].fillna(fill_value, inplace=True)
                filled_summary[col] = {
                    'type': 'numeric',
                    'fill_value': self._convert_to_python_type(fill_value),
                    'filled_count': int(df[col].isna().sum())
                }
            else:
                # Categorical column
                if strategy == 'mode':
                    fill_value = df[col].mode()[0] if not df[col].mode().empty else 'Unknown'
                else:
                    fill_value = 'Unknown'
                
                df[col].fillna(fill_value, inplace=True)
                filled_summary[col] = {
                    'type': 'categorical',
                    'fill_value': self._convert_to_python_type(fill_value),
                    'filled_count': int(df[col].isna().sum())
                }
        
        # Update records
        for idx, record in enumerate(records):
            # Convert to dict and clean all values
            row_dict = df.iloc[idx].to_dict()
            record.row_data = {
                k: self._convert_to_python_type(v)
                for k, v in row_dict.items()
            }
            record.is_edited = True
        
        self.db.commit()
        
        return {
            'session_id': str(session_id),
            'strategy': strategy,
            'filled_summary': filled_summary,
            'total_rows_updated': len(records)
        }
    
    def cleanup_expired_sessions(self):
        """Remove expired staging records (older than 24 hours)"""
        deleted_count = self.db.query(ImportPreviewStaging).filter(
            ImportPreviewStaging.expires_at < datetime.now()
        ).delete()
        
        self.db.commit()
        
        return {'deleted_count': deleted_count}
    
    def _detect_schema(self, df: pd.DataFrame, dataset_type: str) -> Dict[str, Any]:
        """
        Auto-detect schema from DataFrame
        
        Args:
            df: Pandas DataFrame
            dataset_type: Dataset classification
        
        Returns:
            Schema definition as dict
        """
        columns = []
        categories = {}
        
        for col in df.columns:
            # Get example values and convert to Python types
            try:
                col_series = df[col]
                # Ensure we have a Series, not a DataFrame
                if isinstance(col_series, pd.DataFrame):
                    col_series = col_series.iloc[:, 0]
                
                example_vals = list(col_series.dropna().head(3))
                example_vals_clean = [self._convert_to_python_type(v) for v in example_vals]
            except Exception as e:
                # Fallback to empty if extraction fails
                example_vals_clean = []
            
            # Safely get nullable status
            try:
                col_series = df[col]
                if isinstance(col_series, pd.DataFrame):
                    col_series = col_series.iloc[:, 0]
                nullable = bool(col_series.isna().any())
            except Exception:
                nullable = True
            
            col_def = {
                'name': col,
                'type': self._infer_column_type(df[col] if isinstance(df[col], pd.Series) else df[col].iloc[:, 0]),
                'nullable': nullable,
                'unique_values': int(df[col].nunique() if isinstance(df[col], pd.Series) else df[col].iloc[:, 0].nunique()),
                'example_values': example_vals_clean
            }
            
            # Categorize column
            category = self._categorize_column(col)
            col_def['category'] = category
            
            if category not in categories:
                categories[category] = []
            categories[category].append(col)
            
            # Add numeric stats for numeric columns (convert to Python float)
            if col_def['type'] in ['integer', 'numeric']:
                try:
                    col_series = df[col]
                    if isinstance(col_series, pd.DataFrame):
                        col_series = col_series.iloc[:, 0]
                    
                    if not col_series.isna().all():
                        col_def['min'] = self._convert_to_python_type(col_series.min())
                        col_def['max'] = self._convert_to_python_type(col_series.max())
                        col_def['mean'] = self._convert_to_python_type(col_series.mean())
                    else:
                        col_def['min'] = None
                        col_def['max'] = None
                        col_def['mean'] = None
                except Exception:
                    col_def['min'] = None
                    col_def['max'] = None
                    col_def['mean'] = None
            
            columns.append(col_def)
        
        return {
            'version': '1.0',
            'dataset_type': dataset_type,
            'columns': columns,
            'categories': categories,
            'total_columns': len(columns),
            'detected_at': datetime.now().isoformat()
        }
    
    def _infer_column_type(self, series: pd.Series) -> str:
        """Infer column data type"""
        if pd.api.types.is_integer_dtype(series):
            return 'integer'
        elif pd.api.types.is_float_dtype(series):
            return 'numeric'
        elif pd.api.types.is_datetime64_any_dtype(series):
            return 'datetime'
        elif pd.api.types.is_bool_dtype(series):
            return 'boolean'
        else:
            return 'string'
    
    def _categorize_column(self, col_name: str) -> str:
        """
        Categorize column based on name patterns
        
        Common patterns:
        - patient_id, record_id, id → identifier
        - age, gender, ethnicity → demographics
        - diagnosis_date, visit_date → clinical
        - ANA, Anti-dsDNA, C3, IL-6 → lab_results
        """
        col_lower = col_name.lower()
        
        if any(word in col_lower for word in ['id', 'record', 'patient']):
            return 'identifier'
        elif any(word in col_lower for word in ['age', 'gender', 'sex', 'ethnicity', 'race']):
            return 'demographics'
        elif any(word in col_lower for word in ['date', 'time', 'duration', 'year']):
            return 'temporal'
        elif any(word in col_lower for word in ['diagnosis', 'medication', 'treatment', 'symptom']):
            return 'clinical'
        elif any(word in col_lower for word in ['il', 'tnf', 'ifn', 'ana', 'anti', 'c3', 'c4', 'esr', 'crp', 'wbc', 'hb', 'platelet']):
            return 'lab_results'
        else:
            return 'other'
    
    def _validate_row(self, row_data: Dict, schema: Dict) -> Optional[Dict[str, str]]:
        """
        Validate row data against schema
        
        Args:
            row_data: Row data as dict
            schema: Schema definition
        
        Returns:
            Dict of validation errors (field_name: error_message), or None if valid
        """
        errors = {}
        
        for col_def in schema.get('columns', []):
            field_name = col_def['name']
            value = row_data.get(field_name)
            
            # Check required fields
            if not col_def.get('nullable', True) and value is None:
                errors[field_name] = 'Required field is missing'
            
            # Type validation
            if value is not None:
                col_type = col_def['type']
                
                if col_type == 'integer':
                    if not isinstance(value, int):
                        try:
                            int(value)
                        except (ValueError, TypeError):
                            errors[field_name] = 'Must be an integer'
                
                elif col_type == 'numeric':
                    if not isinstance(value, (int, float)):
                        try:
                            float(value)
                        except (ValueError, TypeError):
                            errors[field_name] = 'Must be a number'
                
                # Range validation for numeric fields
                if col_type in ['integer', 'numeric'] and isinstance(value, (int, float)):
                    if 'min' in col_def and value < col_def['min']:
                        errors[field_name] = f"Value below minimum ({col_def['min']})"
                    if 'max' in col_def and value > col_def['max']:
                        errors[field_name] = f"Value above maximum ({col_def['max']})"
        
        return errors if errors else None
    
    def _register_schema(self, dataset_type: str, schema: Dict, dataset_name: Optional[str] = None):
        """Register or update dataset schema"""
        existing = self.db.query(DatasetSchema).filter(
            DatasetSchema.dataset_type == dataset_type
        ).first()
        
        if existing:
            # Update existing schema
            existing.schema_definition = schema
            existing.last_import_date = datetime.now()
            existing.updated_at = datetime.now()
        else:
            # Create new schema
            new_schema = DatasetSchema(
                dataset_type=dataset_type,
                dataset_name=dataset_name or dataset_type,
                schema_definition=schema,
                created_by=self.user_id,
                last_import_date=datetime.now()
            )
            self.db.add(new_schema)
        
        self.db.commit()
