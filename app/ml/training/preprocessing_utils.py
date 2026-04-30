"""
Data Preprocessing Utilities
Implements research-grade preprocessing pipeline aligned with USM SLE study

All methods are CONFIGURABLE - no hardcoded values
Researcher can control all parameters through API
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
from scipy.stats.mstats import winsorize as scipy_winsorize
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
import logging

logger = logging.getLogger(__name__)


class DataPreprocessor:
    """
    Configurable preprocessing pipeline for clinical ML data
    
    Implements research study preprocessing:
    1. Variable filtration (remove high-missing features)
    2. Imputation (median/mode)
    3. Outlier handling (winsorization)
    4. Standardization (Z-score or others)
    
    All steps are OPTIONAL and CONFIGURABLE
    """
    
    def __init__(self):
        self.numeric_imputer = None
        self.categorical_imputer = None
        self.scaler = None
        self.winsorize_limits = None
        self.preprocessing_metadata = {}
    
    def remove_high_missing_features(
        self,
        df: pd.DataFrame,
        threshold: float = 0.5,
        exclude_columns: Optional[List[str]] = None
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Remove features with high percentage of missing values
        
        Args:
            df: Input DataFrame
            threshold: Maximum allowed missing percentage (0.5 = 50%)
            exclude_columns: Columns to preserve regardless of missing %
        
        Returns:
            Tuple of (filtered DataFrame, metadata dict)
        """
        exclude_columns = exclude_columns or []
        
        # Calculate missing percentage per column
        missing_pct = df.isnull().sum() / len(df)
        
        # Identify columns to drop (high missing, not in exclusion list)
        cols_to_drop = [
            col for col in df.columns 
            if missing_pct[col] > threshold and col not in exclude_columns
        ]
        
        metadata = {
            'threshold': threshold,
            'total_features_before': len(df.columns),
            'features_removed': len(cols_to_drop),
            'features_removed_list': cols_to_drop,
            'total_features_after': len(df.columns) - len(cols_to_drop)
        }
        
        if cols_to_drop:
            logger.info(f"Removing {len(cols_to_drop)} features with >{threshold*100}% missing data")
            df_filtered = df.drop(columns=cols_to_drop)
        else:
            logger.info("No features removed (all below missing threshold)")
            df_filtered = df.copy()
        
        return df_filtered, metadata
    
    def impute_missing_values(
        self,
        df: pd.DataFrame,
        numeric_strategy: str = 'median',
        categorical_strategy: str = 'most_frequent',
        target_column: Optional[str] = None
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Impute missing values using sklearn SimpleImputer
        
        Args:
            df: Input DataFrame
            numeric_strategy: Strategy for numeric columns
                             ('mean', 'median', 'most_frequent', 'constant')
            categorical_strategy: Strategy for categorical columns
                                 ('most_frequent', 'constant')
            target_column: Column to exclude from imputation (preserve for ML)
        
        Returns:
            Tuple of (imputed DataFrame, metadata dict)
        """
        df_imputed = df.copy()
        metadata = {
            'numeric_strategy': numeric_strategy,
            'categorical_strategy': categorical_strategy,
            'numeric_columns_imputed': [],
            'categorical_columns_imputed': [],
            'total_values_imputed': 0
        }
        
        # Separate numeric and categorical columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Remove ID columns and target from imputation
        id_cols = [col for col in df.columns if 'id' in col.lower() or 'record' in col.lower()]
        numeric_cols = [col for col in numeric_cols if col not in id_cols]
        categorical_cols = [col for col in categorical_cols if col not in id_cols]
        
        if target_column:
            numeric_cols = [col for col in numeric_cols if col != target_column]
            categorical_cols = [col for col in categorical_cols if col != target_column]
        
        # Impute numeric columns
        if numeric_cols:
            # Count missing before imputation
            missing_before = df[numeric_cols].isnull().sum().sum()
            
            self.numeric_imputer = SimpleImputer(strategy=numeric_strategy)
            df_imputed[numeric_cols] = self.numeric_imputer.fit_transform(df[numeric_cols])
            
            metadata['numeric_columns_imputed'] = numeric_cols
            metadata['numeric_missing_before'] = int(missing_before)
            logger.info(f"Imputed {missing_before} missing values in {len(numeric_cols)} numeric columns (strategy: {numeric_strategy})")
        
        # Impute categorical columns
        if categorical_cols:
            # Count missing before imputation
            missing_before = df[categorical_cols].isnull().sum().sum()
            
            self.categorical_imputer = SimpleImputer(strategy=categorical_strategy)
            df_imputed[categorical_cols] = self.categorical_imputer.fit_transform(df[categorical_cols])
            
            metadata['categorical_columns_imputed'] = categorical_cols
            metadata['categorical_missing_before'] = int(missing_before)
            logger.info(f"Imputed {missing_before} missing values in {len(categorical_cols)} categorical columns (strategy: {categorical_strategy})")
        
        metadata['total_values_imputed'] = metadata.get('numeric_missing_before', 0) + metadata.get('categorical_missing_before', 0)
        
        return df_imputed, metadata
    
    def winsorize_outliers(
        self,
        df: pd.DataFrame,
        limits: Tuple[float, float] = (0.01, 0.01),
        exclude_columns: Optional[List[str]] = None
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Winsorize outliers by capping at specified percentiles
        
        Args:
            df: Input DataFrame
            limits: Tuple of (lower_limit, upper_limit) as proportions
                   (0.01, 0.01) = cap at 1st and 99th percentiles
            exclude_columns: Columns to skip winsorization
        
        Returns:
            Tuple of (winsorized DataFrame, metadata dict)
        """
        exclude_columns = exclude_columns or []
        self.winsorize_limits = limits
        
        df_winsorized = df.copy()
        metadata = {
            'limits': limits,
            'columns_winsorized': [],
            'values_capped': {}
        }
        
        # Get numeric columns only
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Remove excluded columns
        numeric_cols = [col for col in numeric_cols if col not in exclude_columns]
        
        for col in numeric_cols:
            # Skip if all NaN
            if df[col].isnull().all():
                continue
            
            # Get original values for comparison
            original_values = df[col].dropna().values
            
            # Winsorize
            winsorized_values = scipy_winsorize(original_values, limits=limits)
            
            # Count how many values were capped
            lower_capped = np.sum(winsorized_values == winsorized_values.min())
            upper_capped = np.sum(winsorized_values == winsorized_values.max())
            total_capped = lower_capped + upper_capped
            
            if total_capped > 0:
                # Update dataframe
                df_winsorized.loc[df[col].notna(), col] = winsorized_values
                
                metadata['columns_winsorized'].append(col)
                metadata['values_capped'][col] = {
                    'lower_capped': int(lower_capped),
                    'upper_capped': int(upper_capped),
                    'total_capped': int(total_capped)
                }
        
        logger.info(f"Winsorized {len(metadata['columns_winsorized'])} columns at {limits[0]*100}% and {(1-limits[1])*100}% percentiles")
        
        return df_winsorized, metadata
    
    def standardize_features(
        self,
        df: pd.DataFrame,
        method: str = 'standard',
        exclude_columns: Optional[List[str]] = None
    ) -> Tuple[pd.DataFrame, Optional[object], Dict]:
        """
        Standardize numeric features
        
        Args:
            df: Input DataFrame
            method: Scaling method ('standard', 'minmax', 'robust', 'none')
            exclude_columns: Columns to skip scaling
        
        Returns:
            Tuple of (scaled DataFrame, scaler object, metadata dict)
        """
        if method == 'none':
            logger.info("Standardization skipped (method='none')")
            return df.copy(), None, {'method': 'none'}
        
        exclude_columns = exclude_columns or []
        df_scaled = df.copy()
        
        metadata = {
            'method': method,
            'columns_scaled': []
        }
        
        # Get numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        numeric_cols = [col for col in numeric_cols if col not in exclude_columns]
        
        if not numeric_cols:
            logger.warning("No numeric columns to standardize")
            return df_scaled, None, metadata
        
        # Select scaler
        if method == 'standard':
            self.scaler = StandardScaler()
        elif method == 'minmax':
            self.scaler = MinMaxScaler()
        elif method == 'robust':
            self.scaler = RobustScaler()
        else:
            raise ValueError(f"Unknown standardization method: {method}")
        
        # Fit and transform
        df_scaled[numeric_cols] = self.scaler.fit_transform(df[numeric_cols])
        
        metadata['columns_scaled'] = numeric_cols
        metadata['scaler_params'] = {
            'mean': self.scaler.mean_.tolist() if hasattr(self.scaler, 'mean_') else None,
            'scale': self.scaler.scale_.tolist() if hasattr(self.scaler, 'scale_') else None
        }
        
        logger.info(f"Standardized {len(numeric_cols)} columns using {method} scaling")
        
        return df_scaled, self.scaler, metadata
    
    def create_binary_target(
        self,
        df: pd.DataFrame,
        source_column: str,
        threshold: float,
        target_name: str = 'target_binary',
        above_is_positive: bool = True
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Create binary target variable from continuous column
        
        Example: SLEDAI-2000 > 4 → High Activity (1) vs Low Activity (0)
        
        Args:
            df: Input DataFrame
            source_column: Column containing continuous values
            threshold: Cutoff value for dichotomization
            target_name: Name of new binary column
            above_is_positive: If True, values > threshold = 1, else 0
        
        Returns:
            Tuple of (DataFrame with new column, metadata dict)
        """
        if source_column not in df.columns:
            raise ValueError(f"Source column '{source_column}' not found in DataFrame")
        
        df_with_target = df.copy()
        
        # Create binary target
        if above_is_positive:
            df_with_target[target_name] = (df[source_column] > threshold).astype(int)
        else:
            df_with_target[target_name] = (df[source_column] <= threshold).astype(int)
        
        # Calculate class distribution
        class_counts = df_with_target[target_name].value_counts().to_dict()
        
        metadata = {
            'source_column': source_column,
            'threshold': threshold,
            'target_name': target_name,
            'above_is_positive': above_is_positive,
            'class_distribution': class_counts,
            'total_positive': class_counts.get(1, 0),
            'total_negative': class_counts.get(0, 0)
        }
        
        logger.info(f"Created binary target '{target_name}' from '{source_column}' (threshold={threshold})")
        logger.info(f"  Class distribution: {class_counts}")
        
        return df_with_target, metadata
    
    def get_preprocessing_report(self) -> Dict:
        """
        Get comprehensive preprocessing report
        
        Returns:
            Dictionary with all preprocessing metadata
        """
        return self.preprocessing_metadata.copy()
    
    def save_preprocessing_state(self) -> Dict:
        """
        Save preprocessing state for inference
        
        Returns:
            Dictionary containing fitted preprocessors
        """
        return {
            'numeric_imputer': self.numeric_imputer,
            'categorical_imputer': self.categorical_imputer,
            'scaler': self.scaler,
            'winsorize_limits': self.winsorize_limits,
            'metadata': self.preprocessing_metadata
        }
    
    @classmethod
    def load_preprocessing_state(cls, state: Dict) -> 'DataPreprocessor':
        """
        Load preprocessing state from saved dictionary
        
        Args:
            state: Dictionary containing fitted preprocessors
        
        Returns:
            DataPreprocessor instance with loaded state
        """
        preprocessor = cls()
        preprocessor.numeric_imputer = state.get('numeric_imputer')
        preprocessor.categorical_imputer = state.get('categorical_imputer')
        preprocessor.scaler = state.get('scaler')
        preprocessor.winsorize_limits = state.get('winsorize_limits')
        preprocessor.preprocessing_metadata = state.get('metadata', {})
        
        return preprocessor


def calculate_percentile_cutoffs(
    df: pd.DataFrame,
    columns: List[str],
    percentiles: Union[float, List[float]] = [10, 25, 50, 75, 90]
) -> Dict[str, Dict[float, float]]:
    """
    Calculate percentile cutoffs for specified columns
    
    Args:
        df: Input DataFrame
        columns: List of column names
        percentiles: Percentile(s) to calculate (0-100)
    
    Returns:
        Dictionary mapping column -> percentile -> value
    """
    if isinstance(percentiles, (int, float)):
        percentiles = [percentiles]
    
    cutoffs = {}
    
    for col in columns:
        if col not in df.columns:
            logger.warning(f"Column '{col}' not found in DataFrame")
            continue
        
        if not pd.api.types.is_numeric_dtype(df[col]):
            logger.warning(f"Column '{col}' is not numeric, skipping")
            continue
        
        col_cutoffs = {}
        for p in percentiles:
            col_cutoffs[p] = float(df[col].quantile(p / 100.0))
        
        cutoffs[col] = col_cutoffs
        logger.info(f"Calculated {len(percentiles)} percentiles for '{col}'")
    
    return cutoffs


def create_composite_pathological_features(
    df: pd.DataFrame,
    wbc_column: Optional[str] = None,
    hgb_column: Optional[str] = None,
    plt_column: Optional[str] = None,
    alt_column: Optional[str] = None,
    ast_column: Optional[str] = None,
    low_percentile: float = 10,
    high_percentile: float = 70,
    auto_detect_columns: bool = True
) -> Tuple[pd.DataFrame, Dict]:
    """
    Create composite pathological state features
    
    Implements clinical features from research study:
    - Pancytopenia: Low WBC + Low HGB + Low PLT
    - Cytopenia: Any blood count abnormality
    - Liver Damage: High ALT or High AST
    
    Args:
        df: Input DataFrame
        wbc_column: Column name for WBC (white blood cell count)
        hgb_column: Column name for HGB (hemoglobin)
        plt_column: Column name for PLT (platelet count)
        alt_column: Column name for ALT (liver enzyme)
        ast_column: Column name for AST (liver enzyme)
        low_percentile: Percentile for "low" threshold (default: 10th)
        high_percentile: Percentile for "high" threshold (default: 70th)
        auto_detect_columns: If True, auto-detect column names
    
    Returns:
        Tuple of (DataFrame with new features, metadata dict)
    """
    df_composite = df.copy()
    metadata = {
        'features_created': [],
        'thresholds': {},
        'low_percentile': low_percentile,
        'high_percentile': high_percentile
    }
    
    # Auto-detect columns if not provided
    if auto_detect_columns:
        if not wbc_column:
            wbc_cols = [col for col in df.columns if 'wbc' in col.lower() and 'white' not in col.lower()]
            wbc_column = wbc_cols[0] if wbc_cols else None
        
        if not hgb_column:
            hgb_cols = [col for col in df.columns if 'hgb' in col.lower() or 'hemoglobin' in col.lower()]
            hgb_column = hgb_cols[0] if hgb_cols else None
        
        if not plt_column:
            plt_cols = [col for col in df.columns if 'plt' in col.lower() or 'platelet' in col.lower()]
            plt_column = plt_cols[0] if plt_cols else None
        
        if not alt_column:
            alt_cols = [col for col in df.columns if col.lower().endswith('alt') or 'alt' in col.lower() and 'liver' in col.lower()]
            alt_column = alt_cols[0] if alt_cols else None
        
        if not ast_column:
            ast_cols = [col for col in df.columns if col.lower().endswith('ast') or 'ast' in col.lower() and 'liver' in col.lower()]
            ast_column = ast_cols[0] if ast_cols else None
    
    # Create Pancytopenia feature (all three blood counts low)
    if wbc_column and hgb_column and plt_column:
        wbc_threshold = df[wbc_column].quantile(low_percentile / 100.0)
        hgb_threshold = df[hgb_column].quantile(low_percentile / 100.0)
        plt_threshold = df[plt_column].quantile(low_percentile / 100.0)
        
        df_composite['pancytopenia'] = (
            (df[wbc_column] < wbc_threshold) &
            (df[hgb_column] < hgb_threshold) &
            (df[plt_column] < plt_threshold)
        ).astype(int)
        
        metadata['features_created'].append('pancytopenia')
        metadata['thresholds']['pancytopenia'] = {
            'wbc_threshold': float(wbc_threshold),
            'hgb_threshold': float(hgb_threshold),
            'plt_threshold': float(plt_threshold)
        }
        
        pancytopenia_count = df_composite['pancytopenia'].sum()
        logger.info(f"Created 'pancytopenia' feature: {pancytopenia_count}/{len(df)} patients ({pancytopenia_count/len(df)*100:.1f}%)")
    
    # Create Cytopenia feature (any blood count abnormality)
    if wbc_column and hgb_column and plt_column:
        df_composite['cytopenia'] = (
            (df[wbc_column] < wbc_threshold) |
            (df[hgb_column] < hgb_threshold) |
            (df[plt_column] < plt_threshold)
        ).astype(int)
        
        metadata['features_created'].append('cytopenia')
        
        cytopenia_count = df_composite['cytopenia'].sum()
        logger.info(f"Created 'cytopenia' feature: {cytopenia_count}/{len(df)} patients ({cytopenia_count/len(df)*100:.1f}%)")
    
    # Create Liver Damage feature (high ALT or AST)
    if alt_column and ast_column:
        alt_threshold = df[alt_column].quantile(high_percentile / 100.0)
        ast_threshold = df[ast_column].quantile(high_percentile / 100.0)
        
        df_composite['liver_damage'] = (
            (df[alt_column] > alt_threshold) |
            (df[ast_column] > ast_threshold)
        ).astype(int)
        
        metadata['features_created'].append('liver_damage')
        metadata['thresholds']['liver_damage'] = {
            'alt_threshold': float(alt_threshold),
            'ast_threshold': float(ast_threshold)
        }
        
        liver_damage_count = df_composite['liver_damage'].sum()
        logger.info(f"Created 'liver_damage' feature: {liver_damage_count}/{len(df)} patients ({liver_damage_count/len(df)*100:.1f}%)")
    
    if not metadata['features_created']:
        logger.warning("No composite features created - required columns not found")
    
    return df_composite, metadata
