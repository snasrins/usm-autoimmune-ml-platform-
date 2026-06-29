"""
ML Training API Endpoints
FastAPI routes for training ML models
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
import uuid
import numpy as np
import pandas as pd
import json
import io
from datetime import datetime

from app.core.database import get_db, SessionLocal
from app.api.deps import get_current_active_user, require_researcher_or_admin
from app.services.minio_service import MinIOService
from app.models.user import User
from app.models.training_job import TrainingJob, JobType, JobStatus
from app.schemas.training import (
    DatasetGenerationRequest, DatasetGenerationResponse,
    FeatureSelectionRequest, FeatureSelectionResponse,
    BaseModelTrainingRequest, BaseModelTrainingResponse,
    EnsembleTrainingRequest, EnsembleTrainingResponse,
    FullPipelineTrainingRequest, FullPipelineTrainingResponse,
    TrainingJobStatus, TrainingStatus,
    ModelListResponse, TrainedModelInfo,
    ModelEvaluationRequest, ModelEvaluationResponse,
    ModelComparisonRequest, ModelComparisonResponse,
    TrainingHistoryResponse, TrainingHistoryItem
)

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory job tracking (DEPRECATED - now using PostgreSQL)
# Kept for backward compatibility during migration
training_jobs = {}

# In-memory trained models registry (TODO: move to database + MinIO)
trained_models = {}


# ===== Helper Functions =====

def sanitize_for_json(obj):
    """Recursively sanitize dict/list for JSON serialization (remove NaN/Inf)"""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, np.ndarray):
        # Convert numpy arrays to list (handles multiclass 2D arrays)
        return sanitize_for_json(obj.tolist())
    elif isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return 0.0
        return obj
    elif isinstance(obj, np.floating):
        if np.isnan(obj) or np.isinf(obj):
            return 0.0
        return float(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    else:
        return obj


# ===== Persistent Storage Helper Functions =====

def get_minio_service() -> MinIOService:
    """Get MinIO service instance"""
    import os
    return MinIOService(
        endpoint=os.getenv("MINIO_ENDPOINT", "minio:9000"),
        access_key=os.getenv("MINIO_ROOT_USER", "minio_admin"),
        secret_key=os.getenv("MINIO_ROOT_PASSWORD", "MinIO_P@ssw0rd_2026"),
        secure=os.getenv("MINIO_SECURE", "false").lower() == "true"
    )


def save_oof_predictions_to_minio(job_id: str, oof_predictions: np.ndarray) -> str:
    """
    Save OOF predictions to MinIO for later retrieval
    
    Args:
        job_id: Training job ID
        oof_predictions: OOF predictions array
    
    Returns:
        MinIO path to the saved predictions
    """
    try:
        minio_service = get_minio_service()
        
        # Convert to JSON for storage
        oof_data = {
            'job_id': job_id,
            'predictions': oof_predictions.tolist() if hasattr(oof_predictions, 'tolist') else oof_predictions,
            'shape': oof_predictions.shape if hasattr(oof_predictions, 'shape') else None,
            'saved_at': datetime.utcnow().isoformat()
        }
        
        # Save to MinIO predictions bucket
        bucket_name = "training-artifacts"
        object_name = f"oof_predictions/{job_id}.json"
        
        # Ensure bucket exists
        if not minio_service.client.bucket_exists(bucket_name):
            minio_service.client.make_bucket(bucket_name)
        
        # Upload
        json_data = json.dumps(oof_data)
        minio_service.client.put_object(
            bucket_name,
            object_name,
            io.BytesIO(json_data.encode('utf-8')),
            len(json_data),
            content_type='application/json'
        )
        
        path = f"{bucket_name}/{object_name}"
        logger.info(f"✅ Saved OOF predictions to MinIO: {path}")
        return path
        
    except Exception as e:
        logger.error(f"❌ Failed to save OOF predictions to MinIO: {e}")
        return None


def load_oof_predictions_from_minio(minio_path: str) -> Optional[np.ndarray]:
    """
    Load OOF predictions from MinIO
    
    Args:
        minio_path: MinIO path (format: bucket/object)
    
    Returns:
        OOF predictions array or None if not found
    """
    if not minio_path:
        return None
    
    try:
        minio_service = get_minio_service()
        
        # Parse path
        parts = minio_path.split('/', 1)
        if len(parts) != 2:
            logger.error(f"Invalid MinIO path: {minio_path}")
            return None
        
        bucket_name, object_name = parts
        
        # Download
        response = minio_service.client.get_object(bucket_name, object_name)
        data = json.loads(response.read().decode('utf-8'))
        
        predictions = np.array(data['predictions'])
        logger.info(f"✅ Loaded OOF predictions from MinIO: {minio_path}, shape: {predictions.shape}")
        return predictions
        
    except Exception as e:
        logger.error(f"❌ Failed to load OOF predictions from MinIO: {e}")
        return None


def create_job_db(db: Session, job_type: str, user_id: int, params: dict, model_name: str = None, dataset_id: str = None) -> str:
    """
    Create a new training job in PostgreSQL
    
    Args:
        db: Database session
        job_type: Type of job (dataset_generation, base_model, ensemble, etc.)
        user_id: User ID
        params: Training parameters
        model_name: Optional model name (for base_model jobs)
        dataset_id: Optional dataset ID reference
    
    Returns:
        Job ID (UUID)
    """
    job_id = str(uuid.uuid4())
    
    # Map job_type string to JobType enum
    job_type_map = {
        'dataset_generation': JobType.DATASET_GENERATION,
        'feature_selection': JobType.FEATURE_SELECTION,
        'base_model': JobType.BASE_MODEL,
        'ensemble': JobType.ENSEMBLE,
        'full_pipeline': JobType.FULL_PIPELINE
    }
    
    job = TrainingJob(
        job_id=job_id,
        job_type=job_type_map.get(job_type, JobType.BASE_MODEL),
        status=JobStatus.PENDING,
        user_id=user_id,
        params=params,
        model_name=model_name,
        dataset_id=dataset_id,
        created_at=datetime.utcnow()
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Also add to in-memory dict for backward compatibility
    training_jobs[job_id] = {
        'job_id': job_id,
        'job_type': job_type,
        'status': TrainingStatus.QUEUED,
        'user_id': user_id,
        'params': params,
        'created_at': job.created_at,
        'started_at': None,
        'completed_at': None,
        'progress': None,
        'result': None,
        'error_message': None
    }
    
    logger.info(f"✅ Created training job in DB: {job_id} ({job_type})")
    return job_id


def update_job_status_db(db: Session, job_id: str, status: str, **kwargs):
    """
    Update job status in PostgreSQL
    
    Args:
        db: Database session
        job_id: Job ID
        status: New status (pending, running, completed, failed)
        **kwargs: Additional fields to update (result, error, oof_auc, test_auc, etc.)
    """
    job = db.query(TrainingJob).filter(TrainingJob.job_id == job_id).first()
    if not job:
        logger.warning(f"Job {job_id} not found in database")
        return
    
    # Map status string to JobStatus enum
    status_map = {
        'pending': JobStatus.PENDING,
        'running': JobStatus.RUNNING,
        'completed': JobStatus.COMPLETED,
        'failed': JobStatus.FAILED,
        TrainingStatus.QUEUED: JobStatus.PENDING,
        TrainingStatus.RUNNING: JobStatus.RUNNING,
        TrainingStatus.COMPLETED: JobStatus.COMPLETED,
        TrainingStatus.FAILED: JobStatus.FAILED
    }
    
    job.status = status_map.get(status, JobStatus.RUNNING)
    
    # Update timestamps
    if status in ['running', JobStatus.RUNNING, TrainingStatus.RUNNING]:
        job.started_at = datetime.utcnow()
    elif status in ['completed', 'failed', JobStatus.COMPLETED, JobStatus.FAILED, TrainingStatus.COMPLETED, TrainingStatus.FAILED]:
        job.completed_at = datetime.utcnow()
    
    # Update additional fields
    for key, value in kwargs.items():
        if hasattr(job, key):
            setattr(job, key, value)
    
    db.commit()
    db.refresh(job)
    
    # Also update in-memory dict for backward compatibility
    if job_id in training_jobs:
        training_jobs[job_id]['status'] = status
        for key, value in kwargs.items():
            training_jobs[job_id][key] = value
    
    logger.debug(f"Updated job {job_id} status to {status}")


def get_job_from_db(db: Session, job_id: str) -> Optional[Dict[str, Any]]:
    """
    Load training job from PostgreSQL
    
    Args:
        db: Database session
        job_id: Job ID
    
    Returns:
        Job dictionary compatible with existing code, or None if not found
    """
    job = db.query(TrainingJob).filter(TrainingJob.job_id == job_id).first()
    if not job:
        return None
    
    # Convert to dict format compatible with existing code
    job_dict = {
        'job_id': job.job_id,
        'job_type': job.job_type.value,
        'status': TrainingStatus.COMPLETED if job.status == JobStatus.COMPLETED else 
                  TrainingStatus.FAILED if job.status == JobStatus.FAILED else
                  TrainingStatus.RUNNING if job.status == JobStatus.RUNNING else TrainingStatus.QUEUED,
        'user_id': job.user_id,
        'params': job.params,
        'created_at': job.created_at,
        'started_at': job.started_at,
        'completed_at': job.completed_at,
        'result': job.result,
        'error_message': job.error,
        'model_name': job.model_name,
        'dataset_id': job.dataset_id,
        'oof_predictions_path': job.oof_predictions_path,
        'artifact_paths': job.artifact_paths
    }
    
    # If has OOF predictions in MinIO, load them into full_result
    if job.oof_predictions_path and job.result:
        oof_preds = load_oof_predictions_from_minio(job.oof_predictions_path)
        if oof_preds is not None:
            # Add to full_result for ensemble training
            if 'full_result' not in job_dict:
                job_dict['full_result'] = {}
            job_dict['full_result']['oof_predictions'] = oof_preds
    
    return job_dict


def create_job(job_type: str, user_id: int, params: dict) -> str:
    """DEPRECATED: Use create_job_db instead. Kept for backward compatibility."""
    job_id = str(uuid.uuid4())
    training_jobs[job_id] = {
        'job_id': job_id,
        'job_type': job_type,
        'status': TrainingStatus.QUEUED,
        'user_id': user_id,
        'params': params,
        'created_at': datetime.utcnow(),
        'started_at': None,
        'completed_at': None,
        'progress': None,
        'result': None,
        'error_message': None
    }
    return job_id


def update_job_status(job_id: str, status: TrainingStatus, **kwargs):
    """DEPRECATED: Use update_job_status_db instead. Kept for backward compatibility."""
    if job_id in training_jobs:
        training_jobs[job_id]['status'] = status
        for key, value in kwargs.items():
            training_jobs[job_id][key] = value


# ===== Background Tasks =====

async def run_dataset_generation(job_id: str, params: dict, db: Session):
    """Background task to generate dataset"""
    try:
        update_job_status(job_id, TrainingStatus.RUNNING, started_at=datetime.utcnow())
        update_job_status_db(db, job_id, 'running')
        
        from app.ml.training import DatasetGenerator
        import pandas as pd
        
        generator = DatasetGenerator(db)
        result = generator.generate_training_dataset(
            batch_id=params['batch_id'],
            target_column=params['target_column'],
            min_events_per_patient=params.get('min_events_per_patient', 2),
            test_size=params.get('test_size', 0.35),
            random_state=params.get('random_state', 42),
            create_separate_feature_sets=params.get('create_separate_feature_sets', True),
            scaling_strategy=params.get('scaling_strategy', 'standard'),
            use_lasso_feature_selection=params.get('use_lasso_feature_selection', True),
            lasso_alpha=params.get('lasso_alpha', 0.01),
            skip_preprocessing=params.get('skip_preprocessing', False)
        )
        
        # Helper function to convert DataFrame/numpy array to list
        def to_list(obj):
            if isinstance(obj, pd.DataFrame):
                # Convert to numpy first, then handle NaN/Inf
                arr = obj.values
                # Replace NaN/Inf with 0 (safer for ML)
                arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
                return arr.tolist()
            elif hasattr(obj, 'tolist'):
                arr = np.array(obj)
                # Replace NaN/Inf with 0
                arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
                return arr.tolist()
            else:
                return obj
        
        # Convert numpy arrays/DataFrames to lists for JSON serialization
        serializable_result = {
            'X_train': to_list(result['X_train']),
            'X_test': to_list(result['X_test']),
            'y_train': to_list(result['y_train']),
            'y_test': to_list(result['y_test']),
            'X_train_scaled': to_list(result.get('X_train_scaled', result['X_train'])),
            'X_test_scaled': to_list(result.get('X_test_scaled', result['X_test'])),
            'feature_names': list(result.get('feature_names', [])),
            'metadata': sanitize_for_json(result['metadata'])
        }
        
        # ========================================
        # SAVE ML DATASET TO MINIO
        # ========================================
        try:
            import pickle
            from app.services.minio_service import get_minio_service
            
            # Create dataset artifact
            dataset_artifact = {
                'X_train': result['X_train'],
                'X_test': result['X_test'],
                'y_train': result['y_train'],
                'y_test': result['y_test'],
                'X_train_scaled': result.get('X_train_scaled'),
                'X_test_scaled': result.get('X_test_scaled'),
                'feature_names': result.get('feature_names'),
                'metadata': result['metadata']
            }
            
            # Pickle the dataset
            pickle_data = pickle.dumps(dataset_artifact)
            
            # Save to MinIO
            minio_service = get_minio_service()
            minio_path = minio_service.save_ml_dataset(
                dataset_pickle=pickle_data,
                batch_id=params['batch_id'],
                metadata={
                    'train_samples': len(result['X_train']),
                    'test_samples': len(result['X_test']),
                    'n_features': len(result.get('feature_names', [])),
                    'target_column': params['target_column'],
                    'test_size': params.get('test_size', 0.35),
                    'scaling_strategy': params.get('scaling_strategy', 'standard'),
                    'created_at': datetime.utcnow().isoformat(),
                    'created_by_job': job_id
                }
            )
            
            serializable_result['minio_path'] = minio_path
            logger.info(f"✓ ML dataset saved to MinIO: {minio_path}")
        
        except Exception as e:
            logger.warning(f"⚠️  Failed to save ML dataset to MinIO: {e}")
            # Don't fail the job, just log warning
        
        # Store result in memory
        update_job_status(
            job_id,
            TrainingStatus.COMPLETED,
            completed_at=datetime.utcnow(),
            result=serializable_result
        )
        
        # Persist minimal result to database so it survives restarts
        # Also pre-compute feature medians so feature-defaults endpoint works after restart
        _feat_names = serializable_result.get('feature_names', [])
        _x_scaled = serializable_result.get('X_train_scaled') or serializable_result.get('X_train', [])
        _feature_medians = []
        if _feat_names and _x_scaled:
            try:
                _arr = np.array(_x_scaled, dtype=float)
                _meds = np.nanmedian(_arr, axis=0)
                _feature_medians = [round(float(v), 4) if not (np.isnan(v) or np.isinf(v)) else 0.0
                                    for v in _meds[:len(_feat_names)]]
            except Exception:
                pass  # non-fatal, defaults will fall back to MinIO

        db_result = {
            'minio_path': serializable_result.get('minio_path'),
            'feature_names': _feat_names,
            'feature_medians': _feature_medians,
            'metadata': sanitize_for_json(serializable_result.get('metadata', {}))
        }
        update_job_status_db(
            db,
            job_id,
            'completed',
            result=sanitize_for_json(db_result)
        )
        # update_job_status_db also overwrites in-memory result; restore the full one
        if job_id in training_jobs:
            training_jobs[job_id]['result'] = serializable_result
        
        logger.info(f"Dataset generation job {job_id} completed")
        
    except Exception as e:
        logger.error(f"Dataset generation job {job_id} failed: {e}", exc_info=True)
        update_job_status(
            job_id,
            TrainingStatus.FAILED,
            completed_at=datetime.utcnow(),
            error_message=str(e)
        )


# ====================================================================
# LASSO FEATURE SELECTION - DISABLED
# Reason: Not suitable for categorical labels (SLE/RA/SSc)
# Use FeatureEngineeringPipeline instead (see FEATURE_ENGINEERING_GUIDE.md)
# ====================================================================
# async def run_feature_selection(job_id: str, params: dict, db: Session):
#     """Background task to run feature selection - DISABLED"""
#     pass


async def run_base_model_training(job_id: str, params: dict, db: Session):
    """Background task to train a base model"""
    try:
        update_job_status(job_id, TrainingStatus.RUNNING, started_at=datetime.utcnow())
        
        from app.ml.training import BaseModelTrainer
        import time
        
        model_name = params['model_name']
        dataset_id = params['dataset_id']
        n_trials = params['n_trials']
        cv_folds = params['cv_folds']
        
        logger.info(f"=" * 80)
        logger.info(f"🚀 STARTING BASE MODEL TRAINING")
        logger.info(f"   Job ID: {job_id}")
        logger.info(f"   Model: {model_name}")
        logger.info(f"   Dataset: {dataset_id}")
        logger.info(f"   Trials: {n_trials}, CV Folds: {cv_folds}")
        logger.info(f"=" * 80)
        
        # Get the dataset from the completed dataset generation job
        if dataset_id not in training_jobs:
            raise ValueError(f"Dataset job {dataset_id} not found")
        
        dataset_job = training_jobs[dataset_id]
        if dataset_job['status'] != 'completed':
            raise ValueError(f"Dataset job {dataset_id} not completed")
        
        dataset_result = dataset_job['result']
        
        # Convert lists back to DataFrames with proper feature names
        feature_names = dataset_result.get('feature_names', [])
        
        X_train = pd.DataFrame(
            np.array(dataset_result['X_train']),
            columns=feature_names if feature_names else None
        )
        X_test = pd.DataFrame(
            np.array(dataset_result['X_test']),
            columns=feature_names if feature_names else None
        )
        y_train = pd.Series(np.array(dataset_result['y_train']))
        y_test = pd.Series(np.array(dataset_result['y_test']))
        
        X_train_scaled = pd.DataFrame(
            np.array(dataset_result.get('X_train_scaled', dataset_result['X_train'])),
            columns=feature_names if feature_names else None
        )
        X_test_scaled = pd.DataFrame(
            np.array(dataset_result.get('X_test_scaled', dataset_result['X_test'])),
            columns=feature_names if feature_names else None
        )
        
        logger.info(f"Loaded dataset: X_train shape {X_train.shape}, y_train shape {y_train.shape}")
        logger.info(f"Feature names: {list(X_train.columns)}")
        
        # Initialize trainer
        trainer = BaseModelTrainer(random_state=42, n_folds=cv_folds)
        
        # Train the model
        start_time = time.time()
        
        if model_name == 'xgboost':
            result = trainer.train_xgboost(X_train, y_train, n_trials=n_trials, X_test=X_test, y_test=y_test)
        elif model_name == 'lightgbm':
            result = trainer.train_lightgbm(X_train, y_train, n_trials=n_trials, X_test=X_test, y_test=y_test)
        elif model_name == 'catboost':
            result = trainer.train_catboost(X_train, y_train, n_trials=n_trials, X_test=X_test, y_test=y_test)
        elif model_name == 'gradient_boosting':
            result = trainer.train_gradient_boosting(X_train, y_train, n_trials=n_trials, X_test=X_test, y_test=y_test)
        elif model_name == 'random_forest':
            result = trainer.train_random_forest(X_train, y_train, n_trials=n_trials, X_test=X_test, y_test=y_test)
        elif model_name == 'adaboost':
            result = trainer.train_adaboost(X_train, y_train, n_trials=n_trials, X_test=X_test, y_test=y_test)
        elif model_name == 'decision_tree':
            result = trainer.train_decision_tree(X_train, y_train, n_trials=n_trials, X_test=X_test, y_test=y_test)
        elif model_name == 'svm':
            result = trainer.train_svm(X_train_scaled, y_train, n_trials=n_trials, X_test=X_test_scaled, y_test=y_test)
        elif model_name == 'knn':
            result = trainer.train_knn(X_train_scaled, y_train, n_trials=n_trials, X_test=X_test_scaled, y_test=y_test)
        elif model_name == 'logistic_regression':
            result = trainer.train_logistic_regression(X_train_scaled, y_train, n_trials=n_trials, X_test=X_test_scaled, y_test=y_test)
        elif model_name == 'ridge_classifier':
            result = trainer.train_ridge_classifier(X_train_scaled, y_train, n_trials=n_trials, X_test=X_test_scaled, y_test=y_test)
        elif model_name == 'linear_discriminant':
            result = trainer.train_linear_discriminant(X_train_scaled, y_train, n_trials=n_trials, X_test=X_test_scaled, y_test=y_test)
        elif model_name == 'mlp':
            result = trainer.train_mlp(X_train_scaled, y_train, n_trials=n_trials, X_test=X_test_scaled, y_test=y_test)
        else:
            raise ValueError(f"Unknown model: {model_name}")
        
        training_time = time.time() - start_time
        result['training_time_seconds'] = training_time
        result['model_name'] = model_name

        # ── Compute accuracy & specificity at the dispatch level ──────────────
        # base_models.py only returns precision/recall/f1/AUC.
        # accuracy and specificity (required by the research paper's evaluation
        # table) are derived here from the saved fold model + test set.
        if y_test is not None and result.get('fold_models'):
            try:
                from sklearn.metrics import accuracy_score, confusion_matrix as _cm
                _test_model = result['fold_models'][0]
                _X_test_eval = X_test_scaled if model_name in trainer.LINEAR_MODELS else X_test
                _test_pred = _test_model.predict(_X_test_eval)
                result['test_accuracy'] = float(accuracy_score(y_test, _test_pred))
                # Macro-averaged specificity across classes (TN/(TN+FP) per class)
                cm_arr = _cm(y_test, _test_pred)
                specs = []
                for _i in range(len(cm_arr)):
                    _tn = int(cm_arr.sum() - cm_arr[_i, :].sum() - cm_arr[:, _i].sum() + cm_arr[_i, _i])
                    _fp = int(cm_arr[:, _i].sum() - cm_arr[_i, _i])
                    specs.append(_tn / (_tn + _fp) if (_tn + _fp) > 0 else 0.0)
                result['test_specificity'] = float(np.mean(specs))
                logger.info(f"Accuracy: {result['test_accuracy']:.4f}, Specificity: {result['test_specificity']:.4f}")
            except Exception as _e:
                logger.warning(f"Could not compute accuracy/specificity: {_e}")
        # ─────────────────────────────────────────────────────────────────────
        
        # Remove non-serializable objects (model objects, numpy arrays)
        # But keep OOF predictions for ensemble training
        oof_predictions = result.get('oof_predictions', [])
        if hasattr(oof_predictions, 'tolist'):
            oof_predictions = oof_predictions.tolist()
        
        serializable_result = {
            'model_name': result['model_name'],
            'oof_auc': float(result.get('oof_auc', 0.0)),
            'cv_auc': float(result.get('cv_auc', 0.0)),
            'oof_predictions': oof_predictions,  # CRITICAL: Needed for ensemble
            'best_params': result.get('best_params', {}),
            'training_time_seconds': float(training_time),
            'test_auc': float(result.get('test_auc', 0.0)) if 'test_auc' in result else None,
            'test_precision': float(result.get('test_precision', 0.0)) if 'test_precision' in result else None,
            'test_recall': float(result.get('test_recall', 0.0)) if 'test_recall' in result else None,
            'test_f1': float(result.get('test_f1', 0.0)) if 'test_f1' in result else None,
            'test_brier_score': float(result.get('test_brier_score', 0.0)) if 'test_brier_score' in result else None,
            'test_accuracy': float(result.get('test_accuracy', 0.0)) if 'test_accuracy' in result else None,
            'test_specificity': float(result.get('test_specificity', 0.0)) if 'test_specificity' in result else None,
            'feature_names': list(X_train.columns) if hasattr(X_train, 'columns') and len(X_train.columns) > 0 else feature_names,
        }
        
        # Sanitize for JSON (handle NaN/Inf)
        serializable_result = sanitize_for_json(serializable_result)
        
        # Persist models to MinIO (USMA-75)
        try:
            import os
            # MinIO uses ROOT_USER/ROOT_PASSWORD, not ACCESS_KEY/SECRET_KEY
            minio_service = MinIOService(
                endpoint=os.getenv("MINIO_ENDPOINT", "minio:9000"),
                access_key=os.getenv("MINIO_ROOT_USER", "minio_admin"),
                secret_key=os.getenv("MINIO_ROOT_PASSWORD", "MinIO_P@ssw0rd_2026"),
                secure=os.getenv("MINIO_SECURE", "false").lower() == "true"
            )
            
            # Generate version string
            version = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            
            # Get batch_id from dataset metadata (params don't have it for base model training)
            dataset_metadata = dataset_result.get('metadata', {})
            batch_id = dataset_metadata.get('batch_id', 'unknown')
            target_column = dataset_metadata.get('target_column', params.get('target_column', 'labels_disease_classification'))
            
            # Save all fold models
            fold_models = result.get('fold_models', [])
            minio_paths = []
            
            # Get feature names from dataset result
            feature_names = dataset_result.get('feature_names', [])
            if not feature_names and 'selected_features' in dataset_result:
                feature_names = dataset_result['selected_features']
            
            for fold_idx, fold_model in enumerate(fold_models):
                minio_path = minio_service.save_model(
                    model=fold_model,
                    model_name=f"{batch_id[:8] if len(batch_id) >= 8 else batch_id}_{model_name}",
                    version=version,
                    fold_id=fold_idx,
                    metadata={
                        'batch_id': batch_id,
                        'target_column': target_column,
                        'dataset_id': dataset_id,
                        'model_type': model_name,
                        'fold': fold_idx,
                        'cv_auc': float(result.get('cv_auc', 0.0)),
                        'oof_auc': float(result.get('oof_auc', 0.0)),
                        'test_auc': float(result.get('test_auc', 0.0)) if 'test_auc' in result else None,
                        'best_params': result.get('best_params', {}),
                        'feature_names': feature_names,  # ✅ FIXED: Add feature names for prediction
                        'training_time': float(training_time),
                        'created_at': datetime.utcnow().isoformat(),
                        'n_folds': cv_folds
                    }
                )
                minio_paths.append(minio_path)
            
            serializable_result['model_artifact_paths'] = minio_paths
            logger.info(f"✅ MINIO SAVE SUCCESS: Saved {len(minio_paths)} {model_name} fold models to MinIO")
            logger.info(f"   Paths: {minio_paths}")
            
        except Exception as e:
            logger.error(f"⚠️  MINIO SAVE FAILED for {model_name}: {e}")
            logger.error(f"   Error type: {type(e).__name__}")
            import traceback
            logger.error(f"   Traceback: {traceback.format_exc()}")
            serializable_result['minio_error'] = str(e)
        
        # ========================================
        # PERSIST TO DATABASE & MINIO
        # ========================================
        
        # 1. Save OOF predictions to MinIO
        oof_preds_array = result.get('oof_predictions')
        oof_predictions_path = None
        
        if oof_preds_array is not None:
            oof_predictions_path = save_oof_predictions_to_minio(job_id, oof_preds_array)
            if oof_predictions_path:
                serializable_result['oof_predictions_path'] = oof_predictions_path
                logger.info(f"✅ Saved OOF predictions to MinIO: {oof_predictions_path}")
        
        # 2. Keep the full result in memory (with models) for ensemble training
        training_jobs[job_id]['full_result'] = result
        
        # 3. Update in-memory status (backward compatibility)
        update_job_status(
            job_id,
            TrainingStatus.COMPLETED,
            completed_at=datetime.utcnow(),
            result=serializable_result
        )
        
        # 4. Update database with complete results
        update_job_status_db(
            db,
            job_id,
            'completed',
            result=serializable_result,
            oof_auc=float(result.get('oof_auc', 0.0)),
            test_auc=float(result.get('test_auc', 0.0)) if 'test_auc' in result else None,
            test_f1=float(result.get('test_f1', 0.0)) if 'test_f1' in result else None,
            training_time_seconds=float(training_time),
            artifact_paths=serializable_result.get('model_artifact_paths', []),
            oof_predictions_path=oof_predictions_path,
            error=None
        )
        
        logger.info(f"=" * 80)
        logger.info(f"✅ MODEL TRAINING COMPLETED")
        logger.info(f"   Model: {model_name}")
        logger.info(f"   Job ID: {job_id}")
        logger.info(f"   Training Time: {training_time:.1f}s")
        logger.info(f"   OOF AUC: {serializable_result.get('oof_auc', 0):.4f}")
        logger.info(f"   Test AUC: {serializable_result.get('test_auc', 0):.4f}")
        logger.info(f"   MinIO Models: {'✓' if 'model_artifact_paths' in serializable_result else '✗'}")
        logger.info(f"   MinIO OOF Preds: {'✓' if oof_predictions_path else '✗'}")
        logger.info(f"   PostgreSQL: ✓")
        logger.info(f"=" * 80)
        
    except Exception as e:
        logger.error(f"Base model training job {job_id} failed: {e}", exc_info=True)
        update_job_status(
            job_id,
            TrainingStatus.FAILED,
            completed_at=datetime.utcnow(),
            error_message=str(e)
        )
        update_job_status_db(
            db,
            job_id,
            'failed',
            error=str(e)
        )


async def run_ensemble_training(job_id: str, params: dict, db: Session):
    """Background task to train stacking ensemble"""
    # Background tasks outlive the request — create a fresh DB session so
    # status updates are not silently dropped when the request session expires.
    _bg_db = SessionLocal()
    db = _bg_db
    try:
        update_job_status(job_id, TrainingStatus.RUNNING, started_at=datetime.utcnow())
        
        from app.ml.training.ensemble import StackingEnsemble
        import numpy as np
        import io as _io
        import joblib as _joblib
        import pickle as _pickle
        
        base_model_jobs = params['base_model_jobs']
        dataset_id = params['dataset_id']
        meta_learner_type = params.get('meta_learner_type', 'logistic_regression')
        target_column = params.get('target_column', 'labels_disease_classification')
        batch_id = params.get('batch_id', dataset_id[:8])
        
        # Initialize MinIO service early for fallback loading
        try:
            import os as _os
            _minio_svc = MinIOService(
                endpoint=_os.getenv("MINIO_ENDPOINT", "minio:9000"),
                access_key=_os.getenv("MINIO_ROOT_USER", "minio_admin"),
                secret_key=_os.getenv("MINIO_ROOT_PASSWORD", "MinIO_P@ssw0rd_2026"),
                secure=_os.getenv("MINIO_SECURE", "false").lower() == "true"
            )
        except Exception as _e:
            logger.warning(f"MinIO service init failed: {_e}. MinIO fallbacks will be unavailable.")
            _minio_svc = None
        
        logger.info(f"Training ensemble with {len(base_model_jobs)} base models from dataset {dataset_id}")
        logger.info(f"Meta-learner type: {meta_learner_type}")
        
        update_job_status_db(db, job_id, 'running')

        # --- Inline progress tracker for ensemble stages ---
        _PSTEPS = [
            ('load_oof',        'Load OOF predictions'),
            ('load_data',       'Load dataset arrays'),
            ('train_meta',      'Train meta-learner'),
            ('test_eval',       'Evaluate test predictions'),
            ('compute_metrics', 'Compute ensemble metrics'),
            ('save',            'Save model to MinIO'),
        ]
        _done_steps: set = set()

        def _progress(pct: int, label: str, active: str, detail: str = None):
            steps = []
            for _sid, _slabel in _PSTEPS:
                if _sid in _done_steps:
                    _st = 'done'
                elif _sid == active:
                    _st = 'running'
                else:
                    _st = 'pending'
                _entry = {'id': _sid, 'label': _slabel, 'status': _st}
                if _sid == active and detail:
                    _entry['detail'] = detail
                steps.append(_entry)
            training_jobs[job_id]['progress'] = {
                'percentage': pct,
                'label': label,
                'steps': steps,
            }
        # ------------------------------------------------
        n_base = len(base_model_jobs)
        _progress(5, f'Loading OOF predictions (0/{n_base} models)...', 'load_oof')

        # Validate all base model jobs are completed and load from DB if needed
        oof_predictions = {}
        for _oof_i, bm_job_id in enumerate(base_model_jobs):
            # Try in-memory first, then database
            if bm_job_id not in training_jobs:
                logger.info(f"  Loading job {bm_job_id} from database...")
                bm_job = get_job_from_db(db, bm_job_id)
                if not bm_job:
                    raise ValueError(f"Base model job {bm_job_id} not found in memory or database")
                # Cache in memory for ensemble training
                training_jobs[bm_job_id] = bm_job
            else:
                bm_job = training_jobs[bm_job_id]
            
            if bm_job['status'] not in [TrainingStatus.COMPLETED, 'completed']:
                raise ValueError(f"Base model job {bm_job_id} not completed (status: {bm_job['status']})")
            
            bm_result = bm_job.get('result', {})
            model_name = bm_result.get('model_name', f'model_{bm_job_id}')
            _progress(5 + int((_oof_i / max(n_base, 1)) * 30), f'Loading OOF ({_oof_i + 1}/{n_base})...', 'load_oof', model_name)
            oof_preds = bm_result.get('oof_predictions')
            
            # If OOF predictions not in result, try loading from MinIO
            if oof_preds is None:
                oof_path = bm_job.get('oof_predictions_path')
                if oof_path:
                    logger.info(f"  Loading OOF predictions from MinIO for {model_name}...")
                    oof_preds = load_oof_predictions_from_minio(oof_path)
                
                # Also check full_result if available (in-memory)
                if oof_preds is None and 'full_result' in bm_job:
                    oof_preds = bm_job['full_result'].get('oof_predictions')
            
            if oof_preds is None:
                raise ValueError(f"No OOF predictions found in base model job {bm_job_id} (checked result, MinIO, and full_result)")
            
            oof_predictions[model_name] = np.array(oof_preds)

        _done_steps.add('load_oof')
        _progress(40, 'Loading dataset arrays...', 'load_data')

        # Get y_train from dataset job - load from DB if needed
        if dataset_id not in training_jobs:
            logger.info(f"  Loading dataset job {dataset_id} from database...")
            dataset_job = get_job_from_db(db, dataset_id)
            if not dataset_job:
                raise ValueError(f"Dataset job {dataset_id} not found in memory or database")
            training_jobs[dataset_id] = dataset_job
        else:
            dataset_job = training_jobs[dataset_id]
        
        if dataset_job['status'] not in [TrainingStatus.COMPLETED, 'completed']:
            raise ValueError(f"Dataset job {dataset_id} not completed")
        
        dataset_result = dataset_job.get('result') or {}
        
        # If arrays are missing (job loaded from DB without them), load from MinIO
        if 'y_train' not in dataset_result or 'X_test' not in dataset_result:
            minio_path = dataset_result.get('minio_path')
            if not minio_path:
                raise ValueError(
                    f"Dataset job {dataset_id} is missing array data and has no MinIO path. "
                    "Please re-run dataset preparation."
                )
            if _minio_svc is None:
                raise ValueError(f"Dataset arrays not in memory and MinIO is unavailable.")
            logger.info(f"  Loading dataset arrays from MinIO: {minio_path}")
            try:
                response = _minio_svc.client.get_object("ml-datasets", minio_path)
                dataset_artifact = _pickle.loads(response.read())
                response.close()
                response.release_conn()
                def _to_list(x):
                    import pandas as _pd
                    if isinstance(x, _pd.DataFrame):
                        return x.values.tolist()
                    return x.tolist() if hasattr(x, 'tolist') else list(x)
                dataset_result['X_train'] = _to_list(dataset_artifact['X_train'])
                dataset_result['X_test'] = _to_list(dataset_artifact['X_test'])
                dataset_result['y_train'] = _to_list(dataset_artifact['y_train'])
                dataset_result['y_test'] = _to_list(dataset_artifact['y_test'])
                dataset_result['feature_names'] = list(dataset_artifact.get('feature_names') or [])
                logger.info(f"  Loaded dataset arrays from MinIO successfully")
            except Exception as _minio_e:
                raise ValueError(f"Failed to load dataset arrays from MinIO ({minio_path}): {_minio_e}")
        
        y_train = pd.Series(np.array(dataset_result['y_train']))
        y_test = pd.Series(np.array(dataset_result['y_test']))

        _done_steps.add('load_data')
        _progress(50, f'Training meta-learner ({meta_learner_type})...', 'train_meta')

        logger.info(f"OOF matrix shape: {list(oof_predictions.values())[0].shape}")
        logger.info(f"Target shape: {y_train.shape}")
        
        # Train ensemble with configurable meta-learner
        ensemble = StackingEnsemble(meta_learner_type=meta_learner_type)
        ensemble.fit(oof_predictions, y_train)
        
        # Get OOF results
        meta_weights = ensemble.get_meta_weights()
        ensemble_oof_proba = ensemble.predict_proba(oof_predictions)
        
        # Calculate OOF AUC based on binary vs multiclass
        from sklearn.metrics import roc_auc_score
        if ensemble.is_binary:
            ensemble_oof_auc = roc_auc_score(y_train, ensemble_oof_proba)
        else:
            ensemble_oof_auc = roc_auc_score(y_train, ensemble_oof_proba, multi_class='ovr', average='macro')

        _done_steps.add('train_meta')
        _progress(62, f'Evaluating test predictions (0/{n_base} models)...', 'test_eval')

        # CRITICAL: Test set evaluation (USMA-44)
        test_predictions = {}
        
        # Get feature names from dataset for proper DataFrame construction
        feature_names = dataset_result.get('feature_names', None)
        X_test_array = np.array(dataset_result['X_test'])
        
        # Create DataFrame with proper feature names
        if feature_names:
            X_test = pd.DataFrame(X_test_array, columns=feature_names)
        else:
            X_test = pd.DataFrame(X_test_array)
        
        for _test_i, bm_job_id in enumerate(base_model_jobs):
            _test_pct = 62 + int((_test_i / max(n_base, 1)) * 22)
            bm_job = training_jobs[bm_job_id]
            bm_full_result = bm_job.get('full_result', {})
            _bm_label = (bm_job.get('result') or {}).get('model_name', f'model {_test_i + 1}')
            _progress(_test_pct, f'Evaluating test predictions ({_test_i + 1}/{n_base})...', 'test_eval', _bm_label)

            # Get test predictions from base model
            fold_models = bm_full_result.get('fold_models', [])
            
            # Fallback: load fold models from MinIO if not in memory
            if not fold_models:
                artifact_paths = bm_job.get('artifact_paths', [])
                if artifact_paths and _minio_svc is not None:
                    bm_result = bm_job.get('result', {}) or {}
                    _bm_name = bm_result.get('model_name', bm_job_id)
                    logger.info(f"  Loading fold models from MinIO for {_bm_name} ({len(artifact_paths)} paths)...")
                    for _path in artifact_paths:
                        try:
                            _resp = _minio_svc.client.get_object(_minio_svc.models_bucket, _path)
                            _fm = _joblib.load(_io.BytesIO(_resp.read()))
                            _resp.close()
                            _resp.release_conn()
                            fold_models.append(_fm)
                        except Exception as _fe:
                            logger.warning(f"  Could not load fold model from {_path}: {_fe}")
            
            if not fold_models:
                bm_result = bm_job.get('result', {}) or {}
                raise ValueError(
                    f"No fold models available for base model '{bm_result.get('model_name', bm_job_id)}'. "
                    "Re-train base models before running ensemble."
                )
            
            # Average predictions across folds
            test_preds_list = []
            for fold_model in fold_models:
                test_pred = fold_model.predict_proba(X_test)
                test_preds_list.append(test_pred)
            
            avg_test_pred = np.mean(test_preds_list, axis=0)
            model_name = bm_job['result'].get('model_name')

            # Align test prediction shape with OOF prediction shape.
            # OOF predictions may have been stored as 1-D (binary: positive class only).
            # predict_proba always returns 2-D, so collapse to 1-D for binary models.
            oof_for_model = oof_predictions.get(model_name)
            if oof_for_model is not None and oof_for_model.ndim == 1 and avg_test_pred.ndim == 2:
                avg_test_pred = avg_test_pred[:, -1]  # use last column (positive class)

            test_predictions[model_name] = avg_test_pred
        
        _done_steps.add('test_eval')
        _progress(88, 'Computing ensemble metrics...', 'compute_metrics')

        # Ensemble test predictions
        ensemble_test_proba = ensemble.predict_proba(test_predictions)
        # StackingEnsemble has no predict() method — derive from predict_proba
        if hasattr(ensemble, 'predict'):
            ensemble_test_pred = ensemble.predict(test_predictions)
        elif np.ndim(ensemble_test_proba) == 1:
            # Binary: positive-class probability → threshold at 0.5
            ensemble_test_pred = (ensemble_test_proba >= 0.5).astype(int)
        else:
            # Multiclass: take argmax across class columns
            ensemble_test_pred = np.argmax(ensemble_test_proba, axis=1)
        
        # Calculate test metrics
        from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score, accuracy_score
        
        n_classes = len(np.unique(y_train))
        is_binary = n_classes == 2
        
        if is_binary:
            # predict_proba returns 1D array for binary (positive class probability only)
            ensemble_test_auc = roc_auc_score(y_test, ensemble_test_proba)
            ensemble_test_brier = np.mean((y_test - ensemble_test_proba) ** 2)
            avg_method = 'binary'
        else:
            # predict_proba returns 2D array for multiclass (all class probabilities)
            ensemble_test_auc = roc_auc_score(y_test, ensemble_test_proba, multi_class='ovr', average='macro')
            ensemble_test_brier = np.mean(np.sum((np.eye(n_classes)[y_test] - ensemble_test_proba) ** 2, axis=1))
            avg_method = 'macro'
        
        ensemble_test_precision = precision_score(y_test, ensemble_test_pred, average=avg_method, zero_division=0)
        ensemble_test_recall = recall_score(y_test, ensemble_test_pred, average=avg_method, zero_division=0)
        ensemble_test_f1 = f1_score(y_test, ensemble_test_pred, average=avg_method, zero_division=0)
        ensemble_test_accuracy = accuracy_score(y_test, ensemble_test_pred)

        # Normalize model name keys (may be ModelName enums)
        _bm_names_str = [k.value if hasattr(k, 'value') else str(k) for k in oof_predictions.keys()]

        result = {
            # Standard keys — read by models/list and models/metrics
            'oof_auc': float(ensemble_oof_auc),
            'test_auc': float(ensemble_test_auc),
            'test_precision': float(ensemble_test_precision),
            'test_recall': float(ensemble_test_recall),
            'test_f1': float(ensemble_test_f1),
            'test_accuracy': float(ensemble_test_accuracy),
            'train_samples': int(len(y_train)),
            'n_features': int(len(feature_names) if feature_names else 0),
            'feature_names': list(feature_names) if feature_names else [],
            'base_model_job_ids': list(base_model_jobs),
            # Ensemble-specific extras
            'ensemble_oof_auc': float(ensemble_oof_auc),
            'ensemble_test_auc': float(ensemble_test_auc),
            'ensemble_test_precision': float(ensemble_test_precision),
            'ensemble_test_recall': float(ensemble_test_recall),
            'ensemble_test_f1': float(ensemble_test_f1),
            'ensemble_test_brier_score': float(ensemble_test_brier),
            'meta_weights': {str(k): v for k, v in (meta_weights or {}).items()},
            'base_models_included': _bm_names_str,
            'calibration_method': ensemble.calibration_method,
            'is_calibrated': ensemble.is_calibrated
        }
        
        _done_steps.add('compute_metrics')
        _progress(93, 'Saving model to MinIO...', 'save')

        # Persist ensemble to MinIO (USMA-75)
        try:
            import os
            # MinIO uses ROOT_USER/ROOT_PASSWORD, not ACCESS_KEY/SECRET_KEY
            minio_service = MinIOService(
                endpoint=os.getenv("MINIO_ENDPOINT", "minio:9000"),
                access_key=os.getenv("MINIO_ROOT_USER", "minio_admin"),
                secret_key=os.getenv("MINIO_ROOT_PASSWORD", "MinIO_P@ssw0rd_2026"),
                secure=os.getenv("MINIO_SECURE", "false").lower() == "true"
            )
            
            version = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            
            # Build base model MinIO info so the inference service can load them
            base_model_minio_info = {}
            for bm_job_id in base_model_jobs:
                bm_job = training_jobs.get(bm_job_id, {})
                bm_result = bm_job.get('result', {})
                bm_model_name = bm_result.get('model_name', f'model_{bm_job_id}')
                bm_artifact_paths = bm_job.get('artifact_paths', [])
                if bm_artifact_paths:
                    first_path = bm_artifact_paths[0]
                    parts = first_path.split('/')
                    if len(parts) >= 2:
                        base_model_minio_info[bm_model_name] = {
                            'minio_name': parts[0],
                            'version': parts[1],
                            'n_folds': len(bm_artifact_paths)
                        }

            minio_path = minio_service.save_model(
                model=ensemble,
                model_name=f"{batch_id}_ensemble",
                version=version,
                metadata={
                    'batch_id': batch_id,
                    'target_column': target_column,
                    'dataset_id': dataset_id,
                    'model_type': 'stacking_ensemble',
                    'meta_learner_type': meta_learner_type,
                    'base_models': list(oof_predictions.keys()),
                    'base_model_minio_info': base_model_minio_info,
                    'ensemble_oof_auc': float(ensemble_oof_auc),
                    'ensemble_test_auc': float(ensemble_test_auc),
                    'ensemble_test_f1': float(ensemble_test_f1),
                    'ensemble_test_brier': float(ensemble_test_brier),
                    'meta_weights': meta_weights,
                    'calibration_method': ensemble.calibration_method,
                    'feature_names': feature_names if feature_names else [],
                    'created_at': datetime.utcnow().isoformat()
                }
            )
            
            result['model_artifact_path'] = minio_path
            logger.info(f"✅ Saved ensemble model to MinIO: {minio_path}")
            
        except Exception as e:
            logger.error(f"⚠️ Failed to save ensemble to MinIO: {e}")
            result['minio_error'] = str(e)
        
        # Keep full ensemble in memory for inference
        training_jobs[job_id]['full_result'] = {'ensemble': ensemble}
        
        update_job_status(
            job_id,
            TrainingStatus.COMPLETED,
            completed_at=datetime.utcnow(),
            result=result
        )

        # Persist completed ensemble to DB so models/list can return it
        try:
            update_job_status_db(
                db, job_id, 'completed',
                result=result,
                oof_auc=result['oof_auc'],
                test_auc=result['test_auc'],
                test_f1=result['test_f1'],
                artifact_paths=[result.get('model_artifact_path', '')] if result.get('model_artifact_path') else [],
                error=None
            )
        except Exception as _db_e:
            logger.error(f"Could not persist completed ensemble status to DB: {_db_e}")

        logger.info(f"Ensemble training job {job_id} completed with OOF AUC: {ensemble_oof_auc:.4f}")
        
    except Exception as e:
        logger.error(f"Ensemble training job {job_id} failed: {e}", exc_info=True)
        update_job_status(
            job_id,
            TrainingStatus.FAILED,
            completed_at=datetime.utcnow(),
            error_message=str(e)
        )
        # Persist failed status to DB (uses fresh session so it won't be expired)
        try:
            update_job_status_db(db, job_id, 'failed', error=str(e)[:1000])
        except Exception as _db_e:
            logger.error(f"Could not persist failed status to DB for job {job_id}: {_db_e}")
    finally:
        try:
            _bg_db.close()
        except Exception:
            pass


# ===== API Endpoints =====

@router.post("/train/prepare-dataset", response_model=DatasetGenerationResponse)
async def prepare_training_dataset(
    request: DatasetGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_researcher_or_admin),
    db: Session = Depends(get_db)
):
    """
    Generate training dataset with feature engineering
    Persistent storage: dataset metadata in PostgreSQL, artifacts in MinIO
    """
    job_id = create_job_db(
        db=db,
        job_type='dataset_generation',
        user_id=current_user.id,
        params=request.dict(),
        dataset_id=request.batch_id
    )
    
    # Schedule background task
    background_tasks.add_task(
        run_dataset_generation,
        job_id=job_id,
        params=request.dict(),
        db=db
    )
    
    logger.info(f"Dataset generation job {job_id} queued by user {current_user.email} - stored in PostgreSQL")
    
    return DatasetGenerationResponse(
        job_id=job_id,
        status=TrainingStatus.QUEUED,
        message="Dataset generation job queued. Check status with GET /train/status/{job_id}",
        generated_at=datetime.utcnow()
    )


# ====================================================================
# LASSO ENDPOINT - DISABLED  
# Use feature engineering pipeline instead
# See: FEATURE_ENGINEERING_GUIDE.md
# ====================================================================
# @router.post("/train/feature-selection", response_model=FeatureSelectionResponse)
# async def run_feature_selection_endpoint(...):


@router.post("/train/base-model", response_model=BaseModelTrainingResponse)
async def train_base_model(
    request: BaseModelTrainingRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_researcher_or_admin),
    db: Session = Depends(get_db)
):
    """
    Train a single base model (XGBoost, LightGBM, CatBoost, etc.)
    Persistent storage: job metadata in PostgreSQL, models in MinIO
    """
    job_id = create_job_db(
        db=db,
        job_type='base_model',
        user_id=current_user.id,
        params=request.dict(),
        model_name=request.model_name.value,
        dataset_id=request.dataset_id
    )
    
    background_tasks.add_task(
        run_base_model_training,
        job_id=job_id,
        params=request.dict(),
        db=db
    )
    
    logger.info(f"Base model training job {job_id} ({request.model_name}) queued - stored in PostgreSQL")
    
    return BaseModelTrainingResponse(
        job_id=job_id,
        status=TrainingStatus.QUEUED,
        model_name=request.model_name.value
    )


@router.post("/train/ensemble", response_model=EnsembleTrainingResponse)
async def train_ensemble(
    request: EnsembleTrainingRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_researcher_or_admin),
    db: Session = Depends(get_db)
):
    """
    Train stacking ensemble meta-learner from base model predictions
    Persistent storage: job metadata in PostgreSQL, ensemble model in MinIO
    """
    # Guard: reject before creating a ghost job that will fail instantly
    if not request.base_model_jobs or len(request.base_model_jobs) < 2:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail=f"Ensemble requires at least 2 completed base model jobs. "
                   f"Received {len(request.base_model_jobs or [])}. "
                   f"Train base models first, then retry."
        )

    job_id = create_job_db(
        db=db,
        job_type='ensemble',
        user_id=current_user.id,
        params=request.dict(),
        model_name='ensemble',
        dataset_id=request.dataset_id
    )

    # Schedule background task
    background_tasks.add_task(
        run_ensemble_training,
        job_id=job_id,
        params=request.dict(),
        db=db
    )

    logger.info(f"Ensemble training job {job_id} queued by user {current_user.email}")

    return EnsembleTrainingResponse(
        job_id=job_id,
        status=TrainingStatus.QUEUED
    )


@router.post("/train/full-pipeline", response_model=FullPipelineTrainingResponse)
async def train_full_pipeline(
    request: FullPipelineTrainingRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Run complete end-to-end training pipeline:
    1. Generate dataset
    2. Feature selection
    3. Train all base models
    4. Train stacking ensemble
    5. Evaluate
    """
    # TODO: Implement full pipeline orchestration
    job_id = str(uuid.uuid4())
    
    return FullPipelineTrainingResponse(
        job_id=job_id,
        status=TrainingStatus.QUEUED,
        message="Full pipeline training not yet implemented. Use individual endpoints for now."
    )


@router.get("/train/status/{job_id}", response_model=TrainingJobStatus)
async def get_training_status(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get status of a training job
    Loads from PostgreSQL if not in memory (survives restart)
    """
    try:
        # Try in-memory first, then database
        if job_id not in training_jobs:
            logger.info(f"Job {job_id} not in memory, loading from database...")
            job = get_job_from_db(db, job_id)
            if not job:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Training job {job_id} not found"
                )
            # Cache in memory for subsequent requests
            training_jobs[job_id] = job
        else:
            job = training_jobs[job_id]
        
        # Sanitize result and progress for JSON serialization
        result = job.get('result')
        if result is not None:
            result = sanitize_for_json(result)
        
        progress = job.get('progress')
        if progress is not None:
            progress = sanitize_for_json(progress)
        
        return TrainingJobStatus(
            job_id=job['job_id'],
            status=job['status'],
            job_type=job['job_type'],
            created_at=job['created_at'],
            started_at=job.get('started_at'),
            completed_at=job.get('completed_at'),
            progress=progress,
            result=result,
            error_message=job.get('error_message')
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting status for job {job_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve job status: {str(e)}"
        )


@router.get("/train/jobs/{job_id}/feature-defaults")
async def get_feature_defaults(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Return per-feature median values from the training dataset for a trained model.
    Used by the SHAP explainability UI to pre-populate input with representative
    values instead of all-zero defaults.
    """
    try:
        # --- Step 1: resolve dataset_id from the model job ---
        if job_id not in training_jobs:
            job_db = get_job_from_db(db, job_id)
            if not job_db:
                return {"defaults": {}, "note": "Job not found"}
            training_jobs[job_id] = job_db

        model_job = training_jobs[job_id]
        params = model_job.get('params') or {}
        dataset_id = params.get('dataset_id')

        if not dataset_id:
            return {"defaults": {}, "note": "No dataset associated with this model job"}

        # --- Step 2: load the dataset generation job ---
        if dataset_id not in training_jobs:
            ds_job_db = get_job_from_db(db, dataset_id)
            if not ds_job_db:
                return {"defaults": {}, "note": "Dataset job not found"}
            training_jobs[dataset_id] = ds_job_db

        dataset_job = training_jobs[dataset_id]
        dataset_result = dataset_job.get('result') or {}
        feature_names = dataset_result.get('feature_names', [])
        X_train_raw = dataset_result.get('X_train_scaled') or dataset_result.get('X_train')

        # --- Step 3a: use pre-computed medians stored in DB result (fast path) ---
        stored_medians = dataset_result.get('feature_medians', [])
        if feature_names and stored_medians and len(stored_medians) == len(feature_names):
            defaults = {}
            for name, val in zip(feature_names, stored_medians):
                v = float(val) if val is not None else 0.0
                if np.isnan(v) or np.isinf(v):
                    v = 0.0
                defaults[str(name)] = v
            return {"defaults": defaults, "n_features": len(defaults), "note": "Median values from training data"}

        # --- Step 3b: fallback — load full artifact from MinIO if not in memory ---
        if not feature_names or X_train_raw is None:
            minio_path = dataset_result.get('minio_path')
            if not minio_path:
                return {"defaults": {}, "note": "Training data not available"}
            try:
                import pickle as _pickle
                _minio = get_minio_service()
                _resp = _minio.client.get_object("ml-datasets", minio_path)
                _artifact = _pickle.loads(_resp.read())
                _resp.close()
                _resp.release_conn()
                feature_names = list(_artifact.get('feature_names') or [])
                X_train_raw = _artifact.get('X_train_scaled') or _artifact.get('X_train')
            except Exception as _minio_err:
                logger.warning(f"Could not load dataset from MinIO for feature-defaults: {_minio_err}")
                return {"defaults": {}, "note": "Training data not available"}

        if not feature_names or X_train_raw is None:
            return {"defaults": {}, "note": "No feature data found"}

        # --- Step 4: compute per-feature medians ---
        X_arr = np.array(X_train_raw, dtype=float)
        medians = np.nanmedian(X_arr, axis=0)

        defaults = {}
        for i, name in enumerate(feature_names):
            val = float(medians[i]) if i < len(medians) else 0.0
            if np.isnan(val) or np.isinf(val):
                val = 0.0
            defaults[str(name)] = round(val, 4)

        return {"defaults": defaults, "n_features": len(defaults), "note": "Median values from training data"}

    except Exception as e:
        logger.error(f"Error computing feature defaults for job {job_id}: {e}", exc_info=True)
        return {"defaults": {}, "note": str(e)}


@router.get("/models/list", response_model=ModelListResponse)
async def list_trained_models(
    model_type: Optional[str] = None,
    limit: int = 1000,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all trained models from database
    
    Args:
        model_type: Filter by model type ('base_model' or 'ensemble')
        limit: Maximum number of models to return (default: 1000)
    
    Returns:
        List of trained models with metadata
    """
    try:
        # Query database for completed training jobs
        query = db.query(TrainingJob).filter(
            TrainingJob.status == JobStatus.COMPLETED
        )
        
        # Filter by job type if specified
        if model_type == 'base_model':
            query = query.filter(TrainingJob.job_type == JobType.BASE_MODEL)
        elif model_type == 'ensemble':
            query = query.filter(TrainingJob.job_type == JobType.ENSEMBLE)
        else:
            # Get both base models and ensembles
            query = query.filter(TrainingJob.job_type.in_([
                JobType.BASE_MODEL,
                JobType.ENSEMBLE
            ]))
        
        # Sort by completion time (newest first) and limit
        # Scope to current user (admins see all)
        if not getattr(current_user, 'is_admin', False):
            query = query.filter(TrainingJob.user_id == current_user.id)
        db_jobs = query.order_by(TrainingJob.completed_at.desc()).limit(limit).all()
        
        # Convert to model info
        models = []
        for job in db_jobs:
            try:
                result = job.result or {}
                
                # Determine model type
                if job.job_type == JobType.BASE_MODEL:
                    model_type_str = 'base_model'
                    model_name = job.model_name or result.get('model_name', 'unknown')
                else:
                    model_type_str = 'ensemble'
                    model_name = 'stacking_ensemble'
                
                # Extract metrics safely — ensemble uses standard keys now,
                # but fall back to legacy 'ensemble_*' keys for old records
                oof_auc = result.get('oof_auc') or result.get('ensemble_oof_auc')
                test_auc = result.get('test_auc') or result.get('ensemble_test_auc')
                
                # Convert to float if needed
                if oof_auc is not None and not isinstance(oof_auc, (int, float)):
                    try:
                        oof_auc = float(oof_auc)
                    except:
                        oof_auc = None
                
                if test_auc is not None and not isinstance(test_auc, (int, float)):
                    try:
                        test_auc = float(test_auc)
                    except:
                        test_auc = None
                
                # Extract classification metrics safely
                def _safe_float(v):
                    if v is None: return None
                    try: return float(v)
                    except: return None

                # Feature names: try multiple keys in result
                raw_features = (result.get('feature_names') or
                                result.get('selected_features') or
                                result.get('dataset_feature_names') or [])
                feature_names_list = [str(f) for f in raw_features] if raw_features else None

                model_info = TrainedModelInfo(
                    model_id=job.job_id,
                    model_name=model_name,
                    model_type=model_type_str,
                    version='1.0',
                    trained_at=job.completed_at or job.created_at,
                    train_samples=result.get('train_samples', 0),
                    test_samples=result.get('test_samples', 0),
                    oof_auc=oof_auc,
                    test_auc=test_auc,
                    test_precision=_safe_float(result.get('test_precision')),
                    test_recall=_safe_float(result.get('test_recall')),
                    test_f1=_safe_float(result.get('test_f1')),
                    test_accuracy=_safe_float(result.get('test_accuracy')),
                    test_specificity=_safe_float(result.get('test_specificity')),
                    hyperparameters=result.get('best_params'),
                    feature_count=result.get('n_features', 0),
                    artifact_path=result.get('model_artifact_path', ''),
                    feature_names=feature_names_list,
                    base_model_ids=result.get('base_model_job_ids') or job.params.get('base_model_jobs', []) or [],
                    in_ensemble=(model_type_str == 'ensemble')
                )
                models.append(model_info)
            except Exception as e:
                logger.error(f"Failed to convert job {job.job_id} to model info: {e}", exc_info=True)
                continue
        
        return ModelListResponse(
            models=models,
            total_count=len(models)
        )
    except Exception as e:
        logger.error(f"Failed to list models: {e}", exc_info=True)
        # Return empty list instead of error for better UX
        return ModelListResponse(
            models=[],
            total_count=0
        )


@router.get("/datasets/available")
async def get_available_datasets(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get list of datasets available for training with labeling statistics
    Returns only datasets that are ready or partially ready for training
    """
    from app.models.flexible_data import FlexibleDatasetWide
    from sqlalchemy import func
    import uuid as uuid_lib
    
    # Query to get unique batches with record counts
    batches_query = db.query(
        FlexibleDatasetWide.import_batch_id,
        FlexibleDatasetWide.dataset_name,
        FlexibleDatasetWide.dataset_type,
        FlexibleDatasetWide.dataset_source,
        func.min(FlexibleDatasetWide.created_at).label('uploaded_at'),
        func.count(FlexibleDatasetWide.id).label('record_count')
    ).group_by(
        FlexibleDatasetWide.import_batch_id,
        FlexibleDatasetWide.dataset_name,
        FlexibleDatasetWide.dataset_type,
        FlexibleDatasetWide.dataset_source
    ).all()
    
    datasets = []
    for batch in batches_query:
        batch_id = str(batch.import_batch_id)
        
        # Get labeling statistics for this batch
        target_column = 'labels_disease_classification'
        
        batch_records = db.query(FlexibleDatasetWide).filter(
            FlexibleDatasetWide.import_batch_id == batch.import_batch_id
        ).all()
        
        labeled_count = 0
        for record in batch_records:
            if record.data and target_column in record.data:
                label_value = record.data.get(target_column)
                if label_value is not None and label_value != '' and str(label_value).strip() not in ['', 'None', 'null']:
                    labeled_count += 1
        
        datasets.append({
            'batch_id': batch_id,
            'original_filename': batch.dataset_name or f'Dataset-{batch_id[:8]}',
            'uploaded_at': batch.uploaded_at.isoformat() if batch.uploaded_at else None,
            'record_count': batch.record_count,
            'labeled_count': labeled_count,
            'dataset_type': batch.dataset_type,
            'source': batch.dataset_source
        })
    
    return {
        'total': len(datasets),
        'datasets': datasets
    }


@router.get("/models/{model_id}/metrics", response_model=ModelEvaluationResponse)
async def get_model_metrics(
    model_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get evaluation metrics for a trained model
    
    Args:
        model_id: ID of the trained model (job_id)
    
    Returns:
        Comprehensive evaluation metrics
    """
    # Find the training job — check memory first, fall back to DB
    result = {}
    if model_id in training_jobs:
        job = training_jobs[model_id]
        if job['status'] != TrainingStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model training not completed (status: {job['status']})"
            )
        result = job.get('result', {})
    else:
        # Fallback: load from DB (handles backend restarts)
        db_job = db.query(TrainingJob).filter(TrainingJob.job_id == model_id).first()
        if not db_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model {model_id} not found"
            )
        if db_job.status.value != 'completed':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model training not completed (status: {db_job.status.value})"
            )
        result = db_job.result or {}
        # Also restore denormalized metrics from DB columns if result is sparse
        if not result.get('oof_auc') and db_job.oof_auc:
            result['oof_auc'] = db_job.oof_auc
        if not result.get('test_auc') and db_job.test_auc:
            result['test_auc'] = db_job.test_auc
        if not result.get('f1_score') and db_job.test_f1:
            result['f1_score'] = db_job.test_f1
        if not result.get('model_name') and db_job.model_name:
            result['model_name'] = db_job.model_name
    
    # Extract metrics from training result
    model_name = result.get('model_name', 'unknown')
    
    # Build evaluation response
    evaluation = ModelEvaluationResponse(
        model_id=model_id,
        model_name=model_name,
        auc_roc=result.get('oof_auc', 0.0) or result.get('cv_auc', 0.0),
        precision=result.get('precision', 0.0),
        recall=result.get('recall', 0.0),
        f1_score=result.get('f1_score', 0.0),
        specificity=result.get('specificity'),
        brier_score=result.get('brier_score', 0.0),
        confusion_matrix=result.get('confusion_matrix', {
            'true_positive': 0,
            'true_negative': 0,
            'false_positive': 0,
            'false_negative': 0
        }),
        calibration_data=result.get('calibration_data')
    )
    
    return evaluation


@router.post("/models/compare", response_model=ModelComparisonResponse)
async def compare_models(
    request: ModelComparisonRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Compare multiple models side-by-side
    
    Args:
        request: Model comparison request with list of model IDs
    
    Returns:
        Side-by-side comparison of model metrics
    """
    model_ids = request.model_ids
    
    if len(model_ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 models required for comparison"
        )
    
    # Query database for models
    db_jobs = db.query(TrainingJob).filter(
        TrainingJob.job_id.in_(model_ids),
        TrainingJob.status == JobStatus.COMPLETED
    ).all()
    
    # Check if all models were found
    found_ids = {job.job_id for job in db_jobs}
    missing_ids = set(model_ids) - found_ids
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Models not found: {', '.join(missing_ids)}"
        )
    
    # Collect metrics for each model
    comparisons = []
    
    for job in db_jobs:
        result = job.result or {}
        
        # Extract metrics safely
        oof_auc = result.get('oof_auc') or result.get('cv_auc', 0.0)
        test_auc = result.get('test_auc')
        
        # Use test_auc if available, otherwise oof_auc
        auc_roc = test_auc if test_auc is not None else oof_auc
        
        model_metrics = {
            'model_id': job.job_id,
            'model_name': job.model_name or result.get('model_name', 'unknown'),
            'auc_roc': float(auc_roc) if auc_roc is not None else 0.0,
            'precision': float(result.get('test_precision', 0.0) or 0.0),
            'recall': float(result.get('test_recall', 0.0) or 0.0),
            'f1_score': float(result.get('test_f1', 0.0) or 0.0),
            'training_time': float(result.get('training_time_seconds', 0.0) or 0.0),
            'n_features': int(result.get('n_features', 0)),
            'hyperparameters': result.get('best_params', {})
        }
        
        comparisons.append(model_metrics)
    
    # Determine best model (highest AUC)
    if comparisons:
        best_model = max(comparisons, key=lambda x: x['auc_roc'])
        best_model_id = best_model['model_id']
        best_model_name = best_model['model_name']
    else:
        best_model_id = None
        best_model_name = None
    
    return ModelComparisonResponse(
        models=comparisons,
        best_model_id=best_model_id,
        best_model_name=best_model_name,
        comparison_metric='auc_roc'
    )


@router.get("/training-history", response_model=TrainingHistoryResponse)
async def get_training_history(
    limit: int = 50,
    job_type: Optional[str] = None,
    status_filter: Optional[TrainingStatus] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get training job history from database
    
    Args:
        limit: Maximum number of jobs to return (default: 50)
        job_type: Filter by job type ('dataset_generation', 'base_model_training', etc.)
        status_filter: Filter by status ('completed', 'failed', 'running', etc.)
    
    Returns:
        List of training jobs with status and metrics
    """
    # Build query
    query = db.query(TrainingJob)
    
    # Apply filters
    if job_type:
        # Map string to JobType enum
        job_type_map = {
            'dataset_generation': JobType.DATASET_GENERATION,
            'base_model': JobType.BASE_MODEL,
            'base_model_training': JobType.BASE_MODEL,
            'ensemble': JobType.ENSEMBLE,
            'ensemble_training': JobType.ENSEMBLE
        }
        if job_type in job_type_map:
            query = query.filter(TrainingJob.job_type == job_type_map[job_type])
    
    if status_filter:
        # Map TrainingStatus to JobStatus
        status_map = {
            TrainingStatus.COMPLETED: JobStatus.COMPLETED,
            TrainingStatus.FAILED: JobStatus.FAILED,
            TrainingStatus.RUNNING: JobStatus.RUNNING,
            TrainingStatus.QUEUED: JobStatus.PENDING
        }
        if status_filter in status_map:
            query = query.filter(TrainingJob.status == status_map[status_filter])
    
    # Sort by creation time (newest first) and limit
    # Scope to current user (admins see all)
    if not getattr(current_user, 'is_admin', False):
        query = query.filter(TrainingJob.user_id == current_user.id)
    db_jobs = query.order_by(TrainingJob.created_at.desc()).limit(limit).all()
    
    # Build history items
    history_items = []
    for job in db_jobs:
        result = job.result or {}
        
        # Calculate training time if completed
        training_time = None
        if job.completed_at and job.started_at:
            training_time = (job.completed_at - job.started_at).total_seconds()
        
        # Map JobStatus to TrainingStatus
        status = TrainingStatus.COMPLETED if job.status == JobStatus.COMPLETED else \
                 TrainingStatus.FAILED if job.status == JobStatus.FAILED else \
                 TrainingStatus.RUNNING if job.status == JobStatus.RUNNING else \
                 TrainingStatus.QUEUED
        
        history_item = TrainingHistoryItem(
            job_id=job.job_id,
            job_type=job.job_type.value,
            model_name=job.model_name or result.get('model_name'),
            status=status,
            created_at=job.created_at,
            completed_at=job.completed_at,
            oof_auc=job.oof_auc or result.get('oof_auc') or result.get('cv_auc'),
            test_auc=job.test_auc or result.get('test_auc'),
            test_f1=job.test_f1 or result.get('test_f1'),
            training_time_seconds=training_time or result.get('training_time_seconds'),
            dataset_id=job.dataset_id,
            user_id=job.user_id,
            username=job.user.username if job.user else None,
            user_full_name=job.user.full_name if job.user else None
        )
        history_items.append(history_item)
    
    # Calculate statistics from database
    total_jobs = db.query(TrainingJob).count()
    completed_jobs = db.query(TrainingJob).filter(TrainingJob.status == JobStatus.COMPLETED).count()
    failed_jobs = db.query(TrainingJob).filter(TrainingJob.status == JobStatus.FAILED).count()
    running_jobs = db.query(TrainingJob).filter(TrainingJob.status == JobStatus.RUNNING).count()
    
    return TrainingHistoryResponse(
        jobs=history_items,
        total_jobs=total_jobs,
        completed_jobs=completed_jobs,
        failed_jobs=failed_jobs,
        running_jobs=running_jobs
    )


@router.post("/models/sync-from-minio")
async def sync_models_from_minio(
    current_user: User = Depends(require_researcher_or_admin),
    db: Session = Depends(get_db)
):
    """
    Sync trained models from MinIO to database
    
    Scans the ml-models bucket in MinIO and creates database entries for any
    models that don't already have TrainingJob records.
    
    This is useful for recovering from database resets or syncing models
    trained through external scripts.
    
    Returns:
        Summary of synced models
    """
    try:
        from app.core.config import settings
        
        # Initialize MinIO client
        minio = MinIOService(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=settings.MINIO_SECURE
        )
        
        logger.info("[Sync] Scanning MinIO for trained models...")
        
        # List all objects in ml-models bucket
        objects = minio.client.list_objects('ml-models', recursive=True)
        
        synced_count = 0
        skipped_count = 0
        error_count = 0
        synced_models = []
        
        # Group objects by model_name/version
        model_versions = {}
        for obj in objects:
            # Parse path: {model_name}/{version}/model.pkl or metadata.json
            parts = obj.object_name.split('/')
            if len(parts) >= 3:
                model_name = parts[0]
                version = parts[1]
                filename = parts[2]
                
                key = f"{model_name}/{version}"
                if key not in model_versions:
                    model_versions[key] = {
                        'model_name': model_name,
                        'version': version,
                        'has_model': False,
                        'has_metadata': False,
                        'metadata_obj': None
                    }
                
                if filename == 'model.pkl' or filename.startswith('fold_'):
                    model_versions[key]['has_model'] = True
                elif filename == 'metadata.json':
                    model_versions[key]['has_metadata'] = True
                    model_versions[key]['metadata_obj'] = obj.object_name
        
        logger.info(f"[Sync] Found {len(model_versions)} model versions in MinIO")
        
        # Process each model version
        for key, model_info in model_versions.items():
            if not model_info['has_model']:
                continue  # Skip if no model file
            
            model_name = model_info['model_name']
            version = model_info['version']
            
            try:
                # Load metadata if available
                metadata = {}
                if model_info['has_metadata']:
                    try:
                        response = minio.client.get_object('ml-models', model_info['metadata_obj'])
                        metadata_bytes = response.read()
                        response.close()
                        response.release_conn()
                        metadata = json.loads(metadata_bytes.decode('utf-8'))
                    except Exception as e:
                        logger.warning(f"[Sync] Could not load metadata for {key}: {e}")
                
                # Generate a synthetic job_id from model name and version
                # This allows idempotent syncing (same model won't create duplicate entries)
                job_id = f"minio-{model_name}-{version}"
                
                # Check if this model already exists in database
                existing_job = db.query(TrainingJob).filter(
                    TrainingJob.job_id == job_id
                ).first()
                
                if existing_job:
                    logger.debug(f"[Sync] Skipping {model_name} {version} - already in database")
                    skipped_count += 1
                    continue
                
                # Determine job type
                if model_name.lower() in ['stacking_ensemble', 'ensemble']:
                    job_type = JobType.ENSEMBLE
                else:
                    job_type = JobType.BASE_MODEL
                
                # Extract metrics from metadata
                oof_auc = metadata.get('oof_auc') or metadata.get('cv_auc')
                test_auc = metadata.get('test_auc')
                test_f1 = metadata.get('test_f1')
                training_time = metadata.get('training_time_seconds')
                
                # Create TrainingJob entry
                training_job = TrainingJob(
                    job_id=job_id,
                    job_type=job_type,
                    status=JobStatus.COMPLETED,
                    user_id=current_user.id,
                    created_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    params={
                        'synced_from_minio': True,
                        'original_path': f"{model_name}/{version}",
                        'metadata': metadata
                    },
                    result=metadata,
                    artifact_paths=[f"{model_name}/{version}/model.pkl"],
                    model_name=model_name,
                    oof_auc=float(oof_auc) if oof_auc is not None else None,
                    test_auc=float(test_auc) if test_auc is not None else None,
                    test_f1=float(test_f1) if test_f1 is not None else None,
                    training_time_seconds=float(training_time) if training_time is not None else None
                )
                
                db.add(training_job)
                db.commit()
                
                synced_count += 1
                synced_models.append({
                    'model_name': model_name,
                    'version': version,
                    'oof_auc': oof_auc,
                    'test_auc': test_auc
                })
                
                logger.info(f"[Sync] ✓ Synced {model_name} {version} (AUC: {test_auc or oof_auc})")
                
            except Exception as e:
                logger.error(f"[Sync] Error syncing {key}: {e}", exc_info=True)
                error_count += 1
                continue
        
        return {
            'status': 'completed',
            'synced_count': synced_count,
            'skipped_count': skipped_count,
            'error_count': error_count,
            'synced_models': synced_models,
            'message': f"Successfully synced {synced_count} models from MinIO to database"
        }
        
    except Exception as e:
        logger.error(f"[Sync] Failed to sync models from MinIO: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync models: {str(e)}"
        )
