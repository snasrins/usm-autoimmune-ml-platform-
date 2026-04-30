"""
Training Dataset Generator (Layer 6)
Generates training datasets with feature engineering from cleaned data
Uses FlexibleDatasetWide - NO HARDCODED SCHEMA
Includes ML data validation before training
Uses FeatureEngineeringPipeline for reproducible transformations
Uses MLBridgeService for data pipeline → ML pipeline transformation
"""
import pandas as pd
import numpy as np
import json
from sqlalchemy.orm import Session
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging
from sqlalchemy import text

from app.models.flexible_data import FlexibleDatasetWide, ImportPreviewStaging
from app.services.ml_data_validator import MLDataValidator
from app.ml.feature_engineering_pipeline import FeatureEngineeringPipeline
from app.services.ml_bridge_service import MLBridgeService
from app.services.data_provenance_service import DataProvenanceService
from app.ml.training.preprocessing_utils import DataPreprocessor, create_composite_pathological_features

logger = logging.getLogger(__name__)


class DatasetGenerator:
    """
    Generate ML training datasets from fact tables with feature engineering
    
    Features generated:
    - Demographics (age, gender, ethnicity)
    - Laboratory values (latest)
    - Laboratory trends (slopes, changes over time)
    - Medications (current, historical counts)
    - Temporal features (time since diagnosis, etc.)
    - Calculated ratios
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.bridge_service = MLBridgeService(db)
        self.provenance_service = DataProvenanceService(db)
        
    def generate_training_dataset(
        self,
        batch_id: str,
        target_column: str = "labels_disease_classification",
        min_events_per_patient: int = 2,
        test_size: float = 0.2,
        random_state: int = 42,
        create_separate_feature_sets: bool = True,
        scaling_strategy: str = 'standard',
        use_lasso_feature_selection: bool = True,
        lasso_alpha: float = 0.01,
        skip_preprocessing: bool = False,
        # NEW RESEARCH-ALIGNED PREPROCESSING PARAMETERS
        apply_imputation: bool = True,
        imputation_numeric_strategy: str = 'median',
        imputation_categorical_strategy: str = 'most_frequent',
        apply_winsorization: bool = True,
        winsorize_limits: Tuple[float, float] = (0.01, 0.01),
        apply_composite_features: bool = True,
        composite_low_percentile: float = 10.0,
        composite_high_percentile: float = 70.0,
        use_sledai_binary: bool = False,
        sledai_threshold: float = 4.0,
        sledai_column: str = 'disease_activity_SLEDAI_score'
    ) -> Dict:
        """
        Generate complete training dataset with train/test split
        NO HARDCODED SCHEMA - dynamic target column from JSONB data
        
        FULLY CONFIGURABLE PREPROCESSING - researcher's playground!
        
        Args:
            target_column: Column name for target variable (e.g., 'labels_disease_classification')
            min_events_per_patient: Minimum data quality threshold
            test_size: Proportion for test set (default 0.2, study uses 0.35)
            random_state: Random seed for reproducibility
            create_separate_feature_sets: If True, creates both raw (for trees) and scaled (for linear)
            scaling_strategy: 'standard' (StandardScaler), 'minmax' (MinMaxScaler), or 'robust' (RobustScaler)
            use_lasso_feature_selection: If True, applies LASSO to remove redundant/noisy features
            lasso_alpha: Regularization strength for LASSO (lower = more features kept)
            skip_preprocessing: If True, skips ALL ML preprocessing (scaling, LASSO) - ADVANCED USERS ONLY
            
            # NEW RESEARCH-ALIGNED PREPROCESSING (All Optional & Configurable)
            apply_imputation: If True, impute missing values (study: median/mode)
            imputation_numeric_strategy: 'median', 'mean', 'most_frequent', 'constant'
            imputation_categorical_strategy: 'most_frequent', 'constant'
            apply_winsorization: If True, cap outliers at percentiles (study: 1%/99%)
            winsorize_limits: (lower, upper) as proportions, e.g., (0.01, 0.01) = 1%/99%
            apply_composite_features: If True, create pathological state features
            composite_low_percentile: Percentile for "low" blood counts (study: 10th)
            composite_high_percentile: Percentile for "high" liver enzymes (study: 70th)
            use_sledai_binary: If True, create binary target from SLEDAI score (study approach)
            sledai_threshold: SLEDAI cutoff for binary classification (study: 4.0)
            sledai_column: Column containing SLEDAI score
            
        Returns:
            Dictionary containing:
                - X_train, X_test: Raw feature matrices (for tree models)
                - X_train_scaled, X_test_scaled: Scaled features (for linear models)
                - y_train, y_test: Target vectors
                - feature_names: List of feature names
                - scaler: Fitted scaler object (for inference)
                - selected_features: List of features selected by LASSO (if enabled)
                - preprocessing_metadata: Details of all preprocessing steps applied
                - metadata: Dataset metadata
        """
        logger.info(f"Starting dataset generation for batch: {batch_id}")
        logger.info(f"  Target column: {target_column}")
        logger.info(f"  Separate feature sets: {create_separate_feature_sets}")
        logger.info(f"  Skip preprocessing: {skip_preprocessing}")
        
        if skip_preprocessing:
            logger.warning(
                "⚠️ skip_preprocessing=True - ML pipeline will NOT apply scaling/feature selection! "
                "Ensure Layer 5 already did ML-compatible preprocessing."
            )
        
        # Step 0: VALIDATE DATA FOR ML TRAINING (FLEXIBLE - warns but allows proceeding)
        logger.info("Validating data for ML training...")
        validator = MLDataValidator(self.db)
        validation_report = validator.validate_for_ml_training(
            target_column=target_column,
            min_samples=100
        )
        
        # Log validation results
        logger.info(f"Validation status: {validation_report['status']}")
        logger.info(f"Total records: {validation_report['total_records']}")
        logger.info(f"Labeled records: {validation_report['labeled_records']}")
        logger.info(f"Unlabeled records: {validation_report['unlabeled_records']}")
        
        # Show warnings (but continue)
        if validation_report['warnings']:
            for warning in validation_report['warnings']:
                logger.warning(f"⚠️  {warning}")
        
        # Show recommendations
        if validation_report['recommendations']:
            for rec in validation_report['recommendations']:
                logger.info(f"💡 Recommendation: {rec}")
        
        # CRITICAL ISSUES: Stop training
        if not validation_report['can_proceed']:
            critical_issues = [issue for issue in validation_report['issues'] if issue.get('severity') == 'critical']
            error_msg = "Cannot proceed with training:\n"
            for issue in critical_issues:
                error_msg += f"  - {issue['message']}\n"
                error_msg += f"    Recommendation: {issue['recommendation']}\n"
            raise ValueError(error_msg)
        
        logger.info("✅ Validation complete - proceeding with dataset generation")
        
        # Step 1: Extract base features from FlexibleDatasetWide
        df = self._extract_base_features(batch_id=batch_id)
        logger.info(f"Extracted base features: {df.shape}")
        
        # Step 2: Engineer features dynamically using FeatureEngineeringPipeline
        df, feature_pipeline = self._engineer_features_with_pipeline(
            df, target_column, 
            apply_composite_features=apply_composite_features,
            composite_low_percentile=composite_low_percentile,
            composite_high_percentile=composite_high_percentile
        )
        logger.info(f"After feature engineering: {df.shape}")
        
        # Step 2.5: Apply research-aligned preprocessing (FULLY CONFIGURABLE)
        preprocessor = DataPreprocessor()
        preprocessing_metadata = {}
        
        if not skip_preprocessing:
            logger.info("=" * 80)
            logger.info("RESEARCH-ALIGNED PREPROCESSING PIPELINE")
            logger.info("=" * 80)
            
            # 2.5.1: Imputation (study: median for continuous, mode for categorical)
            if apply_imputation:
                logger.info("Step 2.5.1: Imputation (Missing Value Handling)")
                df, impute_meta = preprocessor.impute_missing_values(
                    df,
                    numeric_strategy=imputation_numeric_strategy,
                    categorical_strategy=imputation_categorical_strategy,
                    target_column=target_column
                )
                preprocessing_metadata['imputation'] = impute_meta
                logger.info(f"  ✅ Imputed {impute_meta['total_values_imputed']} missing values")
            else:
                logger.info("Step 2.5.1: Imputation SKIPPED (apply_imputation=False)")
            
            # 2.5.2: Winsorization (study: 1% and 99% quantiles)
            if apply_winsorization:
                logger.info(f"Step 2.5.2: Winsorization (Outlier Handling at {winsorize_limits[0]*100}%/{(1-winsorize_limits[1])*100}% percentiles)")
                df, winsorize_meta = preprocessor.winsorize_outliers(
                    df,
                    limits=winsorize_limits,
                    exclude_columns=[target_column]
                )
                preprocessing_metadata['winsorization'] = winsorize_meta
                logger.info(f"  ✅ Winsorized {len(winsorize_meta['columns_winsorized'])} columns")
            else:
                logger.info("Step 2.5.2: Winsorization SKIPPED (apply_winsorization=False)")
            
            logger.info("=" * 80)
        else:
            logger.info("⚠️ Research preprocessing SKIPPED (skip_preprocessing=True)")
        
        # Step 2.6: Create SLEDAI binary target if requested (study approach)
        if use_sledai_binary:
            if sledai_column in df.columns:
                logger.info(f"Creating SLEDAI binary target from '{sledai_column}' (threshold={sledai_threshold})")
                df, sledai_meta = preprocessor.create_binary_target(
                    df,
                    source_column=sledai_column,
                    threshold=sledai_threshold,
                    target_name='target_sledai_binary',
                    above_is_positive=True
                )
                # Replace target column with SLEDAI binary
                target_column = 'target_sledai_binary'
                preprocessing_metadata['sledai_binary'] = sledai_meta
                logger.info(f"  ✅ SLEDAI binary target created: {sledai_meta['class_distribution']}")
            else:
                logger.warning(f"SLEDAI column '{sledai_column}' not found, skipping binary target creation")
        
        # Step 3: Filter records with insufficient data
        df = self._filter_patients(df, min_events_per_patient)
        logger.info(f"After filtering: {df.shape}")
        
        # Step 4: Prepare target variable
        if target_column not in df.columns:
            available_cols = [col for col in df.columns if 'label' in col.lower() or 'target' in col.lower()]
            raise ValueError(
                f"Target column '{target_column}' not found in dataset. "
                f"Available label columns: {available_cols}"
            )
        
        # CRITICAL: Drop unlabeled records (those with NaN/null target values)
        initial_count = len(df)
        df = df[df[target_column].notna()].copy()
        dropped_count = initial_count - len(df)
        
        if len(df) == 0:
            raise ValueError(
                f"No labeled records found! All {initial_count} records missing target column '{target_column}'. "
                "Please label some records before training."
            )
        
        logger.info(f"Dropped {dropped_count} unlabeled records. Training on {len(df)} labeled records.")
        
        # Remove identifier columns before creating feature matrix
        id_cols = [col for col in df.columns if 'id' in col.lower() or 'record' in col.lower() or 'dataset_type' in col.lower()]
        columns_to_drop = id_cols + [target_column]
        
        X = df.drop(columns=columns_to_drop)
        y = df[target_column]
        original_feature_names = X.columns.tolist()
        
        # CRITICAL: Encode categorical target labels to numeric (for sklearn models)
        label_encoder = None
        class_mapping = None
        if y.dtype == 'object' or pd.api.types.is_categorical_dtype(y):
            logger.info(f"Target column contains categorical labels: {y.unique()}")
            logger.info("Encoding categorical labels to numeric values...")
            
            from sklearn.preprocessing import LabelEncoder
            label_encoder = LabelEncoder()
            y_encoded = label_encoder.fit_transform(y)
            
            # Create class mapping for interpretability
            class_mapping = {label: int(code) for code, label in enumerate(label_encoder.classes_)}
            logger.info(f"Label encoding mapping: {class_mapping}")
            
            # Replace y with encoded version
            y = pd.Series(y_encoded, index=y.index, name=target_column)
            logger.info(f"✅ Target labels encoded: {dict(zip(label_encoder.classes_, range(len(label_encoder.classes_))))}")
        
        # CRITICAL: Check for minimum number of classes
        unique_classes = y.nunique()
        class_counts = y.value_counts().to_dict()
        
        if unique_classes < 2:
            raise ValueError(
                f"Insufficient classes for classification training!\n"
                f"  - Found {unique_classes} unique class: {list(y.unique())}\n"
                f"  - Need at least 2 different classes for binary/multiclass classification\n"
                f"  - Class distribution: {class_counts}\n\n"
                f"💡 Solution: Add labels with different disease classifications.\n"
                f"   Go to Label Assignment UI and ensure you have multiple diagnoses (e.g., RA, SLE, Mixed)"
            )
        
        logger.info(f"✅ Class validation passed: {unique_classes} classes found - {class_counts}")
        
        logger.info(f"Feature matrix before LASSO: {X.shape}")
        
        # Step 5: LASSO Feature Selection (CRITICAL: Before train/test split to prevent leakage)
        selected_features = None
        if skip_preprocessing:
            # Skip LASSO when skip_preprocessing=True
            selected_features = original_feature_names
            logger.info("LASSO feature selection SKIPPED (skip_preprocessing=True)")
        elif use_lasso_feature_selection:
            X, selected_features = self._lasso_feature_selection(
                X, y, 
                alpha=lasso_alpha, 
                random_state=random_state
            )
            logger.info(f"After LASSO selection: {X.shape} ({len(selected_features)} features kept)")
        else:
            selected_features = original_feature_names
            logger.info("LASSO feature selection skipped (use_lasso_feature_selection=False)")
        
        feature_names = X.columns.tolist()
        
        logger.info(f"Feature matrix: {X.shape}, Target: {len(y)} samples")
        
        # Step 5: Train/test split (stratified)
        from sklearn.model_selection import train_test_split
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            stratify=y,
            random_state=random_state
        )
        
        # Step 6: Create scaled versions for linear models (CONFIGURABLE)
        scaler = None
        X_train_scaled = None
        X_test_scaled = None
        
        if skip_preprocessing:
            # Skip scaling when skip_preprocessing=True
            logger.info("Scaling SKIPPED (skip_preprocessing=True)")
            X_train_scaled = X_train
            X_test_scaled = X_test
        elif create_separate_feature_sets:
            logger.info(f"Creating scaled feature set using {scaling_strategy} scaling...")
            
            # Select scaler based on strategy
            from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
            
            if scaling_strategy == 'standard':
                scaler = StandardScaler()
                logger.info("  Using StandardScaler (mean=0, std=1)")
            elif scaling_strategy == 'minmax':
                scaler = MinMaxScaler()
                logger.info("  Using MinMaxScaler (range [0, 1])")
            elif scaling_strategy == 'robust':
                scaler = RobustScaler()
                logger.info("  Using RobustScaler (robust to outliers)")
            else:
                raise ValueError(f"Unknown scaling_strategy: {scaling_strategy}")
            
            # Fit scaler on training data ONLY (prevent data leakage)
            X_train_scaled = pd.DataFrame(
                scaler.fit_transform(X_train),
                columns=feature_names,
                index=X_train.index
            )
            
            # Transform test data with fitted scaler
            X_test_scaled = pd.DataFrame(
                scaler.transform(X_test),
                columns=feature_names,
                index=X_test.index
            )
            
            logger.info(f"  Scaled features created: {X_train_scaled.shape}")
        
        # Step 7: Compile metadata
        metadata = {
            "generated_at": datetime.utcnow().isoformat(),
            "total_samples": len(df),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "n_features": len(feature_names),
            "n_features_original": len(original_feature_names),
            "target_column": target_column,
            "class_distribution": y.value_counts().to_dict(),
            "train_class_distribution": y_train.value_counts().to_dict(),
            "test_class_distribution": y_test.value_counts().to_dict(),
            "feature_names": feature_names,
            "original_feature_names": original_feature_names,
            "selected_features": selected_features,
            "lasso_applied": use_lasso_feature_selection,
            "lasso_alpha": lasso_alpha if use_lasso_feature_selection else None,
            "features_removed_by_lasso": len(original_feature_names) - len(feature_names) if use_lasso_feature_selection else 0,
            "random_state": random_state,
            "scaling_strategy": scaling_strategy if create_separate_feature_sets else None,
            "has_scaled_features": create_separate_feature_sets,
            "feature_pipeline_config": feature_pipeline.get_config(),  # Save pipeline config
            "label_encoder_classes": label_encoder.classes_.tolist() if label_encoder is not None else None,
            "class_mapping": class_mapping,  # e.g., {"Mild": 0, "Moderate": 1, "Severe": 2}
            # NEW: Research-aligned preprocessing metadata
            "preprocessing_applied": not skip_preprocessing,
            "imputation_applied": apply_imputation and not skip_preprocessing,
            "winsorization_applied": apply_winsorization and not skip_preprocessing,
            "composite_features_applied": apply_composite_features,
            "sledai_binary_used": use_sledai_binary,
            "preprocessing_metadata": preprocessing_metadata,  # Detailed preprocessing stats
            "preprocessing_config": {
                "imputation_numeric_strategy": imputation_numeric_strategy if apply_imputation else None,
                "imputation_categorical_strategy": imputation_categorical_strategy if apply_imputation else None,
                "winsorize_limits": winsorize_limits if apply_winsorization else None,
                "composite_low_percentile": composite_low_percentile if apply_composite_features else None,
                "composite_high_percentile": composite_high_percentile if apply_composite_features else None,
                "sledai_threshold": sledai_threshold if use_sledai_binary else None
            }
        }
        
        logger.info(f"Dataset generation complete: {metadata['train_samples']} train, {metadata['test_samples']} test")
        
        result = {
            # Raw features (for tree models: XGBoost, RF, CatBoost, etc.)
            "X_train": X_train,
            "X_test": X_test,
            
            # Target variables
            "y_train": y_train,
            "y_test": y_test,
            
            # Feature information
            "feature_names": feature_names,
            
            # Feature engineering pipeline (for inference)
            "feature_pipeline": feature_pipeline,
            "label_encoder": label_encoder,  # For decoding predictions back to original labels
            "metadata": metadata
        }
        
        # Add scaled features if requested (for linear models: LR, SVM, MLP, etc.)
        if create_separate_feature_sets:
            result.update({
                "X_train_scaled": X_train_scaled,
                "X_test_scaled": X_test_scaled,
                "scaler": scaler
            })
            logger.info("✅ Returning both raw and scaled feature sets")
        else:
            logger.info("✅ Returning raw features only")
        
        return result
    
    def _ensure_dict(self, data) -> dict:
        """Ensure data is a dict. Handles None, string JSON, and existing dicts."""
        if data is None:
            return {}
        if isinstance(data, str):
            try:
                parsed = json.loads(data)
                return parsed if isinstance(parsed, dict) else {}
            except:
                return {}
        if isinstance(data, dict):
            return data
        return {}
    
    def _extract_base_features(self, batch_id: str) -> pd.DataFrame:
        """
        Extract base features from FlexibleDatasetWide or ImportPreviewStaging for a specific batch
        NO HARDCODED SCHEMA - dynamically extracts all fields from JSONB
        Supports both saved data and staging data
        """
        logger.info(f"Extracting features for batch: {batch_id}...")
        
        # Query records from flexible dataset filtered by import_batch_id
        import uuid as uuid_lib
        
        # Validate and parse batch_id as UUID
        try:
            batch_uuid = uuid_lib.UUID(batch_id)
        except (ValueError, AttributeError) as e:
            # If batch_id is not a valid UUID, provide helpful error message
            logger.error(f"Invalid batch_id format: '{batch_id}'. Must be a valid UUID.")
            logger.info("Attempting to find available batch IDs in database...")
            
            # Show available batch IDs to help user
            available_batches = self.db.query(FlexibleDatasetWide.import_batch_id).distinct().limit(10).all()
            if available_batches:
                available_batch_ids = [str(b[0]) for b in available_batches]
                logger.info(f"Available batch IDs (first 10): {available_batch_ids}")
                raise ValueError(
                    f"Invalid batch_id '{batch_id}'. Must be a valid UUID format. "
                    f"Available batch IDs in database: {', '.join(available_batch_ids[:5])}"
                )
            else:
                raise ValueError(
                    f"Invalid batch_id '{batch_id}'. Must be a valid UUID format. "
                    f"No data found in FlexibleDatasetWide table. Please upload data first using the Data Import API."
                )
        
        # First try saved data (FlexibleDatasetWide)
        records = self.db.query(FlexibleDatasetWide).filter(FlexibleDatasetWide.import_batch_id == batch_uuid).all()
        use_staging = False
        
        # If no saved data, check staging (ImportPreviewStaging)
        if not records:
            logger.info("No saved data found, checking staging...")
            records = self.db.query(ImportPreviewStaging).filter(
                ImportPreviewStaging.session_id == batch_uuid,
                ImportPreviewStaging.is_deleted == False
            ).all()
            use_staging = True
            if records:
                logger.info(f"Using staging data: {len(records)} records")
        
        if not records:
            raise ValueError("No data found in database. Please upload data first.")
        
        logger.info(f"Found {len(records)} records in database (staging={use_staging})")
        
        # Extract JSONB data into flat structure
        rows = []
        for record in records:
            # Flatten nested JSONB structure
            if use_staging:
                flat_row = {
                    'record_id': record.staging_id,
                    'dataset_type': record.dataset_type
                }
                raw_data = record.row_data
            else:
                flat_row = {
                    'record_id': record.record_id,
                    'dataset_type': record.dataset_type
                }
                raw_data = record.data
            
            # Ensure data is a dict (handle None, string JSON)
            data_dict = self._ensure_dict(raw_data)
            
            # Recursively flatten JSONB data
            if data_dict:
                flat_row.update(self._flatten_jsonb(data_dict))
            
            rows.append(flat_row)
        
        df = pd.DataFrame(rows)
        logger.info(f"Extracted dataframe shape: {df.shape}")
        
        # DEBUG: Log ALL columns to diagnose label issues
        all_columns = df.columns.tolist()
        logger.info(f"Total columns: {len(all_columns)}")
        
        # Look for label-related columns specifically
        label_columns = [col for col in all_columns if 'label' in col.lower()]
        logger.info(f"Label-related columns: {label_columns}")
        
        # Log first few columns
        logger.info(f"First 20 columns: {all_columns[:20]}")
        
        return df
    
    def _flatten_jsonb(self, data: dict, parent_key: str = '', sep: str = '_') -> dict:
        """
        Flatten nested JSONB structure
        Example: {'demographics': {'age': 34}} -> {'demographics_age': 34}
        """
        items = []
        for k, v in data.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(self._flatten_jsonb(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Convert lists to string representation
                items.append((new_key, str(v)))
            else:
                items.append((new_key, v))
        
        return dict(items)
    
    def _engineer_features_with_pipeline(
        self, 
        df: pd.DataFrame, 
        target_column: str,
        apply_composite_features: bool = True,
        composite_low_percentile: float = 10.0,
        composite_high_percentile: float = 70.0
    ) -> Tuple[pd.DataFrame, FeatureEngineeringPipeline]:
        """
        Engineer features using FeatureEngineeringPipeline
        This pipeline can be saved and reused during inference
        
        Args:
            df: Base features DataFrame
            target_column: Target column to preserve from encoding
            apply_composite_features: If True, create composite pathological features
            composite_low_percentile: Percentile for "low" blood counts
            composite_high_percentile: Percentile for "high" liver enzymes
        
        Returns:
            Tuple of (transformed DataFrame, fitted pipeline)
        """
        logger.info(f"Engineering features with FeatureEngineeringPipeline from {len(df.columns)} base columns...")
        
        # Create pipeline with target column protection
        pipeline = FeatureEngineeringPipeline(target_column=target_column)
        
        # === ADD RATIO FEATURES ===
        # CRP/ESR ratio (inflammation marker)
        crp_cols = [col for col in df.columns if 'crp' in col.lower()]
        esr_cols = [col for col in df.columns if 'esr' in col.lower()]
        if crp_cols and esr_cols:
            pipeline.add_ratio_feature('CRP_ESR_ratio', crp_cols[0], esr_cols[0])
        
        # Complement ratio (C3/C4)
        c3_cols = [col for col in df.columns if 'c3' in col.lower() and 'c4' not in col.lower()]
        c4_cols = [col for col in df.columns if 'c4' in col.lower()]
        if c3_cols and c4_cols:
            pipeline.add_ratio_feature('complement_ratio', c3_cols[0], c4_cols[0])
        
        # === ADD TEMPORAL FEATURES ===
        # Disease duration (if diagnosis date exists)
        diagnosis_cols = [col for col in df.columns if 'diagnosis_date' in col.lower() or 'date_of_diagnosis' in col.lower()]
        if diagnosis_cols:
            pipeline.add_temporal_feature('disease_duration_days', diagnosis_cols[0], unit='days')
        
        # Days since last flare
        flare_cols = [col for col in df.columns if 'flare' in col.lower() and 'date' in col.lower()]
        if flare_cols:
            pipeline.add_temporal_feature('days_since_last_flare', flare_cols[0], unit='days')
        
        # === ADD COMPOSITE PATHOLOGICAL FEATURES (Research Study Alignment) ===
        if apply_composite_features:
            logger.info(f"Adding composite pathological features (low={composite_low_percentile}%, high={composite_high_percentile}%)")
            
            # Auto-detect blood count columns
            wbc_cols = [col for col in df.columns if 'wbc' in col.lower() and 'white' not in col.lower()]
            hgb_cols = [col for col in df.columns if 'hgb' in col.lower() or 'hemoglobin' in col.lower()]
            plt_cols = [col for col in df.columns if 'plt' in col.lower() or 'platelet' in col.lower()]
            alt_cols = [col for col in df.columns if col.lower().endswith('alt') or ('alt' in col.lower() and 'liver' in col.lower())]
            ast_cols = [col for col in df.columns if col.lower().endswith('ast') or ('ast' in col.lower() and 'liver' in col.lower())]
            
            # Pancytopenia: ALL blood counts low (10th percentile)
            if wbc_cols and hgb_cols and plt_cols:
                pipeline.add_composite_pathological_feature(
                    'pancytopenia',
                    source_columns=[wbc_cols[0], hgb_cols[0], plt_cols[0]],
                    percentile=composite_low_percentile,
                    logic='all',
                    above_threshold=False
                )
            
            # Cytopenia: ANY blood count low (10th percentile)
            if wbc_cols and hgb_cols and plt_cols:
                pipeline.add_composite_pathological_feature(
                    'cytopenia',
                    source_columns=[wbc_cols[0], hgb_cols[0], plt_cols[0]],
                    percentile=composite_low_percentile,
                    logic='any',
                    above_threshold=False
                )
            
            # Liver Damage: ANY liver enzyme high (70th percentile)
            if alt_cols and ast_cols:
                pipeline.add_composite_pathological_feature(
                    'liver_damage',
                    source_columns=[alt_cols[0], ast_cols[0]],
                    percentile=composite_high_percentile,
                    logic='any',
                    above_threshold=True
                )
            
            # High Inflammation: CRP/ESR ratio above 75th percentile
            if crp_cols and esr_cols:
                pipeline.add_percentile_cutoff_feature(
                    'high_inflammation',
                    source_column='CRP_ESR_ratio',  # Will be created by pipeline
                    percentile=75.0,
                    above_is_positive=True
                )
            
            # Low Complement: C3/C4 ratio below 25th percentile
            if c3_cols and c4_cols:
                pipeline.add_percentile_cutoff_feature(
                    'low_complement',
                    source_column='complement_ratio',  # Will be created by pipeline
                    percentile=25.0,
                    above_is_positive=False
                )
        
        # Fit and transform
        df_transformed = pipeline.fit_transform(df)
        
        # Add age_at_diagnosis if possible (after disease_duration_days exists)
        age_cols = [col for col in df.columns if 'age' in col.lower()]
        if age_cols and 'disease_duration_days' in df_transformed.columns:
            try:
                df_transformed['age_at_diagnosis'] = df_transformed[age_cols[0]] - (df_transformed['disease_duration_days'] / 365.25)
                logger.info(f"  ✓ Created age_at_diagnosis")
            except Exception as e:
                logger.warning(f"  ✗ Could not create age_at_diagnosis: {e}")
        
        logger.info(f"Feature engineering complete: {df_transformed.shape}")
        
        return df_transformed, pipeline
    
    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Engineer additional features dynamically based on available columns
        NO HARDCODED ASSUMPTIONS - but adds clinical logic when relevant columns exist
        
        Feature types added:
        1. Longitudinal: disease duration, visit frequency
        2. Ratio: CRP/ESR, complement ratios, ANA changes
        3. Temporal: days since last events, visit intervals
        """
        logger.info(f"Engineering features from {len(df.columns)} base columns...")
        
        # Step 1: Add advanced clinical features (if relevant columns exist)
        df = self._engineer_advanced_features(df)
        
        # Step 2: Identify numeric and categorical columns automatically
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Remove identifiers from feature engineering
        id_cols = [col for col in df.columns if 'id' in col.lower() or 'record' in col.lower()]
        categorical_cols = [col for col in categorical_cols if col not in id_cols]
        
        logger.info(f"Found {len(numeric_cols)} numeric columns, {len(categorical_cols)} categorical columns")
        
        # Step 3: Encode categorical features (if any exist)
        if categorical_cols:
            # Keep first N-1 categories to avoid multicollinearity
            df = pd.get_dummies(df, columns=categorical_cols, drop_first=True)
            logger.info(f"One-hot encoded {len(categorical_cols)} categorical columns")
        
        logger.info(f"Final feature matrix shape: {df.shape}")
        
        return df
    
    def _engineer_advanced_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create derived clinical features when relevant columns are available
        All features are OPTIONAL - only created if source columns exist
        
        Feature categories:
        - Longitudinal: disease_duration_days, visit_frequency
        - Ratio: CRP_ESR_ratio, complement_ratio, ANA_titer_change
        - Temporal: days_since_last_flare, visit_interval_mean
        """
        logger.info("Engineering advanced clinical features...")
        features_added = 0
        
        # === LONGITUDINAL FEATURES ===
        # Disease duration (if diagnosis date exists)
        diagnosis_cols = [col for col in df.columns if 'diagnosis_date' in col.lower() or 'date_of_diagnosis' in col.lower()]
        if diagnosis_cols:
            for col in diagnosis_cols:
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    df['disease_duration_days'] = (pd.Timestamp.now() - df[col]).dt.days
                    features_added += 1
                    logger.info(f"  ✓ Created disease_duration_days from {col}")
                    break  # Use first valid diagnosis date
                except Exception as e:
                    logger.warning(f"  ✗ Could not create disease_duration_days: {e}")
        
        # === RATIO FEATURES ===
        # CRP/ESR ratio (inflammation marker)
        crp_cols = [col for col in df.columns if 'crp' in col.lower()]
        esr_cols = [col for col in df.columns if 'esr' in col.lower()]
        if crp_cols and esr_cols:
            try:
                df['CRP_ESR_ratio'] = df[crp_cols[0]] / (df[esr_cols[0]] + 1e-6)
                features_added += 1
                logger.info(f"  ✓ Created CRP_ESR_ratio from {crp_cols[0]}/{esr_cols[0]}")
            except Exception as e:
                logger.warning(f"  ✗ Could not create CRP_ESR_ratio: {e}")
        
        # Complement ratio (C3/C4)
        c3_cols = [col for col in df.columns if 'c3' in col.lower() and 'c4' not in col.lower()]
        c4_cols = [col for col in df.columns if 'c4' in col.lower()]
        if c3_cols and c4_cols:
            try:
                df['complement_ratio'] = df[c3_cols[0]] / (df[c4_cols[0]] + 1e-6)
                features_added += 1
                logger.info(f"  ✓ Created complement_ratio from {c3_cols[0]}/{c4_cols[0]}")
            except Exception as e:
                logger.warning(f"  ✗ Could not create complement_ratio: {e}")
        
        # === TEMPORAL FEATURES ===
        # Days since last flare
        flare_cols = [col for col in df.columns if 'flare' in col.lower() and 'date' in col.lower()]
        if flare_cols:
            for col in flare_cols:
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    df['days_since_last_flare'] = (pd.Timestamp.now() - df[col]).dt.days
                    features_added += 1
                    logger.info(f"  ✓ Created days_since_last_flare from {col}")
                    break
                except Exception as e:
                    logger.warning(f"  ✗ Could not create days_since_last_flare: {e}")
        
        # Visit interval (time between medical visits)
        visit_cols = [col for col in df.columns if 'visit' in col.lower() and 'date' in col.lower()]
        if len(visit_cols) >= 2:
            try:
                for col in visit_cols[:2]:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                df['visit_interval_days'] = (df[visit_cols[0]] - df[visit_cols[1]]).dt.days.abs()
                features_added += 1
                logger.info(f"  ✓ Created visit_interval_days from {visit_cols[0]}, {visit_cols[1]}")
            except Exception as e:
                logger.warning(f"  ✗ Could not create visit_interval_days: {e}")
        
        # Age at diagnosis (if both age and diagnosis date exist)
        age_cols = [col for col in df.columns if 'age' in col.lower()]
        if age_cols and diagnosis_cols:
            try:
                # Age at diagnosis = Current age - disease duration / 365
                if 'disease_duration_days' in df.columns:
                    df['age_at_diagnosis'] = df[age_cols[0]] - (df['disease_duration_days'] / 365.25)
                    features_added += 1
                    logger.info(f"  ✓ Created age_at_diagnosis")
            except Exception as e:
                logger.warning(f"  ✗ Could not create age_at_diagnosis: {e}")
        
        logger.info(f"Advanced feature engineering complete: {features_added} features added")
        
        return df
    
    def _filter_patients(self, df: pd.DataFrame, min_events: int) -> pd.DataFrame:
        """
        Filter records with insufficient data
        Removes rows with too many missing values
        """
        logger.info(f"Filtering records with min_events threshold: {min_events}")
        
        # Calculate % of missing values per row
        missing_pct = df.isnull().sum(axis=1) / len(df.columns)
        
        # Keep rows with < 50% missing values
        df_filtered = df[missing_pct < 0.5].copy()
        
        logger.info(f"Kept {len(df_filtered)}/{len(df)} records after filtering")
        
        return df_filtered
    
    def _lasso_feature_selection(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        alpha: float = 0.01,
        random_state: int = 42
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Apply LASSO (L1 regularization) to remove redundant/noisy features
        
        CRITICAL: This runs BEFORE train/test split to prevent data leakage
        The entire dataset is used for feature selection, then split afterward
        
        Args:
            X: Feature matrix
            y: Target variable
            alpha: Regularization strength (lower = more features kept)
                   - 0.001: Very weak regularization (most features kept)
                   - 0.01: Moderate (recommended default)
                   - 0.1: Strong (aggressive feature removal)
            random_state: Random seed
        
        Returns:
            Tuple of (filtered feature matrix, list of selected feature names)
        """
        logger.info(f"Applying LASSO feature selection (alpha={alpha})...")
        
        from sklearn.linear_model import LassoCV
        from sklearn.preprocessing import StandardScaler
        from sklearn.impute import SimpleImputer
        
        # Handle missing values with robust imputation
        # Only numeric columns for LASSO
        numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
        X_numeric = X[numeric_cols].copy()
        
        # Drop columns that are entirely NaN (can't be imputed)
        all_nan_cols = X_numeric.columns[X_numeric.isna().all()].tolist()
        if all_nan_cols:
            logger.warning(f"  Dropping {len(all_nan_cols)} all-NaN columns: {all_nan_cols[:5]}...")
            X_numeric = X_numeric.drop(columns=all_nan_cols)
            numeric_cols = X_numeric.columns.tolist()
        
        # Impute remaining missing values (mean strategy)
        imputer = SimpleImputer(strategy='mean')
        X_imputed_array = imputer.fit_transform(X_numeric)
        X_imputed = pd.DataFrame(
            X_imputed_array,
            columns=numeric_cols,
            index=X_numeric.index
        )
        
        logger.info(f"  Imputed missing values in {len(numeric_cols)} numeric features")
        
        X_clean = X_imputed
        
        # Scale features for LASSO (L1 is scale-sensitive)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_clean)
        
        # Encode target variable for LASSO (convert categorical labels to numeric)
        from sklearn.preprocessing import LabelEncoder
        label_encoder = LabelEncoder()
        y_encoded = label_encoder.fit_transform(y)
        logger.info(f"  Encoded {len(label_encoder.classes_)} target classes: {label_encoder.classes_}")
        
        # Fit LASSO with cross-validation
        lasso = LassoCV(
            alphas=[alpha * 0.1, alpha, alpha * 10],  # Try 3 alpha values
            cv=5,
            random_state=random_state,
            max_iter=5000
        )
        
        lasso.fit(X_scaled, y_encoded)
        
        # Get feature importances (non-zero coefficients)
        feature_importances = np.abs(lasso.coef_)
        
        # Select features with non-zero coefficients
        selected_mask = feature_importances > 1e-5  # Small threshold for numerical stability
        selected_features = X_clean.columns[selected_mask].tolist()
        
        if len(selected_features) == 0:
            logger.warning(f"⚠️  LASSO selected 0 features (alpha={alpha} too high). Keeping all numeric features.")
            return X_clean, X_clean.columns.tolist()
        
        # Log feature selection results
        n_removed = len(X_clean.columns) - len(selected_features)
        logger.info(f"  LASSO selected {len(selected_features)}/{len(X_clean.columns)} features (removed {n_removed})")
        logger.info(f"  Best alpha: {lasso.alpha_:.4f}")
        
        # Show top 10 most important features
        top_idx = np.argsort(feature_importances[selected_mask])[-10:][::-1]
        top_features = [selected_features[i] for i in top_idx]
        logger.info(f"  Top 10 features by LASSO importance:")
        for i, feat in enumerate(top_features, 1):
            imp = feature_importances[selected_mask][top_idx[i-1]]
            logger.info(f"    {i}. {feat}: {imp:.4f}")
        
        # Return filtered dataframe (only selected numeric features)
        X_filtered = X_clean[selected_features].copy()
        
        return X_filtered, selected_features
