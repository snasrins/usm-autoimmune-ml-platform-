"""
Training API Schemas
Request and response models for ML training endpoints
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class ModelName(str, Enum):
    """Supported base model names"""
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    CATBOOST = "catboost"
    RANDOM_FOREST = "random_forest"
    ADABOOST = "adaboost"
    SVM = "svm"
    MLP = "mlp"
    KNN = "knn"
    DECISION_TREE = "decision_tree"
    LOGISTIC_REGRESSION = "logistic_regression"
    RIDGE_CLASSIFIER = "ridge_classifier"
    LINEAR_DISCRIMINANT = "linear_discriminant"
    GRADIENT_BOOSTING = "gradient_boosting"


class TrainingStatus(str, Enum):
    """Training job status"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ===== Dataset Generation =====

class DatasetGenerationRequest(BaseModel):
    """Request to generate training dataset"""
    batch_id: str = Field(..., description="Batch ID of the dataset to use for training")
    target_column: str = Field(default="labels_disease_classification", description="Target variable column name (after JSONB flattening)")
    min_events_per_patient: int = Field(default=2, ge=1, description="Minimum clinical events per patient")
    test_size: float = Field(default=0.2, ge=0.1, le=0.5, description="Test set proportion")
    random_state: int = Field(default=42, description="Random seed for reproducibility")
    create_separate_feature_sets: bool = Field(default=True, description="Create both raw and scaled feature sets")
    scaling_strategy: str = Field(default='standard', description="Scaling strategy: 'standard', 'minmax', or 'robust'")
    use_lasso_feature_selection: bool = Field(default=True, description="Apply LASSO feature selection")
    lasso_alpha: float = Field(default=0.01, description="LASSO regularization strength")
    skip_preprocessing: bool = Field(default=False, description="Skip all ML preprocessing (advanced)")


class DatasetGenerationResponse(BaseModel):
    """Response from dataset generation"""
    job_id: str
    status: TrainingStatus
    message: str
    metadata: Optional[Dict[str, Any]] = None
    generated_at: datetime


# ===== Feature Selection =====

class FeatureSelectionRequest(BaseModel):
    """Request to run LASSO feature selection"""
    dataset_id: str = Field(..., description="ID of generated dataset")
    alphas: Optional[List[float]] = Field(default=None, description="Alpha values to try (default: [0.0001, 0.001, 0.01, 0.1, 1.0])")
    cv_folds: int = Field(default=5, ge=3, le=10, description="Number of CV folds")


class FeatureSelectionResponse(BaseModel):
    """Response from feature selection"""
    job_id: str
    status: TrainingStatus
    selected_features: Optional[List[str]] = None
    n_features_original: Optional[int] = None
    n_features_selected: Optional[int] = None
    optimal_alpha: Optional[float] = None
    top_features: Optional[List[Dict]] = None  # Top 10 features with coefficients


# ===== Base Model Training =====

class BaseModelTrainingRequest(BaseModel):
    """Request to train a single base model"""
    model_name: ModelName
    dataset_id: str
    n_trials: int = Field(default=100, ge=10, le=500, description="Number of Optuna trials")
    cv_folds: int = Field(default=5, ge=3, le=10, description="Number of CV folds")
    use_selected_features: bool = Field(default=True, description="Use LASSO-selected features")


class BaseModelTrainingResponse(BaseModel):
    """Response from base model training"""
    job_id: str
    status: TrainingStatus
    model_name: str
    oof_auc: Optional[float] = None
    cv_auc: Optional[float] = None
    best_params: Optional[Dict[str, Any]] = None
    training_time_seconds: Optional[float] = None
    model_artifact_path: Optional[str] = None  # MinIO path


# ===== Ensemble Training =====

class EnsembleTrainingRequest(BaseModel):
    """Request to train stacking ensemble"""
    dataset_id: str = Field(..., description="Dataset job ID used to train base models")
    base_model_jobs: List[str] = Field(..., min_length=2, description="List of base model job IDs (minimum 2 required)")
    meta_learner_type: Optional[str] = Field(default='logistic_regression', description="Meta-learner type: logistic_regression, xgboost, lightgbm, random_forest, mlp, ridge, elastic_net")
    target_column: Optional[str] = Field(default='labels_disease_classification', description="Target variable column name")
    batch_id: Optional[str] = Field(default=None, description="Original batch ID for metadata (optional)")


class EnsembleTrainingResponse(BaseModel):
    """Response from ensemble training"""
    job_id: str
    status: TrainingStatus
    ensemble_oof_auc: Optional[float] = None
    meta_weights: Optional[Dict[str, float]] = None  # Which models the meta-learner trusts
    base_models_included: Optional[List[str]] = None
    model_artifact_path: Optional[str] = None


# ===== Full Pipeline Training =====

class FullPipelineTrainingRequest(BaseModel):
    """Request to run complete training pipeline"""
    target_column: str = Field(default="clinical_diagnosis_category")
    test_size: float = Field(default=0.35, ge=0.1, le=0.5)
    random_state: int = Field(default=42)
    n_optuna_trials: int = Field(default=100, ge=10, le=500)
    models_to_train: Optional[List[ModelName]] = Field(
        default=None,
        description="List of models to train (default: all 10)"
    )


class FullPipelineTrainingResponse(BaseModel):
    """Response from full pipeline training"""
    job_id: str
    status: TrainingStatus
    message: str
    dataset_job_id: Optional[str] = None
    feature_selection_job_id: Optional[str] = None
    base_model_job_ids: Optional[Dict[str, str]] = None
    ensemble_job_id: Optional[str] = None


# ===== Training Job Status =====

class TrainingJobStatus(BaseModel):
    """Training job status response"""
    job_id: str
    status: TrainingStatus
    job_type: str  # 'dataset', 'feature_selection', 'base_model', 'ensemble', 'full_pipeline'
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: Optional[Dict[str, Any]] = None  # Current progress (e.g., "fold 3/5", "trial 50/100")
    result: Optional[Dict[str, Any]] = None  # Final result when completed
    error_message: Optional[str] = None


# ===== Model List =====

class TrainedModelInfo(BaseModel):
    """Information about a trained model"""
    model_id: str
    model_name: str
    model_type: str  # 'base_model' or 'ensemble'
    version: str
    trained_at: datetime
    train_samples: int
    test_samples: int
    oof_auc: Optional[float] = None
    test_auc: Optional[float] = None
    test_precision: Optional[float] = None
    test_recall: Optional[float] = None
    test_f1: Optional[float] = None
    test_accuracy: Optional[float] = None
    test_specificity: Optional[float] = None
    hyperparameters: Optional[Dict[str, Any]] = None
    feature_count: int
    artifact_path: str  # MinIO path
    feature_names: Optional[List[str]] = None  # Feature names from training


class ModelListResponse(BaseModel):
    """List of all trained models"""
    models: List[TrainedModelInfo]
    total_count: int


# ===== Evaluation =====

class ModelEvaluationRequest(BaseModel):
    """Request to evaluate a trained model"""
    model_id: str
    threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Classification threshold")


class ModelEvaluationResponse(BaseModel):
    """Model evaluation metrics"""
    model_id: str
    model_name: str
    auc_roc: float
    precision: float
    recall: float
    f1_score: float
    specificity: Optional[float] = None
    brier_score: float
    confusion_matrix: Dict[str, int]
    calibration_data: Optional[Dict] = None


class ModelComparisonRequest(BaseModel):
    """Request to compare multiple models"""
    model_ids: List[str] = Field(..., description="List of model IDs to compare (min 2)")


class ModelComparisonResponse(BaseModel):
    """Comparison of multiple models"""
    models: List[Dict[str, Any]]  # List of model metrics
    best_model_id: Optional[str] = None
    best_model_name: Optional[str] = None
    comparison_metric: str = 'auc_roc'


class TrainingHistoryItem(BaseModel):
    """Single training job in history"""
    job_id: str
    job_type: str
    model_name: Optional[str] = None
    status: TrainingStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    oof_auc: Optional[float] = None
    test_auc: Optional[float] = None
    test_f1: Optional[float] = None
    training_time_seconds: Optional[float] = None
    dataset_id: Optional[str] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    user_full_name: Optional[str] = None


class TrainingHistoryResponse(BaseModel):
    """Training history response"""
    jobs: List[TrainingHistoryItem]
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    running_jobs: int


# ===== INFERENCE SCHEMAS (NEW) =====

class PredictionRequest(BaseModel):
    """Request for making prediction on new patient data"""
    model_name: str = Field(..., description="Name of model to use (e.g., 'xgboost', 'ensemble')")
    version: str = Field(default="v1", description="Model version")
    patient_data: Dict[str, Any] = Field(..., description="Patient features matching training format")
    return_probability: bool = Field(default=True, description="Return probability or binary prediction")


class PredictionResponse(BaseModel):
    """Response from prediction - supports multi-class classification"""
    model_name: str
    version: str
    prediction: str  # Predicted class label (e.g., "Mild", "Moderate", "Severe")
    probabilities: Dict[str, float]  # Probability for each class {"Mild": 0.6, "Moderate": 0.3, "Severe": 0.1}
    confidence: float  # Confidence score (max probability)
    predicted_class_index: int  # Numeric class index (0, 1, 2)
    severity_category: str  # Same as prediction for SLE severity
    class_mapping: Dict[str, int]  # Maps class names to indices


class BatchPredictionRequest(BaseModel):
    """Request for batch predictions"""
    model_name: str
    version: str = "v1"
    patients_data: List[Dict[str, Any]] = Field(..., description="List of patient feature dictionaries")


class BatchPredictionResponse(BaseModel):
    """Response from batch predictions"""
    predictions: List[PredictionResponse]
    total_processed: int
    success_count: int
    failure_count: int


class ModelInfoRequest(BaseModel):
    """Request for model information"""
    model_name: str
    version: str = "v1"


class ModelInfoResponse(BaseModel):
    """Response with model information"""
    model_name: str
    version: str
    available_versions: List[str]
    metadata: Dict[str, Any]


class AvailableModelsResponse(BaseModel):
    """Response listing all available models"""
    models: List[Dict[str, Any]]
    total_count: int
