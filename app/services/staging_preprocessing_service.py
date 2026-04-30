"""
Staging Preprocessing Service (Layer 5)
Applies DATA QUALITY operations to import_preview_staging JSONB data
Connects Data Pipeline → Layer 5 Data Quality → flexible_dataset_wide → ML Pipeline

IMPORTANT: Layer 5 focuses on DATA QUALITY, not ML preprocessing
- Missing values: Handle/cap (user choice)
- Duplicates: Remove
- Outliers: Detect and cap (not remove rows)
- Quality reports: Identify issues

ML-SPECIFIC preprocessing (scaling, encoding, feature selection) happens in ML pipeline:
- StandardScaler/MinMaxScaler/RobustScaler → ML only
- One-hot encoding → ML only  
- LASSO feature selection → ML only
- Imputation for ML models → ML only

This prevents double preprocessing and feature distortion!
"""
from typing import Dict, List, Any, Optional
import uuid
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
import logging

from app.models.flexible_data import ImportPreviewStaging

logger = logging.getLogger(__name__)


class StagingPreprocessingService:
    """
    Apply DATA QUALITY operations to staging table JSONB data
    
    PURPOSE: Data quality and exploration (not ML preprocessing)
    - Remove duplicates
    - Handle missing values (cap, not remove)
    - Detect and cap outliers
    - Generate quality reports
    
    ML-specific preprocessing (scaling, encoding) happens in ML pipeline to avoid double preprocessing.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.preprocessing_operations = []  # Track applied operations
    
    def get_quality_report(self, session_id: uuid.UUID) -> Dict[str, Any]:
        """
        Analyze data quality for staging session
        
        Args:
            session_id: Preview session ID
        
        Returns:
            Quality metrics (missing values, duplicates, outliers)
        """
        # Load staging data
        df = self._load_staging_as_dataframe(session_id)
        
        if df.empty:
            raise ValueError(f"No data found for session {session_id}")
        
        # Calculate quality metrics
        total_cells = df.size
        missing_cells = df.isnull().sum().sum()
        
        # Identify numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Outlier detection (IQR method)
        outlier_counts = {}
        for col in numeric_cols:
            if df[col].notna().sum() > 0:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                outliers = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
                if outliers > 0:
                    outlier_counts[col] = int(outliers)
        
        # Duplicate rows
        duplicate_count = df.duplicated().sum()
        
        # Column-level missing values
        columns_with_missing = {}
        for col in df.columns:
            missing = df[col].isnull().sum()
            if missing > 0:
                columns_with_missing[col] = {
                    'count': int(missing),
                    'percentage': round(float(missing / len(df) * 100), 2)
                }
        
        # Quality score (0-100)
        missing_penalty = (missing_cells / total_cells) * 50
        duplicate_penalty = (duplicate_count / len(df)) * 30
        outlier_penalty = (len(outlier_counts) / max(len(numeric_cols), 1)) * 20
        
        quality_score = max(0, 100 - missing_penalty - duplicate_penalty - outlier_penalty)
        
        return {
            'session_id': str(session_id),
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'quality_score': round(quality_score, 1),
            'missing_values': {
                'total_cells': int(missing_cells),
                'percentage': round(float(missing_cells / total_cells * 100), 2),
                'columns_affected': len(columns_with_missing),
                'details': columns_with_missing
            },
            'duplicates': {
                'count': int(duplicate_count),
                'percentage': round(float(duplicate_count / len(df) * 100), 2)
            },
            'outliers': {
                'columns_affected': len(outlier_counts),
                'details': outlier_counts
            },
            'column_types': {
                'numeric': len(numeric_cols),
                'categorical': len(df.select_dtypes(include=['object']).columns),
                'datetime': len(df.select_dtypes(include=['datetime64']).columns)
            }
        }
    
    def get_problematic_rows(self, session_id: uuid.UUID) -> List[Dict[str, Any]]:
        """
        Get rows with data quality issues for interactive cleaning
        
        Returns actual rows with missing values, duplicates, or outliers
        including affected columns and data preview.
        
        Args:
            session_id: Preview session ID
        
        Returns:
            List of problematic rows with issue details
        """
        df = self._load_staging_as_dataframe(session_id)
        
        if df.empty:
            return []
        
        problematic_rows = []
        
        # Identify numeric columns for outlier detection
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Calculate outlier bounds
        outlier_bounds = {}
        for col in numeric_cols:
            if df[col].notna().sum() > 0:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                outlier_bounds[col] = {
                    'lower': Q1 - 1.5 * IQR,
                    'upper': Q3 + 1.5 * IQR
                }
        
        # Identify duplicate rows
        duplicate_mask = df.duplicated(keep=False)
        
        # Process each row
        for idx, row in df.iterrows():
            issues = []
            
            # Check for missing values
            missing_cols = [col for col in df.columns if pd.isna(row[col])]
            if missing_cols:
                for col in missing_cols:
                    issues.append({
                        'type': 'missing',
                        'column': col,
                        'severity': 'high' if len(missing_cols) > len(df.columns) * 0.3 else 'medium'
                    })
            
            # Check for duplicates
            if duplicate_mask[idx]:
                issues.append({
                    'type': 'duplicate',
                    'column': None,
                    'severity': 'medium'
                })
            
            # Check for outliers
            for col in numeric_cols:
                if col in outlier_bounds and pd.notna(row[col]):
                    value = row[col]
                    bounds = outlier_bounds[col]
                    if value < bounds['lower'] or value > bounds['upper']:
                        issues.append({
                            'type': 'outlier',
                            'column': col,
                            'severity': 'high' if abs(value - bounds['upper']) > 3 * (bounds['upper'] - bounds['lower']) else 'medium'
                        })
            
            # Add row if it has issues
            if issues:
                # Convert row to dict, handling NaN and datetime
                row_dict = {}
                for col, val in row.items():
                    if pd.isna(val):
                        row_dict[col] = None
                    elif isinstance(val, (pd.Timestamp, datetime)):
                        row_dict[col] = val.isoformat()
                    elif isinstance(val, (np.integer, np.floating)):
                        row_dict[col] = float(val)
                    else:
                        row_dict[col] = val
                
                problematic_rows.append({
                    'row_id': int(idx),
                    'row_number': int(idx) + 1,
                    'issues': issues,
                    'data_preview': row_dict
                })
        
        return problematic_rows
    
    def clean_selected_rows(
        self,
        session_id: uuid.UUID,
        row_ids: List[int],
        method: str = 'median',
        outlier_method: str = 'cap'
    ) -> Dict[str, Any]:
        """
        Clean selected rows based on user selection
        
        Applies targeted cleaning operations only to specified rows.
        
        Args:
            session_id: Preview session ID
            row_ids: List of row indices to clean
            method: Method for handling missing values ('mean', 'median', 'mode', 'drop')
            outlier_method: Method for handling outliers ('cap', 'remove')
        
        Returns:
            Operation summary
        """
        df = self._load_staging_as_dataframe(session_id)
        
        if df.empty:
            raise ValueError(f"No data found for session {session_id}")
        
        changes = []
        rows_cleaned = 0
        
        # Identify numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Calculate outlier bounds
        outlier_bounds = {}
        for col in numeric_cols:
            if df[col].notna().sum() > 0:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                outlier_bounds[col] = {
                    'lower': Q1 - 1.5 * IQR,
                    'upper': Q3 + 1.5 * IQR
                }
        
        # Process each selected row
        for row_id in row_ids:
            if row_id not in df.index:
                continue
            
            row_changed = False
            
            # Handle missing values
            for col in df.columns:
                if pd.isna(df.loc[row_id, col]):
                    if method == 'drop':
                        df = df.drop(row_id)
                        changes.append(f"Removed row {row_id} with missing values")
                        row_changed = True
                        break
                    
                    elif method in ['mean', 'median', 'mode']:
                        if df[col].dtype in ['int64', 'float64']:
                            if method == 'mean':
                                fill_value = df[col].mean()
                            elif method == 'median':
                                fill_value = df[col].median()
                            else:  # mode
                                mode_val = df[col].mode()
                                fill_value = mode_val[0] if len(mode_val) > 0 else df[col].median()
                        else:
                            mode_val = df[col].mode()
                            fill_value = mode_val[0] if len(mode_val) > 0 else 'Unknown'
                        
                        df.loc[row_id, col] = fill_value
                        changes.append(f"Filled {col} in row {row_id} with {method}: {fill_value}")
                        row_changed = True
            
            # Handle outliers
            for col in numeric_cols:
                if col in outlier_bounds and pd.notna(df.loc[row_id, col]):
                    value = df.loc[row_id, col]
                    bounds = outlier_bounds[col]
                    
                    if value < bounds['lower'] or value > bounds['upper']:
                        if outlier_method == 'cap':
                            new_value = bounds['lower'] if value < bounds['lower'] else bounds['upper']
                            df.loc[row_id, col] = new_value
                            changes.append(f"Capped {col} in row {row_id}: {value} → {new_value}")
                            row_changed = True
                        elif outlier_method == 'remove':
                            df = df.drop(row_id)
                            changes.append(f"Removed row {row_id} with outlier in {col}")
                            row_changed = True
                            break
            
            if row_changed:
                rows_cleaned += 1
        
        # Save back to staging
        self._update_staging_from_dataframe(session_id, df)
        
        return {
            'rows_cleaned': rows_cleaned,
            'total_selected': len(row_ids),
            'summary': '\n'.join(changes[:10]) + (f'\n...and {len(changes) - 10} more changes' if len(changes) > 10 else '')
        }
    
    def aggregate_patient_records(
        self,
        session_id: uuid.UUID,
        patient_id_column: str = 'patient_id',
        aggregation_strategy: str = 'latest'
    ) -> Dict[str, Any]:
        """
        Consolidate multiple rows for same patient into single comprehensive record
        
        PURPOSE: Patient-level deduplication (Layer 5 - Data Quality)
        - Identifies duplicate patient records
        - Merges them based on strategy (latest, most_complete, etc.)
        - Preserves most relevant information
        
        Args:
            session_id: Preview session ID
            patient_id_column: Column name containing patient identifier
            aggregation_strategy: How to merge records
                - 'latest': Keep most recent record (by timestamp/date columns)
                - 'most_complete': Keep record with fewest missing values
                - 'merge': Combine non-null values from all records
        
        Returns:
            Aggregation report with before/after stats
        """
        df = self._load_staging_as_dataframe(session_id)
        
        if df.empty:
            raise ValueError(f"No data found for session {session_id}")
        
        # Check if patient ID column exists
        if patient_id_column not in df.columns:
            raise ValueError(f"Patient ID column '{patient_id_column}' not found. Available columns: {list(df.columns)}")
        
        # Track before stats
        before_rows = len(df)
        before_patients = df[patient_id_column].nunique()
        
        # Find duplicate patients
        duplicate_patients = df[patient_id_column].value_counts()
        duplicate_patients = duplicate_patients[duplicate_patients > 1]
        
        if len(duplicate_patients) == 0:
            return {
                'success': True,
                'operation': 'patient_aggregation',
                'message': 'No duplicate patient records found',
                'before_rows': before_rows,
                'after_rows': before_rows,
                'patients_consolidated': 0
            }
        
        logger.info(f"Found {len(duplicate_patients)} patients with duplicate records")
        
        # Apply aggregation strategy
        if aggregation_strategy == 'latest':
            df_aggregated = self._aggregate_latest(df, patient_id_column)
        elif aggregation_strategy == 'most_complete':
            df_aggregated = self._aggregate_most_complete(df, patient_id_column)
        elif aggregation_strategy == 'merge':
            df_aggregated = self._aggregate_merge(df, patient_id_column)
        else:
            raise ValueError(f"Unknown aggregation strategy: {aggregation_strategy}")
        
        # Track after stats
        after_rows = len(df_aggregated)
        after_patients = df_aggregated[patient_id_column].nunique()
        rows_removed = before_rows - after_rows
        
        # Update staging
        self._update_staging_from_dataframe(session_id, df_aggregated)
        
        # Track operation
        self.preprocessing_operations.append({
            'operation': 'patient_aggregation',
            'strategy': aggregation_strategy,
            'timestamp': datetime.now().isoformat(),
            'rows_removed': rows_removed
        })
        
        return {
            'success': True,
            'operation': 'patient_aggregation',
            'strategy': aggregation_strategy,
            'before_rows': before_rows,
            'after_rows': after_rows,
            'rows_removed': rows_removed,
            'before_patients': before_patients,
            'after_patients': after_patients,
            'patients_consolidated': len(duplicate_patients),
            'message': f'Consolidated {len(duplicate_patients)} patients with duplicate records. Removed {rows_removed} duplicate rows.'
        }
    
    def _aggregate_latest(self, df: pd.DataFrame, patient_id_col: str) -> pd.DataFrame:
        """Keep most recent record per patient (by date columns)"""
        # Find date/timestamp columns
        date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
        
        if not date_cols:
            # Try to infer from column names
            potential_date_cols = [col for col in df.columns if any(x in col.lower() for x in ['date', 'time', 'visit', 'created'])]
            if potential_date_cols:
                # Convert to datetime if possible
                for col in potential_date_cols:
                    try:
                        df[col] = pd.to_datetime(df[col])
                        date_cols.append(col)
                    except:
                        pass
        
        if date_cols:
            # Sort by patient ID and most recent date
            df_sorted = df.sort_values([patient_id_col] + [date_cols[0]], ascending=[True, False])
            # Keep first (most recent) record per patient
            return df_sorted.drop_duplicates(subset=[patient_id_col], keep='first').reset_index(drop=True)
        else:
            # No date columns, just keep first occurrence
            logger.warning("No date columns found, keeping first occurrence per patient")
            return df.drop_duplicates(subset=[patient_id_col], keep='first').reset_index(drop=True)
    
    def _aggregate_most_complete(self, df: pd.DataFrame, patient_id_col: str) -> pd.DataFrame:
        """Keep record with fewest missing values per patient"""
        # Calculate completeness score for each row
        df['_completeness'] = df.notna().sum(axis=1)
        
        # Sort by patient ID and completeness (descending)
        df_sorted = df.sort_values([patient_id_col, '_completeness'], ascending=[True, False])
        
        # Keep most complete record per patient
        df_aggregated = df_sorted.drop_duplicates(subset=[patient_id_col], keep='first').reset_index(drop=True)
        
        # Remove helper column
        df_aggregated = df_aggregated.drop(columns=['_completeness'])
        
        return df_aggregated
    
    def _aggregate_merge(self, df: pd.DataFrame, patient_id_col: str) -> pd.DataFrame:
        """Merge all records per patient, filling nulls with non-null values"""
        aggregated_records = []
        
        for patient_id in df[patient_id_col].unique():
            patient_rows = df[df[patient_id_col] == patient_id]
            
            if len(patient_rows) == 1:
                # Single record, keep as is
                aggregated_records.append(patient_rows.iloc[0].to_dict())
            else:
                # Multiple records, merge
                merged_record = {}
                for col in df.columns:
                    # Get all non-null values for this column
                    non_null_values = patient_rows[col].dropna()
                    
                    if len(non_null_values) == 0:
                        merged_record[col] = None
                    elif len(non_null_values) == 1:
                        merged_record[col] = non_null_values.iloc[0]
                    else:
                        # Multiple non-null values - take most recent or most common
                        if col == patient_id_col:
                            merged_record[col] = patient_id  # Keep patient ID
                        else:
                            # For numeric: take mean
                            # For categorical: take mode (most common)
                            if pd.api.types.is_numeric_dtype(non_null_values):
                                merged_record[col] = non_null_values.mean()
                            else:
                                merged_record[col] = non_null_values.mode().iloc[0] if len(non_null_values.mode()) > 0 else non_null_values.iloc[0]
                
                aggregated_records.append(merged_record)
        
        return pd.DataFrame(aggregated_records).reset_index(drop=True)
    
    def handle_missing_values(
        self,
        session_id: uuid.UUID,
        method: str = 'mean',
        threshold: float = 0.5,
        columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Handle missing values in staging data
        
        Args:
            session_id: Preview session ID
            method: 'mean', 'median', 'mode', 'ffill', 'bfill', 'drop'
            threshold: Drop columns with missing % above this (0.0-1.0)
            columns: Specific columns to process (None = all)
        
        Returns:
            Operation report with before/after stats
        """
        df = self._load_staging_as_dataframe(session_id)
        df_original = df.copy()
        
        # Track changes
        before_missing = df.isnull().sum().sum()
        before_rows = len(df)
        before_cols = len(df.columns)
        
        # Drop columns with too many missing values
        cols_to_drop = []
        for col in df.columns:
            missing_pct = df[col].isnull().sum() / len(df)
            if missing_pct > threshold:
                cols_to_drop.append(col)
        
        if cols_to_drop:
            df = df.drop(columns=cols_to_drop)
            logger.info(f"Dropped {len(cols_to_drop)} columns exceeding threshold: {cols_to_drop}")
        
        # Filter columns to process
        if columns:
            cols_to_process = [col for col in columns if col in df.columns]
        else:
            cols_to_process = df.columns.tolist()
        
        # Apply imputation method
        if method == 'drop':
            df = df.dropna(subset=cols_to_process)
        
        elif method in ['mean', 'median', 'mode']:
            for col in cols_to_process:
                if df[col].isnull().sum() == 0:
                    continue
                
                if df[col].dtype in ['int64', 'float64']:
                    if method == 'mean':
                        df[col].fillna(df[col].mean(), inplace=True)
                    elif method == 'median':
                        df[col].fillna(df[col].median(), inplace=True)
                    elif method == 'mode':
                        mode_val = df[col].mode()
                        if len(mode_val) > 0:
                            df[col].fillna(mode_val[0], inplace=True)
                else:  # Categorical
                    mode_val = df[col].mode()
                    if len(mode_val) > 0:
                        df[col].fillna(mode_val[0], inplace=True)
        
        elif method == 'ffill':
            df[cols_to_process] = df[cols_to_process].fillna(method='ffill')
        
        elif method == 'bfill':
            df[cols_to_process] = df[cols_to_process].fillna(method='bfill')
        
        # Calculate after stats
        after_missing = df.isnull().sum().sum()
        after_rows = len(df)
        after_cols = len(df.columns)
        
        # Update staging table with preprocessed data
        self._update_staging_from_dataframe(session_id, df)
        
        # Track operation for metadata
        self.preprocessing_operations.append({
            'operation': 'missing_values',
            'method': method,
            'threshold': threshold,
            'timestamp': datetime.now().isoformat(),
            'cells_imputed': int(before_missing - after_missing),
            'rows_removed': before_rows - after_rows,
            'columns_dropped': len(cols_to_drop)
        })
        
        return {
            'success': True,
            'operation': 'handle_missing_values',
            'method': method,
            'threshold': threshold,
            'before': {
                'rows': before_rows,
                'columns': before_cols,
                'missing_cells': int(before_missing)
            },
            'after': {
                'rows': after_rows,
                'columns': after_cols,
                'missing_cells': int(after_missing)
            },
            'changes': {
                'rows_removed': before_rows - after_rows,
                'columns_dropped': len(cols_to_drop),
                'dropped_columns': cols_to_drop,
                'cells_imputed': int(before_missing - after_missing)
            }
        }
    
    def remove_duplicates(
        self,
        session_id: uuid.UUID,
        keep_first: bool = True
    ) -> Dict[str, Any]:
        """
        Remove duplicate rows from staging data
        
        Args:
            session_id: Preview session ID
            keep_first: Keep first occurrence (True) or last (False)
        
        Returns:
            Operation report
        """
        df = self._load_staging_as_dataframe(session_id)
        
        before_rows = len(df)
        duplicate_count = df.duplicated(keep=False).sum()
        
        # Remove duplicates
        keep_option = 'first' if keep_first else 'last'
        df = df.drop_duplicates(keep=keep_option)
        
        after_rows = len(df)
        
        # Update staging
        self._update_staging_from_dataframe(session_id, df)
        
        # Track operation
        self.preprocessing_operations.append({
            'operation': 'duplicates',
            'keep_first': keep_first,
            'timestamp': datetime.now().isoformat(),
            'duplicates_removed': before_rows - after_rows
        })
        
        return {
            'success': True,
            'operation': 'remove_duplicates',
            'keep_first': keep_first,
            'before_rows': before_rows,
            'after_rows': after_rows,
            'duplicates_removed': before_rows - after_rows,
            'duplicate_groups': int(duplicate_count)
        }
    
    def handle_outliers(
        self,
        session_id: uuid.UUID,
        method: str = 'iqr',
        threshold: float = 1.5,
        columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Detect and handle outliers
        
        Args:
            session_id: Preview session ID
            method: 'iqr' or 'zscore'
            threshold: IQR multiplier (1.5=mild, 3=extreme) or Z-score value
            columns: Specific columns (None = all numeric)
        
        Returns:
            Operation report
        """
        df = self._load_staging_as_dataframe(session_id)
        
        # Get numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if columns:
            numeric_cols = [col for col in columns if col in numeric_cols]
        
        outliers_detected = {}
        outliers_removed = 0
        
        for col in numeric_cols:
            if df[col].notna().sum() == 0:
                continue
            
            if method == 'iqr':
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - threshold * IQR
                upper_bound = Q3 + threshold * IQR
                
                outlier_mask = (df[col] < lower_bound) | (df[col] > upper_bound)
                
            elif method == 'zscore':
                mean = df[col].mean()
                std = df[col].std()
                z_scores = np.abs((df[col] - mean) / std)
                outlier_mask = z_scores > threshold
            
            else:
                raise ValueError(f"Unknown outlier method: {method}")
            
            outlier_count = outlier_mask.sum()
            if outlier_count > 0:
                outliers_detected[col] = int(outlier_count)
                # Cap outliers instead of removing rows
                if method == 'iqr':
                    df.loc[df[col] < lower_bound, col] = lower_bound
                    df.loc[df[col] > upper_bound, col] = upper_bound
                outliers_removed += outlier_count
        
        # Update staging
        self._update_staging_from_dataframe(session_id, df)
        
        # Track operation
        self.preprocessing_operations.append({
            'operation': 'outliers',
            'method': method,
            'threshold': threshold,
            'timestamp': datetime.now().isoformat(),
            'outliers_capped': outliers_removed,
            'columns_processed': len(numeric_cols)
        })
        
        return {
            'success': True,
            'operation': 'handle_outliers',
            'method': method,
            'threshold': threshold,
            'outliers_detected': outliers_detected,
            'outliers_capped': outliers_removed,
            'columns_processed': len(numeric_cols)
        }
    
    def normalize_data(
        self,
        session_id: uuid.UUID,
        method: str = 'standard',
        columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        ⚠️ DEPRECATED - NOT RECOMMENDED FOR ML PREPROCESSING
        
        Normalize numeric columns (z-score, min-max, robust scaling)
        
        WARNING: This creates DOUBLE PREPROCESSING risk!
        - Layer 5 normalization → ML pipeline normalization again → Features distorted
        - ML pipeline already handles StandardScaler/MinMaxScaler/RobustScaler
        
        RECOMMENDED APPROACH:
        - Layer 5: Data quality only (duplicates, outliers, missing values)
        - ML Pipeline: Handles all scaling/normalization with fitted scalers
        
        Use this ONLY for data exploration/visualization, NOT for ML training.
        
        Args:
            session_id: Preview session ID
            method: 'standard' (z-score), 'minmax' (0-1), 'robust' (median/IQR)
            columns: Specific columns (None = all numeric)
        
        Returns:
            Operation report
        """
        logger.warning(
            "⚠️ normalize_data() called - NOT recommended for ML preprocessing! "
            "ML pipeline handles scaling to prevent double preprocessing."
        )
        df = self._load_staging_as_dataframe(session_id)
        
        # Get numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if columns:
            numeric_cols = [col for col in columns if col in numeric_cols]
        
        # Store original ranges for report
        original_ranges = {}
        for col in numeric_cols:
            if df[col].notna().sum() > 0:
                original_ranges[col] = {
                    'min': float(df[col].min()),
                    'max': float(df[col].max()),
                    'mean': float(df[col].mean()),
                    'std': float(df[col].std())
                }
        
        # Apply normalization
        if method == 'standard':
            # Z-score: (x - mean) / std
            for col in numeric_cols:
                if df[col].notna().sum() > 1:
                    mean = df[col].mean()
                    std = df[col].std()
                    if std > 0:
                        df[col] = (df[col] - mean) / std
        
        elif method == 'minmax':
            # Min-Max: (x - min) / (max - min)
            for col in numeric_cols:
                if df[col].notna().sum() > 1:
                    min_val = df[col].min()
                    max_val = df[col].max()
                    if max_val > min_val:
                        df[col] = (df[col] - min_val) / (max_val - min_val)
        
        elif method == 'robust':
            # Robust: (x - median) / IQR
            for col in numeric_cols:
                if df[col].notna().sum() > 1:
                    median = df[col].median()
                    Q1 = df[col].quantile(0.25)
                    Q3 = df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    if IQR > 0:
                        df[col] = (df[col] - median) / IQR
        
        else:
            raise ValueError(f"Unknown normalization method: {method}")
        
        # Update staging
        self._update_staging_from_dataframe(session_id, df)
        
        # Track operation
        self.preprocessing_operations.append({
            'operation': 'normalization',
            'method': method,
            'timestamp': datetime.now().isoformat(),
            'columns_normalized': numeric_cols
        })
        
        # Calculate new ranges
        normalized_ranges = {}
        for col in numeric_cols:
            if df[col].notna().sum() > 0:
                normalized_ranges[col] = {
                    'min': float(df[col].min()),
                    'max': float(df[col].max()),
                    'mean': float(df[col].mean()),
                    'std': float(df[col].std())
                }
        
        return {
            'success': True,
            'operation': 'normalize_data',
            'method': method,
            'columns_normalized': numeric_cols,
            'original_ranges': original_ranges,
            'normalized_ranges': normalized_ranges
        }
    
    def get_before_after_preview(
        self,
        session_id: uuid.UUID,
        rows: int = 20
    ) -> Dict[str, Any]:
        """
        Get preview of staging data for before/after comparison
        
        Args:
            session_id: Preview session ID
            rows: Number of rows to return
        
        Returns:
            Preview data with stats
        """
        df = self._load_staging_as_dataframe(session_id)
        
        # Get preview rows
        preview_data = df.head(rows).to_dict(orient='records')
        
        # Convert NaN to None for JSON
        for record in preview_data:
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None
        
        return {
            'session_id': str(session_id),
            'total_rows': len(df),
            'preview_rows': len(preview_data),
            'columns': df.columns.tolist(),
            'data': preview_data,
            'stats': {
                'missing_cells': int(df.isnull().sum().sum()),
                'duplicate_rows': int(df.duplicated().sum()),
                'numeric_columns': len(df.select_dtypes(include=[np.number]).columns)
            }
        }
    
    def get_preprocessing_metadata(self) -> Dict[str, Any]:
        """
        Get preprocessing metadata to attach to saved records
        
        Returns:
            Metadata dict with all operations applied and their details
        """
        return {
            'layer_5': True,
            'applied_at': datetime.now().isoformat(),
            'operations': [op['operation'] for op in self.preprocessing_operations],
            'operation_details': self.preprocessing_operations,
            'total_operations': len(self.preprocessing_operations)
        }
    
    # ============================================
    # HELPER METHODS
    # ============================================
    
    def _load_staging_as_dataframe(self, session_id: uuid.UUID) -> pd.DataFrame:
        """
        Load staging records as pandas DataFrame
        
        Args:
            session_id: Preview session ID
        
        Returns:
            DataFrame with row_data JSONB flattened
        """
        records = self.db.query(ImportPreviewStaging).filter(
            and_(
                ImportPreviewStaging.session_id == session_id,
                ImportPreviewStaging.is_deleted == False
            )
        ).order_by(ImportPreviewStaging.row_number).all()
        
        if not records:
            return pd.DataFrame()
        
        # Extract row_data JSONB to list of dicts
        rows = [record.row_data for record in records]
        
        # Convert to DataFrame
        df = pd.DataFrame(rows)
        
        return df
    
    def _update_staging_from_dataframe(
        self,
        session_id: uuid.UUID,
        df: pd.DataFrame
    ) -> None:
        """
        Update staging table with preprocessed DataFrame
        
        Args:
            session_id: Preview session ID
            df: Preprocessed DataFrame
        """
        # Delete old records
        self.db.query(ImportPreviewStaging).filter(
            ImportPreviewStaging.session_id == session_id
        ).delete()
        
        # Insert new records
        for idx, row in df.iterrows():
            # Convert row to dict, handle NaN
            row_dict = row.to_dict()
            for key, value in row_dict.items():
                if pd.isna(value):
                    row_dict[key] = None
            
            # Get original record to preserve metadata
            staging_record = ImportPreviewStaging(
                session_id=session_id,
                dataset_type='preprocessed',
                dataset_name=f'Preprocessed Session {session_id}',
                row_data=row_dict,
                row_number=int(idx) + 1,
                is_edited=True,  # Mark as edited
                validation_status='valid',
                created_at=datetime.now()
            )
            
            self.db.add(staging_record)
        
        self.db.commit()
        logger.info(f"Updated {len(df)} rows in staging for session {session_id}")
