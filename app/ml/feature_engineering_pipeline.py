"""
Feature Engineering Pipeline
Reusable pipeline that applies the same feature transformations during training and inference
Prevents inference feature mismatch errors
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class FeatureEngineeringPipeline:
    """
    Captures feature engineering logic from training and applies it during inference
    
    Problem solved:
    - Training creates derived features (e.g., CRP_ESR_ratio)
    - Inference receives raw data without these features
    - Missing features filled with 0 → incorrect predictions
    
    Solution:
    - Save feature engineering logic with the model
    - Apply same transformations during inference
    - Ensures feature consistency between training and inference
    """
    
    def __init__(self, target_column: Optional[str] = None):
        self.feature_specs = []  # List of feature transformation specifications
        self.categorical_columns = []  # Columns that were one-hot encoded
        self.categorical_mapping = {}  # Mapping of categorical columns to dummy columns
        self.target_column = target_column  # Target column to preserve
        self.fitted = False
        
    def add_ratio_feature(
        self, 
        feature_name: str, 
        numerator_col: str, 
        denominator_col: str,
        epsilon: float = 1e-6
    ):
        """
        Add a ratio feature (e.g., CRP_ESR_ratio = CRP / ESR)
        
        Args:
            feature_name: Name of derived feature
            numerator_col: Column name for numerator
            denominator_col: Column name for denominator
            epsilon: Small value to prevent division by zero
        """
        self.feature_specs.append({
            'type': 'ratio',
            'name': feature_name,
            'numerator': numerator_col,
            'denominator': denominator_col,
            'epsilon': epsilon
        })
        logger.info(f"Added ratio feature: {feature_name} = {numerator_col} / {denominator_col}")
    
    def add_temporal_feature(
        self,
        feature_name: str,
        date_column: str,
        reference_date: Optional[str] = None,
        unit: str = 'days'
    ):
        """
        Add temporal feature (e.g., disease_duration_days)
        
        Args:
            feature_name: Name of derived feature
            date_column: Column containing the date
            reference_date: Reference date (if None, uses current date)
            unit: 'days', 'months', or 'years'
        """
        self.feature_specs.append({
            'type': 'temporal',
            'name': feature_name,
            'date_column': date_column,
            'reference_date': reference_date or datetime.now().isoformat(),
            'unit': unit
        })
        logger.info(f"Added temporal feature: {feature_name} from {date_column}")
    
    def add_derived_feature(
        self,
        feature_name: str,
        source_columns: List[str],
        transformation: str,
        transformation_params: Optional[Dict] = None
    ):
        """
        Add custom derived feature
        
        Args:
            feature_name: Name of derived feature
            source_columns: List of source column names
            transformation: Type of transformation ('sum', 'mean', 'product', 'difference')
            transformation_params: Additional parameters for transformation
        """
        self.feature_specs.append({
            'type': 'derived',
            'name': feature_name,
            'source_columns': source_columns,
            'transformation': transformation,
            'params': transformation_params or {}
        })
        logger.info(f"Added derived feature: {feature_name} from {source_columns}")
    
    def add_composite_pathological_feature(
        self,
        feature_name: str,
        source_columns: List[str],
        percentile: float,
        logic: str = 'all',
        above_threshold: bool = False
    ):
        """
        Add composite pathological state feature (e.g., Pancytopenia, Liver Damage)
        
        Args:
            feature_name: Name of derived feature (e.g., 'pancytopenia')
            source_columns: List of column names to evaluate
            percentile: Percentile threshold (0-100)
            logic: 'all' (all conditions must be true) or 'any' (any condition true)
            above_threshold: If True, above percentile = positive, else below = positive
        """
        self.feature_specs.append({
            'type': 'composite_pathological',
            'name': feature_name,
            'source_columns': source_columns,
            'percentile': percentile,
            'logic': logic,
            'above_threshold': above_threshold
        })
        logic_str = "ALL" if logic == 'all' else "ANY"
        direction = "above" if above_threshold else "below"
        logger.info(f"Added composite feature: {feature_name} = {logic_str} of {source_columns} {direction} {percentile}th percentile")
    
    def add_percentile_cutoff_feature(
        self,
        feature_name: str,
        source_column: str,
        percentile: float,
        above_is_positive: bool = True
    ):
        """
        Add binary feature based on percentile cutoff
        
        Args:
            feature_name: Name of derived feature (e.g., 'high_inflammation')
            source_column: Column to evaluate
            percentile: Percentile threshold (0-100)
            above_is_positive: If True, above percentile = 1, else = 0
        """
        self.feature_specs.append({
            'type': 'percentile_cutoff',
            'name': feature_name,
            'source_column': source_column,
            'percentile': percentile,
            'above_is_positive': above_is_positive
        })
        direction = "above" if above_is_positive else "below"
        logger.info(f"Added percentile cutoff feature: {feature_name} = {source_column} {direction} {percentile}th percentile")
    
    def fit(self, df: pd.DataFrame) -> 'FeatureEngineeringPipeline':
        """
        Fit the pipeline on training data
        
        Args:
            df: Training DataFrame
        
        Returns:
            self (fitted pipeline)
        """
        logger.info("Fitting FeatureEngineeringPipeline...")
        
        # Record categorical columns that will be one-hot encoded
        self.categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Remove ID columns and target column from categorical encoding
        id_cols = [col for col in self.categorical_columns if 'id' in col.lower() or 'record' in col.lower()]
        self.categorical_columns = [col for col in self.categorical_columns if col not in id_cols]
        
        # CRITICAL: Exclude target column from encoding (preserve original for ML)
        if self.target_column and self.target_column in self.categorical_columns:
            self.categorical_columns.remove(self.target_column)
            logger.info(f"Preserving target column '{self.target_column}' from encoding")
        
        logger.info(f"Identified {len(self.categorical_columns)} categorical columns for encoding")
        
        self.fitted = True
        return self
    
    def transform(self, df: pd.DataFrame, is_inference: bool = False) -> pd.DataFrame:
        """
        Apply feature engineering transformations
        
        Args:
            df: DataFrame to transform
            is_inference: If True, handles missing columns gracefully
        
        Returns:
            Transformed DataFrame
        """
        if not self.fitted:
            raise ValueError("Pipeline must be fitted before transform()")
        
        logger.info(f"Transforming data with {len(self.feature_specs)} feature engineering steps...")
        df = df.copy()
        
        # Step 1: Apply feature engineering specifications
        for spec in self.feature_specs:
            try:
                if spec['type'] == 'ratio':
                    df = self._apply_ratio(df, spec, is_inference)
                
                elif spec['type'] == 'temporal':
                    df = self._apply_temporal(df, spec, is_inference)
                
                elif spec['type'] == 'derived':
                    df = self._apply_derived(df, spec, is_inference)
                
                elif spec['type'] == 'composite_pathological':
                    df = self._apply_composite_pathological(df, spec, is_inference)
                
                elif spec['type'] == 'percentile_cutoff':
                    df = self._apply_percentile_cutoff(df, spec, is_inference)
                
            except Exception as e:
                if is_inference:
                    # During inference, log warning but continue
                    logger.warning(f"Could not create feature {spec['name']}: {e}")
                    df[spec['name']] = 0  # Fill with default value
                else:
                    # During training, raise error
                    raise
        
        # Step 2: One-hot encode categorical columns
        if self.categorical_columns:
            # Only encode columns that exist in the current dataframe
            cols_to_encode = [col for col in self.categorical_columns if col in df.columns]
            
            if cols_to_encode:
                df = pd.get_dummies(df, columns=cols_to_encode, drop_first=True)
                logger.info(f"One-hot encoded {len(cols_to_encode)} categorical columns")
        
        return df
    
    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fit the pipeline and transform the data in one step
        
        Args:
            df: Training DataFrame
        
        Returns:
            Transformed DataFrame
        """
        return self.fit(df).transform(df, is_inference=False)
    
    def _apply_ratio(self, df: pd.DataFrame, spec: Dict, is_inference: bool) -> pd.DataFrame:
        """Apply ratio transformation"""
        numerator = spec['numerator']
        denominator = spec['denominator']
        epsilon = spec['epsilon']
        name = spec['name']
        
        # Check if source columns exist
        if numerator not in df.columns or denominator not in df.columns:
            if is_inference:
                logger.warning(f"Missing columns for {name}: {numerator} or {denominator}")
                df[name] = 0
            else:
                raise ValueError(f"Missing columns for {name}: {numerator}, {denominator}")
            return df
        
        # Convert columns to numeric, coercing errors to NaN
        numerator_numeric = pd.to_numeric(df[numerator], errors='coerce')
        denominator_numeric = pd.to_numeric(df[denominator], errors='coerce')
        
        # Calculate ratio
        df[name] = numerator_numeric / (denominator_numeric + epsilon)
        logger.debug(f"Created ratio feature: {name}")
        
        return df
    
    def _apply_temporal(self, df: pd.DataFrame, spec: Dict, is_inference: bool) -> pd.DataFrame:
        """Apply temporal transformation"""
        date_col = spec['date_column']
        name = spec['name']
        unit = spec['unit']
        reference = pd.to_datetime(spec['reference_date'])
        
        # Check if date column exists
        if date_col not in df.columns:
            if is_inference:
                logger.warning(f"Missing date column for {name}: {date_col}")
                df[name] = 0
            else:
                raise ValueError(f"Missing date column for {name}: {date_col}")
            return df
        
        # Convert to datetime
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        
        # Calculate temporal difference
        time_diff = (reference - df[date_col]).dt.total_seconds()
        
        if unit == 'days':
            df[name] = time_diff / 86400
        elif unit == 'months':
            df[name] = time_diff / (86400 * 30.44)  # Average month
        elif unit == 'years':
            df[name] = time_diff / (86400 * 365.25)  # Account for leap years
        else:
            df[name] = time_diff
        
        logger.debug(f"Created temporal feature: {name}")
        
        return df
    
    def _apply_derived(self, df: pd.DataFrame, spec: Dict, is_inference: bool) -> pd.DataFrame:
        """Apply derived feature transformation"""
        source_cols = spec['source_columns']
        name = spec['name']
        transformation = spec['transformation']
        
        # Check if all source columns exist
        missing_cols = [col for col in source_cols if col not in df.columns]
        if missing_cols:
            if is_inference:
                logger.warning(f"Missing source columns for {name}: {missing_cols}")
                df[name] = 0
            else:
                raise ValueError(f"Missing source columns for {name}: {missing_cols}")
            return df
        
        # Convert source columns to numeric first
        for col in source_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Apply transformation
        if transformation == 'sum':
            df[name] = df[source_cols].sum(axis=1)
        elif transformation == 'mean':
            df[name] = df[source_cols].mean(axis=1)
        elif transformation == 'product':
            df[name] = df[source_cols].prod(axis=1)
        elif transformation == 'difference':
            # Assumes 2 columns
            df[name] = df[source_cols[0]] - df[source_cols[1]]
        else:
            raise ValueError(f"Unknown transformation: {transformation}")
        
        logger.debug(f"Created derived feature: {name}")
        
        return df
    
    def get_feature_specs(self) -> List[Dict]:
        """Get list of feature engineering specifications"""
        return self.feature_specs
    
    def get_config(self) -> Dict:
        """
        Get pipeline configuration for saving
        
        Returns:
            Dictionary containing pipeline configuration
        """
        return {
            'feature_specs': self.feature_specs,
            'categorical_columns': self.categorical_columns,
            'categorical_mapping': self.categorical_mapping,
            'fitted': self.fitted
        }
    
    @classmethod
    def from_config(cls, config: Dict) -> 'FeatureEngineeringPipeline':
        """
        Create pipeline from saved configuration
        
        Args:
            config: Dictionary containing pipeline configuration
        
        Returns:
            FeatureEngineeringPipeline instance
        """
        pipeline = cls()
        pipeline.feature_specs = config.get('feature_specs', [])
        pipeline.categorical_columns = config.get('categorical_columns', [])
        pipeline.categorical_mapping = config.get('categorical_mapping', {})
        pipeline.fitted = config.get('fitted', False)
        
        logger.info(f"Loaded pipeline with {len(pipeline.feature_specs)} feature engineering steps")
        
        return pipeline
    
    def _apply_composite_pathological(self, df: pd.DataFrame, spec: Dict, is_inference: bool) -> pd.DataFrame:
        """Apply composite pathological feature transformation"""
        source_cols = spec['source_columns']
        name = spec['name']
        percentile = spec['percentile']
        logic = spec['logic']
        above_threshold = spec['above_threshold']
        
        # Check if all source columns exist
        missing_cols = [col for col in source_cols if col not in df.columns]
        if missing_cols:
            if is_inference:
                logger.warning(f"Missing source columns for {name}: {missing_cols}")
                df[name] = 0
            else:
                raise ValueError(f"Missing source columns for {name}: {missing_cols}")
            return df
        
        # Convert columns to numeric and calculate percentile thresholds
        thresholds = {}
        for col in source_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            thresholds[col] = df[col].quantile(percentile / 100.0)
        
        # Create boolean conditions
        if above_threshold:
            conditions = [df[col] > thresholds[col] for col in source_cols]
        else:
            conditions = [df[col] < thresholds[col] for col in source_cols]
        
        # Apply logic (all or any)
        if logic == 'all':
            result = pd.Series(True, index=df.index)
            for condition in conditions:
                result = result & condition
        else:  # any
            result = pd.Series(False, index=df.index)
            for condition in conditions:
                result = result | condition
        
        df[name] = result.astype(int)
        logger.debug(f"Created composite pathological feature: {name} ({df[name].sum()} positive cases)")
        
        return df
    
    def _apply_percentile_cutoff(self, df: pd.DataFrame, spec: Dict, is_inference: bool) -> pd.DataFrame:
        """Apply percentile cutoff transformation"""
        source_col = spec['source_column']
        name = spec['name']
        percentile = spec['percentile']
        above_is_positive = spec['above_is_positive']
        
        # Check if source column exists
        if source_col not in df.columns:
            if is_inference:
                logger.warning(f"Missing source column for {name}: {source_col}")
                df[name] = 0
            else:
                raise ValueError(f"Missing source column for {name}: {source_col}")
            return df
        
        # Convert to numeric and calculate percentile threshold
        df[source_col] = pd.to_numeric(df[source_col], errors='coerce')
        threshold = df[source_col].quantile(percentile / 100.0)
        
        # Create binary feature
        if above_is_positive:
            df[name] = (df[source_col] > threshold).astype(int)
        else:
            df[name] = (df[source_col] <= threshold).astype(int)
        
        logger.debug(f"Created percentile cutoff feature: {name} (threshold={threshold:.2f}, {df[name].sum()} positive cases)")
        
        return df
    
    def __repr__(self):
        return f"FeatureEngineeringPipeline(features={len(self.feature_specs)}, fitted={self.fitted})"
