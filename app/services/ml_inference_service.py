"""
ML Inference Service
Handles predictions on new data using trained models
Uses FeatureEngineeringPipeline to ensure feature consistency
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
import logging

from app.services.minio_service import get_minio_service
from app.ml.training.dataset_generator import DatasetGenerator
from app.ml.feature_engineering_pipeline import FeatureEngineeringPipeline

logger = logging.getLogger(__name__)


class MLInferenceService:
    """Service for making predictions with trained ML models"""
    
    def __init__(self, db: Session):
        self.db = db
        self.minio = get_minio_service()
    
    def predict_single(
        self,
        model_name: str,
        version: str,
        patient_data: Dict[str, Any],
        return_probability: bool = True
    ) -> Dict:
        """
        Make prediction for a single patient
        
        Args:
            model_name: Name of trained model ('xgboost', 'ensemble', etc.)
            version: Model version ('v1', 'v2', etc.)
            patient_data: Dictionary of patient features matching training format
            return_probability: If True, returns probability; if False, returns class
        
        Returns:
            Dictionary with prediction, probability, and risk category
        """
        try:
            # Load model metadata to get feature names and preprocessing info
            metadata = self.minio.load_metadata(model_name, version)
            
            if not metadata:
                raise ValueError(f"No metadata found for {model_name}/{version}")
            
            feature_names = metadata.get('feature_names', [])
            requires_scaling = metadata.get('requires_scaling', False)
            
            # Convert patient data to DataFrame
            df = pd.DataFrame([patient_data])
            
            # === CRITICAL: Apply feature engineering pipeline ===
            # This ensures derived features (CRP_ESR_ratio, etc.) are calculated
            # instead of filled with 0
            if 'feature_pipeline_config' in metadata:
                logger.info("Applying feature engineering pipeline from training...")
                pipeline = FeatureEngineeringPipeline.from_config(metadata['feature_pipeline_config'])
                df = pipeline.transform(df, is_inference=True)
                logger.info(f"After feature engineering: {df.shape[1]} features")
            else:
                logger.warning(
                    "⚠️ No feature_pipeline_config found in metadata - "
                    "model may have been trained before GAP 5 fix. "
                    "Derived features will be filled with 0 (predictions may be degraded)."
                )
            
            # Ensure all required features are present
            missing_features = set(feature_names) - set(df.columns)
            if missing_features:
                logger.warning(f"Missing {len(missing_features)} features after pipeline: {missing_features}")
                # Fill missing features with 0 (last resort)
                for feat in missing_features:
                    df[feat] = 0
            
            # Select only required features in correct order
            X = df[feature_names]
            
            # Handle scaling if model requires it
            if requires_scaling and 'scaler' in metadata:
                scaler = metadata['scaler']
                X = pd.DataFrame(
                    scaler.transform(X),
                    columns=feature_names
                )
            
            # Load model(s)
            if metadata.get('n_folds', 0) > 1:
                # For CV models, average predictions across folds
                fold_models = self.minio.load_all_folds(
                    model_name, version, metadata['n_folds']
                )
                all_probs = []
                for fold_model in fold_models:
                    prob = fold_model.predict_proba(X)  # Shape: [1, n_classes]
                    all_probs.append(prob)
                # Average across folds
                final_probs = np.mean(all_probs, axis=0)[0]  # Shape: [n_classes]
            else:
                # Single model
                model = self.minio.load_model(model_name, version)
                final_probs = model.predict_proba(X)[0]  # Shape: [n_classes]
            
            # Get predicted class (highest probability)
            predicted_class_idx = int(np.argmax(final_probs))
            confidence = float(final_probs[predicted_class_idx])
            
            # Get class mapping from metadata (e.g., {"Mild": 0, "Moderate": 1, "Severe": 2})
            class_mapping = metadata.get('class_mapping', {})
            
            # Inverse mapping (index -> class name)
            idx_to_class = {v: k for k, v in class_mapping.items()}
            
            # Get predicted class name
            prediction = idx_to_class.get(predicted_class_idx, f"Class_{predicted_class_idx}")
            
            # Build probabilities dict
            probabilities = {
                idx_to_class.get(i, f"Class_{i}"): float(final_probs[i])
                for i in range(len(final_probs))
            }
            
            result = {
                'model_name': model_name,
                'version': version,
                'prediction': prediction,
                'probabilities': probabilities,
                'confidence': confidence,
                'predicted_class_index': predicted_class_idx,
                'severity_category': prediction,  # For SLE, this is the severity
                'class_mapping': class_mapping
            }
            
            logger.info(f"Prediction made: {model_name} -> {prediction} (prob: {final_prob:.3f})")
            
            return result
        
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            raise
    
    def predict_batch(
        self,
        model_name: str,
        version: str,
        patient_data_list: List[Dict[str, Any]]
    ) -> List[Dict]:
        """
        Make predictions for multiple patients
        
        Args:
            model_name: Name of trained model
            version: Model version
            patient_data_list: List of patient feature dictionaries
        
        Returns:
            List of prediction dictionaries
        """
        try:
            results = []
            for patient_data in patient_data_list:
                result = self.predict_single(model_name, version, patient_data)
                results.append(result)
            
            return results
        
        except Exception as e:
            logger.error(f"Error in batch prediction: {e}")
            raise
    
    def predict_ensemble(
        self,
        patient_data: Dict[str, Any],
        ensemble_version: str = 'v1'
    ) -> Dict:
        """
        Make prediction using stacking ensemble (most accurate)
        
        Args:
            patient_data: Patient feature dictionary
            ensemble_version: Version of ensemble model
        
        Returns:
            Prediction dictionary with ensemble results
        """
        return self.predict_single('ensemble', ensemble_version, patient_data)
    
    def explain_prediction(
        self,
        model_name: str,
        version: str,
        patient_data: Dict[str, Any],
        top_k: int = 10
    ) -> Dict:
        """
        Explain a prediction using SHAP values (if available)
        
        Args:
            model_name: Name of trained model
            version: Model version
            patient_data: Patient feature dictionary
            top_k: Number of top features to return
        
        Returns:
            Dictionary with prediction and feature importance
        """
        try:
            # Make base prediction
            result = self.predict_single(model_name, version, patient_data)
            
            # Load SHAP explainer if available
            metadata = self.minio.load_metadata(model_name, version)
            
            if 'shap_explainer' in metadata:
                # TODO: Implement SHAP explanation
                # This requires storing the SHAP explainer object
                result['top_features'] = []
                result['explanation_available'] = False
            else:
                result['top_features'] = []
                result['explanation_available'] = False
            
            return result
        
        except Exception as e:
            logger.error(f"Error explaining prediction: {e}")
            raise
    
    def _get_risk_category(self, probability: float, thresholds: Dict[str, float] = None) -> str:
        """
        Map probability to risk category using calibrated or default thresholds
        
        Args:
            probability: Predicted probability (0-1)
            thresholds: Optional dict with 'low', 'medium', 'high' thresholds
                       If None, uses default fixed thresholds
        
        Returns:
            Risk category string
        """
        if thresholds is None:
            # Default fixed thresholds (fallback)
            thresholds = {'low': 0.25, 'medium': 0.50, 'high': 0.75}
        
        if probability < thresholds.get('low', 0.25):
            return "Low Risk"
        elif probability < thresholds.get('medium', 0.50):
            return "Medium Risk"
        elif probability < thresholds.get('high', 0.75):
            return "High Risk"
        else:
            return "Very High Risk"
    
    def calibrate_thresholds(
        self,
        y_true: np.ndarray,
        y_pred_proba: np.ndarray
    ) -> Dict[str, float]:
        """
        Calibrate risk thresholds using Youden's J statistic
        
        This method finds the optimal probability threshold that maximizes
        sensitivity + specificity (Youden's J index), then creates risk bins
        around this optimal point.
        
        Args:
            y_true: Ground truth labels (0 or 1)
            y_pred_proba: Predicted probabilities
        
        Returns:
            Dictionary with 'optimal', 'low', 'medium', 'high' thresholds
        """
        from sklearn.metrics import roc_curve
        
        # Compute ROC curve
        fpr, tpr, thresholds = roc_curve(y_true, y_pred_proba)
        
        # Calculate Youden's J statistic for each threshold
        j_scores = tpr - fpr
        
        # Find optimal threshold (maximizes J)
        optimal_idx = np.argmax(j_scores)
        optimal_threshold = thresholds[optimal_idx]
        
        logger.info(f"Youden's J optimal threshold: {optimal_threshold:.4f}")
        logger.info(f"  Sensitivity (TPR): {tpr[optimal_idx]:.4f}")
        logger.info(f"  Specificity (1-FPR): {1 - fpr[optimal_idx]:.4f}")
        logger.info(f"  J-statistic: {j_scores[optimal_idx]:.4f}")
        
        # Create risk bins around optimal threshold
        # Low: < 50% of optimal
        # Medium: 50% to optimal
        # High: optimal to 150% of optimal
        # Very High: > 150% of optimal
        calibrated_thresholds = {
            'optimal': float(optimal_threshold),
            'low': float(optimal_threshold * 0.5),
            'medium': float(optimal_threshold),
            'high': float(min(optimal_threshold * 1.5, 0.95))  # Cap at 0.95
        }
        
        return calibrated_thresholds
    
    def get_model_info(self, model_name: str, version: str) -> Dict:
        """
        Get model information and metadata
        
        Args:
            model_name: Name of the model
            version: Model version
        
        Returns:
            Model metadata dictionary
        """
        try:
            metadata = self.minio.load_metadata(model_name, version)
            
            # Add version list
            versions = self.minio.list_model_versions(model_name)
            
            return {
                'model_name': model_name,
                'version': version,
                'available_versions': versions,
                'metadata': metadata
            }
        
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            raise
    
    def list_available_models(self) -> List[Dict]:
        """
        List all available trained models
        
        Returns:
            List of model information dictionaries
        """
        try:
            # Get all models from MinIO
            models = []
            model_names = [
                'xgboost', 'lightgbm', 'catboost', 'random_forest',
                'adaboost', 'svm', 'mlp', 'knn', 'decision_tree',
                'logistic_regression', 'ensemble'
            ]
            
            for model_name in model_names:
                versions = self.minio.list_model_versions(model_name)
                if versions:
                    for version in versions:
                        metadata = self.minio.load_metadata(model_name, version)
                        models.append({
                            'model_name': model_name,
                            'version': version,
                            'trained_at': metadata.get('trained_at'),
                            'oof_auc': metadata.get('oof_auc'),
                            'cv_auc': metadata.get('cv_auc'),
                            'n_features': metadata.get('n_features')
                        })
            
            return models
        
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
