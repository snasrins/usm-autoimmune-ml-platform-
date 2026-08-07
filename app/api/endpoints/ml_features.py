"""
Feature Engineering API Endpoints
Apply feature engineering transformations to datasets
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging
import pandas as pd
from datetime import datetime

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.schemas.feature_engineering import (
    FeatureEngineeringRequest,
    FeatureEngineeringResponse,
    FeatureInfo,
    FeatureEngineeringStatus
)
from app.services.ml_bridge_service import MLBridgeService
from app.ml.feature_engineering_pipeline import FeatureEngineeringPipeline

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/engineer-features", response_model=FeatureEngineeringResponse)
async def engineer_features(
    request: FeatureEngineeringRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Apply feature engineering transformations to a dataset
    
    Creates new features:
    - Biomarker ratios (CRP/ESR, NLR, PLR)
    - Temporal features (disease duration)
    - Derived features (inflammation score, organ involvement)
    - Categorical encoding (automatic)
    """
    try:
        logger.info(f"Feature engineering requested for batch {request.import_batch_id} by user {current_user.email}")
        
        # Load data through ML Bridge
        bridge = MLBridgeService(db)
        data_result = bridge.prepare_data_for_ml(
            import_batch_id=request.import_batch_id,
            target_column=request.target_column,
            validate=False,
            drop_unlabeled=False
        )
        
        if not data_result['success']:
            raise HTTPException(status_code=400, detail=f"Failed to load dataset: {data_result.get('error')}")
        
        df = data_result['df']
        original_columns = df.shape[1]
        logger.info(f"Loaded {len(df)} records with {original_columns} features")
        
        # DEBUG: Log available columns
        available_columns = list(df.columns)
        logger.info(f"Available columns ({len(available_columns)}): {', '.join(sorted(available_columns))}")
        
        # Initialize feature engineering pipeline
        pipeline = FeatureEngineeringPipeline(target_column=request.target_column)
        new_features: List[FeatureInfo] = []
        skipped_features = []
        
        # Add ratio features
        if request.enable_ratios:
            if request.crp_esr_ratio:
                if 'biomarkers_crp' in df.columns and 'biomarkers_esr' in df.columns:
                    pipeline.add_ratio_feature('crp_esr_ratio', 'biomarkers_crp', 'biomarkers_esr')
                    new_features.append(FeatureInfo(
                        name='crp_esr_ratio',
                        type='ratio',
                        description='C-Reactive Protein / Erythrocyte Sedimentation Rate',
                        source_columns=['biomarkers_crp', 'biomarkers_esr']
                    ))
                elif 'lab_results_crp' in df.columns and 'lab_results_esr' in df.columns:
                    pipeline.add_ratio_feature('crp_esr_ratio', 'lab_results_crp', 'lab_results_esr')
                    new_features.append(FeatureInfo(
                        name='crp_esr_ratio',
                        type='ratio',
                        description='C-Reactive Protein / Erythrocyte Sedimentation Rate',
                        source_columns=['lab_results_crp', 'lab_results_esr']
                    ))
                elif 'crp' in df.columns and 'esr' in df.columns:
                    pipeline.add_ratio_feature('crp_esr_ratio', 'crp', 'esr')
                    new_features.append(FeatureInfo(
                        name='crp_esr_ratio',
                        type='ratio',
                        description='C-Reactive Protein / Erythrocyte Sedimentation Rate',
                        source_columns=['crp', 'esr']
                    ))
                else:
                    skipped_features.append({
                        'name': 'crp_esr_ratio',
                        'reason': 'Missing columns: need CRP and ESR columns'
                    })
            
            if request.nlr_ratio:
                if 'hematology_neutrophils' in df.columns and 'hematology_lymphocytes' in df.columns:
                    pipeline.add_ratio_feature('nlr', 'hematology_neutrophils', 'hematology_lymphocytes')
                    new_features.append(FeatureInfo(
                        name='nlr',
                        type='ratio',
                        description='Neutrophil-Lymphocyte Ratio (NLR) - inflammation marker',
                        source_columns=['hematology_neutrophils', 'hematology_lymphocytes']
                    ))
                elif 'other_neu%' in df.columns and 'other_lym%' in df.columns:
                    pipeline.add_ratio_feature('nlr', 'other_neu%', 'other_lym%')
                    new_features.append(FeatureInfo(
                        name='nlr',
                        type='ratio',
                        description='Neutrophil-Lymphocyte Ratio (NLR) - inflammation marker',
                        source_columns=['other_neu%', 'other_lym%']
                    ))
                elif 'neutrophils' in df.columns and 'lymphocytes' in df.columns:
                    pipeline.add_ratio_feature('nlr', 'neutrophils', 'lymphocytes')
                    new_features.append(FeatureInfo(
                        name='nlr',
                        type='ratio',
                        description='Neutrophil-Lymphocyte Ratio (NLR) - inflammation marker',
                        source_columns=['neutrophils', 'lymphocytes']
                    ))
                else:
                    skipped_features.append({
                        'name': 'nlr',
                        'reason': 'Missing columns: need neutrophil and lymphocyte columns'
                    })
            
            if request.plr_ratio:
                if 'heother_plt' in df.columns and 'other_lym%' in df.columns:
                    pipeline.add_ratio_feature('plr', 'other_plt', 'other_lym%')
                    new_features.append(FeatureInfo(
                        name='plr',
                        type='ratio',
                        description='Platelet-Lymphocyte Ratio (PLR) - inflammatory state marker',
                        source_columns=['other_plt', 'other_lym%']
                    ))
                elif 'platelets' in df.columns and 'lymphocytes' in df.columns:
                    pipeline.add_ratio_feature('plr', 'platelets', 'lymphocytes')
                    new_features.append(FeatureInfo(
                        name='plr',
                        type='ratio',
                        description='Platelet-Lymphocyte Ratio (PLR) - inflammatory state marker',
                        source_columns=['platelets', 'lymphocytes']
                    ))
                elif 'platelet_count' in df.columns and 'lymphocytes' in df.columns:
                    pipeline.add_ratio_feature('plr', 'platelet_count', 'lymphocytes')
                    new_features.append(FeatureInfo(
                        name='plr',
                        type='ratio',
                        description='Platelet-Lymphocyte Ratio (PLR) - inflammatory state marker',
                        source_columns=['platelet_count', 'lymphocytes']
                    ))
                else:
                    skipped_features.append({
                        'name': 'plr',
                        'reason': 'Missing columns: need platelet and lymphocyte columns'
                    })
        
        # Add temporal features
        if request.enable_temporal:
            if request.disease_duration:
                if 'clinical_diagnosis_date' in df.columns:
                    pipeline.add_temporal_feature(
                        'disease_duration_years',
                        'clinical_diagnosis_date',
                        unit='years'
                    )
                    new_features.append(FeatureInfo(
                        name='disease_duration_years',
                        type='temporal',
                        description='Years since disease diagnosis',
                        source_columns=['clinical_diagnosis_date']
                    ))
                elif 'temporal_date_diagnosed' in df.columns:
                    pipeline.add_temporal_feature(
                        'disease_duration_years',
                        'temporal_date_diagnosed',
                        unit='years'
                    )
                    new_features.append(FeatureInfo(
                        name='disease_duration_years',
                        type='temporal',
                        description='Years since disease diagnosis',
                        source_columns=['temporal_date_diagnosed']
                    ))
                else:
                    skipped_features.append({
                        'name': 'disease_duration_years',
                        'reason': 'Missing columns: need diagnosis date column'
                    })
        
        # Add derived features
        if request.enable_derived:
            if request.inflammation_score:
                if 'biomarkers_crp' in df.columns and 'biomarkers_esr' in df.columns:
                    pipeline.add_derived_feature(
                        'inflammation_index',
                        ['biomarkers_crp', 'biomarkers_esr'],
                        'mean'
                    )
                    new_features.append(FeatureInfo(
                        name='inflammation_index',
                        type='derived',
                        description='Combined inflammation score (mean of CRP and ESR)',
                        source_columns=['biomarkers_crp', 'biomarkers_esr']
                    ))
                elif 'lab_results_crp' in df.columns and 'lab_results_esr' in df.columns:
                    pipeline.add_derived_feature(
                        'inflammation_index',
                        ['lab_results_crp', 'lab_results_esr'],
                        'mean'
                    )
                    new_features.append(FeatureInfo(
                        name='inflammation_index',
                        type='derived',
                        description='Combined inflammation score (mean of CRP and ESR)',
                        source_columns=['lab_results_crp', 'lab_results_esr']
                    ))
                else:
                    skipped_features.append({
                        'name': 'inflammation_index',
                        'reason': 'Missing columns: need CRP and ESR columns'
                    })
            
            if request.organ_involvement:
                organ_cols = [col for col in df.columns if 'clinical_' in col and 'involvement' in col]
                if len(organ_cols) > 0:
                    pipeline.add_derived_feature(
                        'organ_involvement_count',
                        organ_cols,
                        'sum'
                    )
                    new_features.append(FeatureInfo(
                        name='organ_involvement_count',
                        type='derived',
                        description='Number of affected organ systems',
                        source_columns=organ_cols
                    ))
        
        # Apply feature engineering
        df_engineered = pipeline.fit_transform(df)
        engineered_columns = df_engineered.shape[1]
        features_added = engineered_columns - original_columns
        
        logger.info(f"Feature engineering complete: {original_columns} → {engineered_columns} features (+{features_added})")
        if skipped_features:
            logger.warning(f"Skipped {len(skipped_features)} features due to missing columns: {skipped_features}")
        
        # Persist the user-configured FE specs to MinIO so the training pipeline
        # can re-apply the same transformations during dataset generation.
        try:
            import json as _json
            import io as _io
            import os as _os
            from app.services.minio_service import MinIOService as _MinIO
            _minio_svc = _MinIO(
                endpoint=_os.getenv("MINIO_ENDPOINT", "minio:9000"),
                access_key=_os.getenv("MINIO_ROOT_USER", "minio_admin"),
                secret_key=_os.getenv("MINIO_ROOT_PASSWORD", "MinIO_P@ssw0rd_2026"),
                secure=_os.getenv("MINIO_SECURE", "false").lower() == "true"
            )
            _fe_payload = {
                'feature_specs': pipeline.feature_specs,
                'applied_at': datetime.utcnow().isoformat(),
                'applied_feature_names': [f.name for f in new_features],
                'import_batch_id': request.import_batch_id,
            }
            _config_bytes = _json.dumps(_fe_payload).encode('utf-8')
            _obj_name = f"feature-engineering/{request.import_batch_id}/user_specs.json"
            _minio_svc.client.put_object(
                "ml-datasets",
                _obj_name,
                _io.BytesIO(_config_bytes),
                length=len(_config_bytes),
                content_type="application/json"
            )
            logger.info(f"Saved FE user specs to MinIO: {_obj_name}")
        except Exception as _fe_save_err:
            logger.warning(f"Could not save FE specs to MinIO (non-fatal): {_fe_save_err}")

        return FeatureEngineeringResponse(
            success=True,
            message=f"Successfully engineered {features_added} new features",
            import_batch_id=request.import_batch_id,
            original_feature_count=original_columns,
            engineered_feature_count=engineered_columns,
            new_features=new_features,
            features_added=features_added,
            skipped_features=skipped_features,
            available_columns=sorted(available_columns)
        )
        
    except Exception as e:
        logger.error(f"Feature engineering failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Feature engineering failed: {str(e)}")


@router.get("/feature-status/{import_batch_id}", response_model=FeatureEngineeringStatus)
async def get_feature_engineering_status(
    import_batch_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get feature engineering status for a dataset
    
    Returns information about whether features have been engineered
    and what features exist.
    """
    try:
        # Load data to check features
        bridge = MLBridgeService(db)
        data_result = bridge.prepare_data_for_ml(
            import_batch_id=import_batch_id,
            validate=False,
            drop_unlabeled=False
        )
        
        if not data_result['success']:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        df = data_result['df']
        
        # Check for engineered feature markers
        engineered_features = [
            col for col in df.columns 
            if any(marker in col for marker in ['_ratio', '_index', '_duration', '_count', 'nlr', 'plr'])
        ]
        
        return FeatureEngineeringStatus(
            import_batch_id=import_batch_id,
            is_engineered=len(engineered_features) > 0,
            features_count=df.shape[1],
            engineered_features=engineered_features
        )
        
    except Exception as e:
        logger.error(f"Failed to get feature status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ────────────────────────────────────────────────────────────────────
# GET /feature-columns/{import_batch_id}
# Returns all numeric feature column names available for a batch.
# Used by the frontend clinician selection checklist.
# ────────────────────────────────────────────────────────────────────
@router.get("/feature-columns/{import_batch_id}")
async def get_feature_columns(
    import_batch_id: str,
    target_column: str = "labels_disease_classification",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return all available feature column names (excluding label/metadata columns)."""
    try:
        bridge = MLBridgeService(db)
        data_result = bridge.prepare_data_for_ml(
            import_batch_id=import_batch_id,
            target_column=target_column,
            validate=False,
            drop_unlabeled=False,
        )
        if not data_result["success"]:
            raise HTTPException(status_code=404, detail="Dataset not found or could not be loaded")

        df: pd.DataFrame = data_result["df"]

        # Exclude label columns, internal metadata, and string-only columns
        exclude_prefixes = ("labels_", "_labeling", "record_id", "patient_id", "id")
        feature_cols = [
            c for c in df.columns
            if not any(c.startswith(p) for p in exclude_prefixes)
            and c != target_column
        ]

        # Separate numeric from categorical
        numeric_cols = [c for c in feature_cols if pd.api.types.is_numeric_dtype(df[c])]
        categorical_cols = [c for c in feature_cols if c not in numeric_cols]

        return {
            "import_batch_id": import_batch_id,
            "total_features": len(feature_cols),
            "numeric_features": sorted(numeric_cols),
            "categorical_features": sorted(categorical_cols),
            "all_features": sorted(feature_cols),
            "n_rows": len(df),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_feature_columns failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ────────────────────────────────────────────────────────────────────
# POST /detect-correlations/{import_batch_id}
# Identifies feature pairs above a Pearson correlation threshold.
# Research basis: remove one from each highly-correlated pair before
# LASSO to reduce multicollinearity on small datasets.
# ────────────────────────────────────────────────────────────────────
@router.post("/detect-correlations/{import_batch_id}")
async def detect_correlated_features(
    import_batch_id: str,
    threshold: float = 0.85,
    target_column: str = "labels_disease_classification",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Compute Pearson correlation matrix and flag feature pairs
    whose |r| ≥ threshold.  For each correlated pair, one feature
    is recommended for removal (the one with lower variance).
    """
    import numpy as np

    if not (0.0 < threshold < 1.0):
        raise HTTPException(status_code=400, detail="threshold must be between 0 and 1")

    try:
        bridge = MLBridgeService(db)
        data_result = bridge.prepare_data_for_ml(
            import_batch_id=import_batch_id,
            target_column=target_column,
            validate=False,
            drop_unlabeled=False,
        )
        if not data_result["success"]:
            raise HTTPException(status_code=404, detail="Dataset not found")

        df: pd.DataFrame = data_result["df"]

        # Keep only numeric, non-label columns
        exclude_prefixes = ("labels_", "_labeling", "record_id", "patient_id", "id")
        numeric_cols = [
            c for c in df.columns
            if pd.api.types.is_numeric_dtype(df[c])
            and not any(c.startswith(p) for p in exclude_prefixes)
            and c != target_column
        ]

        if len(numeric_cols) < 2:
            return {"correlated_pairs": [], "features_to_remove": [], "threshold": threshold}

        corr_matrix = df[numeric_cols].corr(method="pearson").abs()

        # Collect pairs above threshold (upper triangle only, skip diagonal)
        correlated_pairs = []
        features_to_remove = set()
        for i in range(len(numeric_cols)):
            for j in range(i + 1, len(numeric_cols)):
                r = corr_matrix.iloc[i, j]
                if pd.isna(r) or r < threshold:
                    continue
                col_a = numeric_cols[i]
                col_b = numeric_cols[j]
                # Recommend removing the lower-variance feature
                var_a = float(df[col_a].var())
                var_b = float(df[col_b].var())
                remove = col_a if var_a <= var_b else col_b
                features_to_remove.add(remove)
                correlated_pairs.append({
                    "feature_a": col_a,
                    "feature_b": col_b,
                    "correlation": round(float(r), 4),
                    "recommended_remove": remove,
                })

        # Sort by descending |r|
        correlated_pairs.sort(key=lambda x: x["correlation"], reverse=True)

        return {
            "import_batch_id": import_batch_id,
            "threshold": threshold,
            "n_numeric_features": len(numeric_cols),
            "correlated_pairs": correlated_pairs,
            "features_to_remove": sorted(features_to_remove),
            "features_to_keep": sorted(set(numeric_cols) - features_to_remove),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"detect_correlated_features failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ────────────────────────────────────────────────────────────────────
# POST /lasso-feature-selection/{import_batch_id}
# LASSO (L1-penalised LogisticRegression) for classification tasks.
# Matches the research paper methodology: features whose coefficients
# are shrunk to zero are dropped; the rest are returned ranked by
# mean |coefficient| across classes.
# ────────────────────────────────────────────────────────────────────
@router.post("/lasso-feature-selection/{import_batch_id}")
async def run_lasso_feature_selection(
    import_batch_id: str,
    alpha: float = 0.00001,
    target_column: str = "labels_disease_classification",
    max_iter: int = 2000,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Run LASSO (L1) feature selection via LogisticRegression.

    For small datasets (n~100) the research framework recommends a very
    low alpha (0.00001–0.0001) so the L1 penalty is weak enough to keep
    most informative features rather than aggressively zeroing them out.

    Returns features ranked by mean |coefficient| across all classes,
    with zero-coefficient features marked as 'removed'.
    """
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.impute import SimpleImputer

    if alpha <= 0:
        raise HTTPException(status_code=400, detail="alpha must be > 0")

    try:
        bridge = MLBridgeService(db)
        data_result = bridge.prepare_data_for_ml(
            import_batch_id=import_batch_id,
            target_column=target_column,
            validate=False,
            drop_unlabeled=True,  # LASSO needs labels
        )
        if not data_result["success"]:
            raise HTTPException(status_code=404, detail=f"Dataset not found: {data_result.get('error')}")

        df: pd.DataFrame = data_result["df"]

        # Target vector
        if target_column not in df.columns:
            raise HTTPException(status_code=400, detail=f"Target column '{target_column}' not found in dataset")

        y_raw = df[target_column].dropna()
        if len(y_raw) < 10:
            raise HTTPException(status_code=400, detail="Too few labelled records for LASSO (need ≥ 10)")

        df = df.loc[y_raw.index]

        # Feature matrix — numeric only
        exclude_prefixes = ("labels_", "_labeling", "record_id", "patient_id", "id")
        feature_cols = [
            c for c in df.columns
            if pd.api.types.is_numeric_dtype(df[c])
            and not any(c.startswith(p) for p in exclude_prefixes)
            and c != target_column
        ]

        if not feature_cols:
            raise HTTPException(status_code=400, detail="No numeric feature columns found")

        X = df[feature_cols].values.astype(float)

        # Impute, then scale (LASSO is scale-dependent)
        imputer = SimpleImputer(strategy="median")
        X = imputer.fit_transform(X)

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Encode labels
        le = LabelEncoder()
        y = le.fit_transform(y_raw.astype(str))
        n_classes = len(le.classes_)

        # C = 1 / (n_samples * alpha)  — sklearn convention
        C_value = 1.0 / (max(len(y), 1) * alpha)

        clf = LogisticRegression(
            penalty="l1",
            solver="saga",
            C=C_value,
            multi_class="auto",
            max_iter=max_iter,
            random_state=42,
        )
        clf.fit(X_scaled, y)

        # coef_ shape: (n_classes, n_features) for multi-class, (1, n_features) for binary
        coef_matrix = np.abs(clf.coef_)
        mean_importance = coef_matrix.mean(axis=0)  # average across classes

        results = []
        for idx, col in enumerate(feature_cols):
            importance = float(mean_importance[idx])
            results.append({
                "feature": col,
                "mean_abs_coef": round(importance, 6),
                "selected": importance > 1e-8,  # non-zero coefficient
            })

        # Sort by importance descending
        results.sort(key=lambda x: x["mean_abs_coef"], reverse=True)
        selected = [r["feature"] for r in results if r["selected"]]
        removed = [r["feature"] for r in results if not r["selected"]]

        return {
            "import_batch_id": import_batch_id,
            "target_column": target_column,
            "alpha": alpha,
            "C_value": round(C_value, 6),
            "n_labeled_records": len(y),
            "n_classes": n_classes,
            "class_labels": list(le.classes_),
            "n_features_input": len(feature_cols),
            "n_features_selected": len(selected),
            "n_features_removed": len(removed),
            "features": results,          # all features with scores
            "selected_features": selected,
            "removed_features": removed,
            "converged": bool(clf.n_iter_[0] < max_iter) if hasattr(clf, "n_iter_") else True,
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"lasso_feature_selection failed: {e}\n{tb}")
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}\n\nTraceback:\n{tb}")
