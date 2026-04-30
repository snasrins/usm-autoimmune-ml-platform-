"""
SHAP Explainability Service (USMA-50)
Provides model interpretability using SHAP (SHapley Additive exPlanations)
"""
import shap
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
import logging
import base64
import io
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server
import matplotlib.pyplot as plt

from app.services.minio_service import get_minio_service
from app.ml.feature_engineering_pipeline import FeatureEngineeringPipeline

logger = logging.getLogger(__name__)


class SHAPExplainerService:
    """Service for generating SHAP explanations for ML predictions"""
    
    def __init__(self, db: Session):
        self.db = db
        self.minio = get_minio_service()
        self.explainer_cache = {}  # Cache explainers in memory
    
    def explain_prediction(
        self,
        model_name: str,
        version: str,
        patient_data: Dict[str, Any],
        top_k: int = 10,
        generate_plot: bool = True
    ) -> Dict:
        """
        Explain a single prediction using SHAP values
        
        Args:
            model_name: Name of trained model
            version: Model version
            patient_data: Patient feature dictionary
            top_k: Number of top features to return
            generate_plot: Whether to generate waterfall plot
        
        Returns:
            Dictionary with SHAP values, top features, and optional plot
        """
        try:
            logger.info(f"Generating SHAP explanation for {model_name}/{version}")
            
            # Load model metadata
            metadata = self.minio.load_metadata(model_name, version)
            feature_names = metadata.get('feature_names', [])
            
            # Prepare patient data (same preprocessing as inference)
            df = pd.DataFrame([patient_data])
            
            # Apply feature engineering pipeline
            if 'feature_pipeline_config' in metadata:
                pipeline = FeatureEngineeringPipeline.from_config(metadata['feature_pipeline_config'])
                df = pipeline.transform(df, is_inference=True)
            
            # Ensure all required features are present
            missing_features = set(feature_names) - set(df.columns)
            if missing_features:
                for feat in missing_features:
                    df[feat] = 0
            
            # Select features in correct order
            X = df[feature_names]
            
            # Apply scaling if needed
            if metadata.get('requires_scaling', False) and 'scaler' in metadata:
                scaler = metadata['scaler']
                X = pd.DataFrame(
                    scaler.transform(X),
                    columns=feature_names
                )
            
            # Get SHAP explainer (use cache if available)
            explainer_key = f"{model_name}_{version}"
            if explainer_key not in self.explainer_cache:
                logger.info(f"Creating new SHAP explainer for {model_name}/{version}")
                explainer = self._create_explainer(model_name, version, metadata)
                self.explainer_cache[explainer_key] = explainer
            else:
                logger.info(f"Using cached SHAP explainer for {model_name}/{version}")
                explainer = self.explainer_cache[explainer_key]
            
            # Calculate SHAP values
            shap_values = explainer(X)
            
            # For multi-class, get SHAP values for predicted class
            if len(shap_values.shape) == 3:
                # Shape: [n_samples, n_features, n_classes]
                # Get predicted class
                model = self.minio.load_model(model_name, version)
                predicted_class = model.predict(X)[0]
                
                # Extract SHAP values for predicted class
                shap_values_for_class = shap_values[:, :, predicted_class]
                base_value = explainer.expected_value[predicted_class]
            else:
                # Binary classification or regression
                shap_values_for_class = shap_values
                base_value = explainer.expected_value
            
            # Get feature contributions
            shap_values_array = shap_values_for_class.values[0]
            
            # Create feature importance ranking
            feature_importance = pd.DataFrame({
                'feature': feature_names,
                'shap_value': shap_values_array,
                'abs_shap_value': np.abs(shap_values_array),
                'feature_value': X.iloc[0].values
            }).sort_values('abs_shap_value', ascending=False)
            
            # Top K features
            top_features = feature_importance.head(top_k).to_dict('records')
            
            # Generate waterfall plot (base64 encoded)
            plot_base64 = None
            if generate_plot:
                plot_base64 = self._generate_waterfall_plot(
                    shap_values_for_class[0],
                    base_value,
                    feature_names
                )
            
            # Get class mapping for multi-class
            class_mapping = metadata.get('class_mapping', {})
            idx_to_class = {v: k for k, v in class_mapping.items()}
            predicted_class_name = idx_to_class.get(predicted_class, f"Class_{predicted_class}") if len(shap_values.shape) == 3 else None
            
            result = {
                'model_name': model_name,
                'version': version,
                'predicted_class': predicted_class_name,
                'base_value': float(base_value),
                'top_features': [
                    {
                        'feature': f['feature'],
                        'shap_value': float(f['shap_value']),
                        'feature_value': float(f['feature_value']),
                        'contribution': 'positive' if f['shap_value'] > 0 else 'negative',
                        'importance': float(f['abs_shap_value'])
                    }
                    for f in top_features
                ],
                'all_features': feature_importance.to_dict('records'),
                'waterfall_plot': plot_base64,
                'explanation_text': self._generate_explanation_text(top_features[:5], predicted_class_name)
            }
            
            logger.info(f"SHAP explanation generated successfully")
            return result
        
        except Exception as e:
            logger.error(f"Error generating SHAP explanation: {e}")
            raise
    
    def _create_explainer(
        self,
        model_name: str,
        version: str,
        metadata: Dict
    ) -> shap.Explainer:
        """
        Create SHAP explainer for a model
        
        Uses TreeExplainer for tree-based models (XGBoost, LightGBM, RandomForest)
        Uses KernelExplainer for other models
        """
        try:
            # Load model
            n_folds = metadata.get('n_folds', 0)
            
            if n_folds > 1:
                # For CV models, use first fold for explanation
                model = self.minio.load_model(model_name, version, fold_id=0)
            else:
                model = self.minio.load_model(model_name, version)
            
            # Choose appropriate explainer based on model type
            model_type = model_name.lower()
            
            if any(tree_model in model_type for tree_model in ['xgboost', 'lightgbm', 'random_forest', 'catboost']):
                logger.info(f"Using TreeExplainer for {model_name}")
                # TreeExplainer for tree-based models (fast and exact)
                explainer = shap.TreeExplainer(model)
            else:
                logger.info(f"Using KernelExplainer for {model_name}")
                # KernelExplainer for other models (slower but model-agnostic)
                # Need background data - use a small sample
                # For now, use zero vector as background
                feature_names = metadata.get('feature_names', [])
                background = np.zeros((1, len(feature_names)))
                explainer = shap.KernelExplainer(model.predict_proba, background)
            
            return explainer
        
        except Exception as e:
            logger.error(f"Error creating SHAP explainer: {e}")
            raise
    
    def _generate_waterfall_plot(
        self,
        shap_values,
        base_value: float,
        feature_names: List[str]
    ) -> str:
        """
        Generate SHAP waterfall plot and return as base64 encoded image
        
        Args:
            shap_values: SHAP values for single prediction
            base_value: Expected value (baseline)
            feature_names: List of feature names
        
        Returns:
            Base64 encoded PNG image
        """
        try:
            # Create waterfall plot
            fig, ax = plt.subplots(figsize=(10, 6))
            shap.waterfall_plot(
                shap.Explanation(
                    values=shap_values.values,
                    base_values=base_value,
                    data=shap_values.data,
                    feature_names=feature_names
                ),
                max_display=15,
                show=False
            )
            
            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close(fig)
            
            return image_base64
        
        except Exception as e:
            logger.warning(f"Error generating waterfall plot: {e}")
            return None
    
    def _generate_explanation_text(
        self,
        top_features: List[Dict],
        predicted_class: Optional[str] = None
    ) -> str:
        """
        Generate human-readable explanation text
        
        Args:
            top_features: List of top contributing features
            predicted_class: Predicted class name (if multi-class)
        
        Returns:
            Explanation text
        """
        try:
            if not top_features:
                return "No significant features found."
            
            class_text = f"for {predicted_class} severity" if predicted_class else ""
            
            explanation = f"The model's prediction {class_text} is primarily driven by:\n\n"
            
            for i, feat in enumerate(top_features, 1):
                feature_name = feat['feature'].replace('_', ' ').title()
                shap_val = feat['shap_value']
                feat_val = feat['feature_value']
                
                direction = "increases" if shap_val > 0 else "decreases"
                
                explanation += f"{i}. **{feature_name}** (value: {feat_val:.2f}) {direction} the prediction by {abs(shap_val):.3f}\n"
            
            return explanation
        
        except Exception as e:
            logger.warning(f"Error generating explanation text: {e}")
            return "Explanation generation failed."
    
    def explain_ensemble(
        self,
        patient_data: Dict[str, Any],
        ensemble_version: str = 'v1',
        top_k: int = 10
    ) -> Dict:
        """
        Explain ensemble prediction (aggregates SHAP values from base models)
        
        Args:
            patient_data: Patient feature dictionary
            ensemble_version: Ensemble model version
            top_k: Number of top features to return
        
        Returns:
            Aggregated SHAP explanation
        """
        try:
            # For ensemble, explain each base model and aggregate
            # This is a simplified version - full ensemble SHAP is complex
            
            # For now, just explain the ensemble meta-learner
            return self.explain_prediction(
                model_name='ensemble',
                version=ensemble_version,
                patient_data=patient_data,
                top_k=top_k
            )
        
        except Exception as e:
            logger.error(f"Error explaining ensemble: {e}")
            raise
    
    def clear_cache(self):
        """Clear explainer cache (useful after model updates)"""
        self.explainer_cache.clear()
        logger.info("SHAP explainer cache cleared")
