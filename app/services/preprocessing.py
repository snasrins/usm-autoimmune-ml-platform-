"""
Data Preprocessing Service
Handles missing values, encoding, normalization, and outlier detection
USMA-22, USMA-24, USMA-25, USMA-23
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder, OneHotEncoder
from sklearn.impute import SimpleImputer
from typing import Dict, List, Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)


class DataPreprocessor:
    """
    Automated data preprocessing pipeline
    Handles missing values, encoding, normalization, and outlier detection
    """
    
    def __init__(self):
        self.preprocessing_history = []
        self.scalers = {}
        self.encoders = {}
        
    def analyze_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        USMA-26: Analyze data quality metrics
        Returns comprehensive data quality report
        """
        report = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "total_cells": df.size,
            "memory_usage_mb": round(df.memory_usage(deep=True).sum() / 1024**2, 2),
            
            # Missing values analysis
            "missing_values": {
                "total_missing": int(df.isnull().sum().sum()),
                "missing_percentage": round(df.isnull().sum().sum() / df.size * 100, 2),
                "columns_with_missing": {},
                "rows_with_missing": int(df.isnull().any(axis=1).sum())
            },
            
            # Duplicate rows
            "duplicates": {
                "duplicate_rows": int(df.duplicated().sum()),
                "duplicate_percentage": round(df.duplicated().sum() / len(df) * 100, 2)
            },
            
            # Data types
            "data_types": {
                "numeric_columns": list(df.select_dtypes(include=['int64', 'float64']).columns),
                "categorical_columns": list(df.select_dtypes(include=['object', 'category']).columns),
                "datetime_columns": list(df.select_dtypes(include=['datetime64']).columns),
                "boolean_columns": list(df.select_dtypes(include=['bool']).columns)
            },
            
            # Column details
            "column_info": []
        }
        
        # Missing values per column
        for col in df.columns:
            missing_count = int(df[col].isnull().sum())
            if missing_count > 0:
                report["missing_values"]["columns_with_missing"][col] = {
                    "count": missing_count,
                    "percentage": round(missing_count / len(df) * 100, 2)
                }
        
        # Column-level information
        for col in df.columns:
            col_info = {
                "name": col,
                "dtype": str(df[col].dtype),
                "non_null_count": int(df[col].count()),
                "null_count": int(df[col].isnull().sum()),
                "unique_count": int(df[col].nunique()),
                "unique_ratio": round(df[col].nunique() / len(df) * 100, 2)
            }
            
            # Add stats for numeric columns
            if df[col].dtype in ['int64', 'float64']:
                col_info.update({
                    "mean": float(df[col].mean()) if not df[col].isnull().all() else None,
                    "median": float(df[col].median()) if not df[col].isnull().all() else None,
                    "std": float(df[col].std()) if not df[col].isnull().all() else None,
                    "min": float(df[col].min()) if not df[col].isnull().all() else None,
                    "max": float(df[col].max()) if not df[col].isnull().all() else None,
                    "q25": float(df[col].quantile(0.25)) if not df[col].isnull().all() else None,
                    "q75": float(df[col].quantile(0.75)) if not df[col].isnull().all() else None,
                })
            
            # Add sample values
            col_info["sample_values"] = df[col].dropna().head(5).tolist()
            
            report["column_info"].append(col_info)
        
        return report
    
    def handle_missing_values(
        self, 
        df: pd.DataFrame, 
        strategy: Dict[str, str] = None,
        threshold: float = 0.5
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        USMA-22: Handle missing values
        
        Args:
            df: Input dataframe
            strategy: Dict mapping column names to strategies
                     Options: 'mean', 'median', 'mode', 'ffill', 'bfill', 'drop', 'constant'
            threshold: Drop columns with missing % above threshold
        
        Returns:
            Processed dataframe and processing report
        """
        df_processed = df.copy()
        report = {
            "action": "missing_value_handling",
            "columns_dropped": [],
            "imputation_performed": {},
            "rows_dropped": 0
        }
        
        # Drop columns with too many missing values
        missing_pct = df_processed.isnull().sum() / len(df_processed)
        cols_to_drop = missing_pct[missing_pct > threshold].index.tolist()
        
        if cols_to_drop:
            df_processed = df_processed.drop(columns=cols_to_drop)
            report["columns_dropped"] = cols_to_drop
            logger.info(f"Dropped {len(cols_to_drop)} columns with >{threshold*100}% missing values")
        
        # Apply imputation strategies
        if strategy is None:
            # Auto strategy: mean for numeric, mode for categorical
            strategy = {}
            for col in df_processed.columns:
                if df_processed[col].dtype in ['int64', 'float64']:
                    strategy[col] = 'median'
                else:
                    strategy[col] = 'mode'
        
        for col, strat in strategy.items():
            if col not in df_processed.columns:
                continue
            
            missing_before = int(df_processed[col].isnull().sum())
            if missing_before == 0:
                continue
            
            if strat == 'mean':
                fill_value = df_processed[col].mean()
                df_processed[col].fillna(fill_value, inplace=True)
            elif strat == 'median':
                fill_value = df_processed[col].median()
                df_processed[col].fillna(fill_value, inplace=True)
            elif strat == 'mode':
                fill_value = df_processed[col].mode()[0] if not df_processed[col].mode().empty else None
                if fill_value is not None:
                    df_processed[col].fillna(fill_value, inplace=True)
            elif strat == 'ffill':
                df_processed[col].fillna(method='ffill', inplace=True)
            elif strat == 'bfill':
                df_processed[col].fillna(method='bfill', inplace=True)
            elif strat == 'drop':
                rows_before = len(df_processed)
                df_processed = df_processed.dropna(subset=[col])
                report["rows_dropped"] += rows_before - len(df_processed)
            elif isinstance(strat, (int, float, str)):
                # Constant value
                df_processed[col].fillna(strat, inplace=True)
            
            missing_after = int(df_processed[col].isnull().sum())
            report["imputation_performed"][col] = {
                "strategy": strat,
                "missing_before": missing_before,
                "missing_after": missing_after,
                "imputed_count": missing_before - missing_after
            }
        
        self.preprocessing_history.append(report)
        return df_processed, report
    
    def encode_categorical_variables(
        self, 
        df: pd.DataFrame,
        encoding_type: str = 'auto',
        columns: List[str] = None
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        USMA-24: Encode categorical variables
        
        Args:
            df: Input dataframe
            encoding_type: 'label', 'onehot', 'auto'
            columns: Specific columns to encode (None = all categorical)
        
        Returns:
            Encoded dataframe and encoding report
        """
        df_processed = df.copy()
        report = {
            "action": "categorical_encoding",
            "encoding_performed": {}
        }
        
        # Identify categorical columns
        if columns is None:
            columns = df_processed.select_dtypes(include=['object', 'category']).columns.tolist()
        
        for col in columns:
            if col not in df_processed.columns:
                continue
            
            unique_count = df_processed[col].nunique()
            
            # Auto strategy: label encoding for ordinal, onehot for low cardinality
            if encoding_type == 'auto':
                if unique_count > 10:
                    method = 'label'
                else:
                    method = 'onehot'
            else:
                method = encoding_type
            
            if method == 'label':
                # Label encoding
                le = LabelEncoder()
                # Handle NaN values
                mask = df_processed[col].notna()
                df_processed.loc[mask, col] = le.fit_transform(df_processed.loc[mask, col].astype(str))
                self.encoders[col] = le
                
                report["encoding_performed"][col] = {
                    "method": "label_encoding",
                    "unique_values": unique_count,
                    "mappings": dict(zip(le.classes_, le.transform(le.classes_)))
                }
            
            elif method == 'onehot':
                # One-hot encoding
                dummies = pd.get_dummies(df_processed[col], prefix=col, drop_first=True)
                df_processed = pd.concat([df_processed.drop(columns=[col]), dummies], axis=1)
                
                report["encoding_performed"][col] = {
                    "method": "onehot_encoding",
                    "unique_values": unique_count,
                    "new_columns": dummies.columns.tolist()
                }
        
        self.preprocessing_history.append(report)
        return df_processed, report
    
    def normalize_data(
        self,
        df: pd.DataFrame,
        method: str = 'standard',
        columns: List[str] = None
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        USMA-25: Normalize/standardize numeric data
        
        Args:
            df: Input dataframe
            method: 'standard' (z-score), 'minmax', 'robust'
            columns: Specific columns to normalize (None = all numeric)
        
        Returns:
            Normalized dataframe and normalization report
        """
        df_processed = df.copy()
        report = {
            "action": "normalization",
            "method": method,
            "normalization_performed": {}
        }
        
        # Identify numeric columns
        if columns is None:
            columns = df_processed.select_dtypes(include=['int64', 'float64']).columns.tolist()
        
        for col in columns:
            if col not in df_processed.columns:
                continue
            
            original_stats = {
                "mean": float(df_processed[col].mean()),
                "std": float(df_processed[col].std()),
                "min": float(df_processed[col].min()),
                "max": float(df_processed[col].max())
            }
            
            if method == 'standard':
                # Z-score standardization
                scaler = StandardScaler()
                df_processed[[col]] = scaler.fit_transform(df_processed[[col]])
                self.scalers[col] = scaler
            
            elif method == 'minmax':
                # Min-Max scaling to [0,1]
                scaler = MinMaxScaler()
                df_processed[[col]] = scaler.fit_transform(df_processed[[col]])
                self.scalers[col] = scaler
            
            elif method == 'robust':
                # Robust scaling (using median and IQR)
                from sklearn.preprocessing import RobustScaler
                scaler = RobustScaler()
                df_processed[[col]] = scaler.fit_transform(df_processed[[col]])
                self.scalers[col] = scaler
            
            normalized_stats = {
                "mean": float(df_processed[col].mean()),
                "std": float(df_processed[col].std()),
                "min": float(df_processed[col].min()),
                "max": float(df_processed[col].max())
            }
            
            report["normalization_performed"][col] = {
                "original_stats": original_stats,
                "normalized_stats": normalized_stats
            }
        
        self.preprocessing_history.append(report)
        return df_processed, report
    
    def detect_outliers(
        self,
        df: pd.DataFrame,
        method: str = 'iqr',
        columns: List[str] = None,
        threshold: float = 1.5
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        USMA-23: Detect and optionally remove outliers
        
        Args:
            df: Input dataframe
            method: 'iqr', 'z-score', 'isolation_forest'
            columns: Specific columns to check (None = all numeric)
            threshold: IQR multiplier (1.5) or z-score threshold (3)
        
        Returns:
            Outlier detection report
        """
        report = {
            "action": "outlier_detection",
            "method": method,
            "outliers_detected": {}
        }
        
        # Identify numeric columns
        if columns is None:
            columns = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        
        outlier_mask = pd.Series([False] * len(df), index=df.index)
        
        for col in columns:
            if col not in df.columns:
                continue
            
            col_outliers = pd.Series([False] * len(df), index=df.index)
            
            if method == 'iqr':
                # IQR method
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - threshold * IQR
                upper_bound = Q3 + threshold * IQR
                
                col_outliers = (df[col] < lower_bound) | (df[col] > upper_bound)
                
                report["outliers_detected"][col] = {
                    "outlier_count": int(col_outliers.sum()),
                    "outlier_percentage": round(col_outliers.sum() / len(df) * 100, 2),
                    "lower_bound": float(lower_bound),
                    "upper_bound": float(upper_bound),
                    "outlier_indices": df[col_outliers].index.tolist()[:100]  # Limit to 100
                }
            
            elif method == 'z-score':
                # Z-score method
                z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                col_outliers = z_scores > threshold
                
                report["outliers_detected"][col] = {
                    "outlier_count": int(col_outliers.sum()),
                    "outlier_percentage": round(col_outliers.sum() / len(df) * 100, 2),
                    "z_threshold": threshold,
                    "outlier_indices": df[col_outliers].index.tolist()[:100]
                }
            
            outlier_mask = outlier_mask | col_outliers
        
        report["total_outlier_rows"] = int(outlier_mask.sum())
        report["total_outlier_percentage"] = round(outlier_mask.sum() / len(df) * 100, 2)
        
        self.preprocessing_history.append(report)
        return df, report
    
    def remove_outliers(self, df: pd.DataFrame, outlier_report: Dict) -> pd.DataFrame:
        """Remove rows identified as outliers"""
        all_outlier_indices = set()
        for col_report in outlier_report["outliers_detected"].values():
            all_outlier_indices.update(col_report["outlier_indices"])
        
        df_clean = df.drop(index=list(all_outlier_indices))
        logger.info(f"Removed {len(all_outlier_indices)} outlier rows")
        return df_clean
    
    def winsorize_outliers(
        self,
        df: pd.DataFrame,
        lower_percentile: float = 0.01,
        upper_percentile: float = 0.99,
        columns: List[str] = None
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Winsorize outliers by capping values at specified percentiles
        
        This is the preferred method for SLE research as it preserves sample size
        while reducing the impact of extreme values.
        
        Args:
            df: Input dataframe
            lower_percentile: Lower bound percentile (default 1st percentile = 0.01)
            upper_percentile: Upper bound percentile (default 99th percentile = 0.99)
            columns: Specific columns to winsorize (None = all numeric)
        
        Returns:
            Tuple of (processed dataframe, report dict)
        """
        from scipy.stats.mstats import winsorize
        
        report = {
            "action": "winsorization",
            "lower_percentile": lower_percentile,
            "upper_percentile": upper_percentile,
            "columns_processed": [],
            "values_capped": {}
        }
        
        df_processed = df.copy()
        
        # Identify numeric columns
        if columns is None:
            columns = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        
        for col in columns:
            if col not in df.columns:
                continue
            
            # Get original values
            original_values = df[col].copy()
            
            # Calculate percentile bounds
            lower_bound = df[col].quantile(lower_percentile)
            upper_bound = df[col].quantile(upper_percentile)
            
            # Winsorize: cap values at percentiles
            df_processed[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
            
            # Track changes
            lower_capped = (original_values < lower_bound).sum()
            upper_capped = (original_values > upper_bound).sum()
            total_capped = lower_capped + upper_capped
            
            if total_capped > 0:
                report["columns_processed"].append(col)
                report["values_capped"][col] = {
                    "lower_bound": float(lower_bound),
                    "upper_bound": float(upper_bound),
                    "lower_capped_count": int(lower_capped),
                    "upper_capped_count": int(upper_capped),
                    "total_capped": int(total_capped),
                    "percentage_capped": round(total_capped / len(df) * 100, 2)
                }
        
        report["total_columns"] = len(report["columns_processed"])
        report["total_values_capped"] = sum(v["total_capped"] for v in report["values_capped"].values())
        
        logger.info(f"Winsorized {report['total_columns']} columns, capped {report['total_values_capped']} values")
        self.preprocessing_history.append(report)
        
        return df_processed, report
    
    def filter_high_missing_variables(
        self,
        df: pd.DataFrame,
        threshold: float = 0.5
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Remove variables (columns) with missing data above threshold
        
        Research standard: Remove variables with >50% missing data
        This ensures reliable statistical analysis.
        
        Args:
            df: Input dataframe
            threshold: Maximum allowed missing proportion (default 0.5 = 50%)
        
        Returns:
            Tuple of (filtered dataframe, report dict)
        """
        report = {
            "action": "variable_filtration",
            "threshold": threshold,
            "threshold_percentage": threshold * 100,
            "removed_columns": [],
            "kept_columns": [],
            "removal_details": {}
        }
        
        df_filtered = df.copy()
        
        for col in df.columns:
            missing_count = df[col].isna().sum()
            missing_percentage = missing_count / len(df)
            
            if missing_percentage > threshold:
                # Remove this column
                df_filtered = df_filtered.drop(columns=[col])
                report["removed_columns"].append(col)
                report["removal_details"][col] = {
                    "missing_count": int(missing_count),
                    "missing_percentage": round(missing_percentage * 100, 2),
                    "reason": f"Exceeds {threshold*100}% missing threshold"
                }
            else:
                report["kept_columns"].append(col)
        
        report["original_column_count"] = len(df.columns)
        report["removed_column_count"] = len(report["removed_columns"])
        report["remaining_column_count"] = len(report["kept_columns"])
        
        logger.info(
            f"Variable filtration: Removed {report['removed_column_count']}/{report['original_column_count']} "
            f"columns with >{threshold*100}% missing data"
        )
        
        self.preprocessing_history.append(report)
        
        return df_filtered, report
    
    def get_preprocessing_pipeline_report(self) -> Dict:
        """Get full preprocessing pipeline report"""
        return {
            "total_steps": len(self.preprocessing_history),
            "steps": self.preprocessing_history
        }
