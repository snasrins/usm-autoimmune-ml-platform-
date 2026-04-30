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
        
        # TODO: Save engineered dataset back to database or cache
        # For now, just return the statistics
        
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
