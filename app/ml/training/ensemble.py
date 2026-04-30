"""
Stacking Ensemble Meta-Learner (Layer 7.5)
Combines predictions from all base models using a meta-learner
"""
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression, Ridge, ElasticNet
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.calibration import CalibratedClassifierCV
from typing import Dict, List, Literal, Optional
import logging

logger = logging.getLogger(__name__)


class StackingEnsemble:
    """
    Stacking ensemble that learns to combine base model predictions
    Uses out-of-fold predictions to avoid overfitting
    Supports multiple meta-learner types - USER CONFIGURABLE
    """
    
    def __init__(
        self, 
        meta_learner_type: Literal[
            'logistic_regression', 
            'xgboost', 
            'lightgbm', 
            'random_forest', 
            'mlp', 
            'ridge', 
            'elastic_net'
        ] = 'logistic_regression',
        random_state: int = 42,
        calibration_method: Optional[Literal['sigmoid', 'isotonic']] = 'isotonic'
    ):
        """
        Args:
            meta_learner_type: Type of meta-learner to use (USER CONFIGURABLE)
            random_state: Random seed
            calibration_method: Calibration method for clinical reliability
                - 'sigmoid': Platt scaling (assumes sigmoid calibration curve)
                - 'isotonic': Isotonic regression (non-parametric, more flexible)
                - None: No calibration (not recommended for clinical use)
        """
        self.random_state = random_state
        self.meta_learner_type = meta_learner_type
        self.calibration_method = calibration_method
        self.meta_scaler = StandardScaler()
        self.meta_learner = self._create_meta_learner(meta_learner_type)
        self.calibrated_meta_learner = None  # Will be set after calibration
        self.base_model_names = []
        self.meta_weights = None
        self.is_calibrated = False
        self.is_binary = None  # Will be set during fit
        self.n_classes = None  # Will be set during fit
    
    def _create_meta_learner(self, meta_learner_type: str):
        """Create meta-learner based on user selection"""
        if meta_learner_type == 'logistic_regression':
            return LogisticRegression(
                C=0.1,
                penalty='l2',
                solver='lbfgs',
                max_iter=1000,
                random_state=self.random_state
            )
        elif meta_learner_type == 'xgboost':
            import xgboost as xgb
            return xgb.XGBClassifier(
                n_estimators=100,
                max_depth=3,
                learning_rate=0.1,
                random_state=self.random_state,
                eval_metric='logloss'
            )
        elif meta_learner_type == 'lightgbm':
            import lightgbm as lgb
            return lgb.LGBMClassifier(
                n_estimators=100,
                max_depth=3,
                learning_rate=0.1,
                random_state=self.random_state,
                verbose=-1
            )
        elif meta_learner_type == 'random_forest':
            return RandomForestClassifier(
                n_estimators=100,
                max_depth=5,
                random_state=self.random_state
            )
        elif meta_learner_type == 'mlp':
            return MLPClassifier(
                hidden_layer_sizes=(50, 25),
                max_iter=1000,
                random_state=self.random_state
            )
        elif meta_learner_type == 'ridge':
            from sklearn.linear_model import RidgeClassifier
            return RidgeClassifier(
                alpha=1.0,
                random_state=self.random_state
            )
        elif meta_learner_type == 'elastic_net':
            from sklearn.linear_model import SGDClassifier
            return SGDClassifier(
                loss='log_loss',
                penalty='elasticnet',
                alpha=0.0001,
                l1_ratio=0.5,
                random_state=self.random_state
            )
        else:
            raise ValueError(f"Unknown meta_learner_type: {meta_learner_type}")
        
    def fit(
        self,
        oof_predictions: Dict[str, np.ndarray],
        y_train: pd.Series
    ) -> 'StackingEnsemble':
        """
        Train meta-learner on out-of-fold predictions from base models
        
        Args:
            oof_predictions: Dictionary mapping model_name -> OOF predictions
            y_train: True labels
            
        Returns:
            self
        """
        logger.info("Training stacking ensemble meta-learner...")
        
        # Build OOF matrix: [n_samples, n_models]
        self.base_model_names = sorted(oof_predictions.keys())
        oof_matrix = np.column_stack([
            oof_predictions[name] for name in self.base_model_names
        ])
        
        logger.info(f"OOF matrix shape: {oof_matrix.shape}")
        logger.info(f"Base models: {self.base_model_names}")
        
        # Scale OOF predictions
        oof_scaled = self.meta_scaler.fit_transform(oof_matrix)
        
        # Train meta-learner
        self.meta_learner.fit(oof_scaled, y_train)
        
        # Extract meta-learner weights (only for linear models)
        if hasattr(self.meta_learner, 'coef_'):
            self.meta_weights = dict(zip(
                self.base_model_names,
                self.meta_learner.coef_[0]
            ))
            logger.info(f"Meta-learner ({self.meta_learner_type}) weights:")
            for name, weight in sorted(self.meta_weights.items(), key=lambda x: -abs(x[1])):
                logger.info(f"  {name}: {weight:.4f}")
        elif hasattr(self.meta_learner, 'feature_importances_'):
            # For tree-based models, use feature importance
            self.meta_weights = dict(zip(
                self.base_model_names,
                self.meta_learner.feature_importances_
            ))
            logger.info(f"Meta-learner ({self.meta_learner_type}) feature importances:")
            for name, weight in sorted(self.meta_weights.items(), key=lambda x: -x[1]):
                logger.info(f"  {name}: {weight:.4f}")
        else:
            logger.info(f"Meta-learner ({self.meta_learner_type}) does not expose interpretable weights")
            self.meta_weights = {name: 1.0 / len(self.base_model_names) for name in self.base_model_names}
        
        # Calculate ensemble OOF AUC
        from sklearn.metrics import roc_auc_score
        
        # Detect if binary or multiclass and store for later use
        self.n_classes = len(np.unique(y_train))
        self.is_binary = self.n_classes == 2
        
        if self.is_binary:
            # Binary classification: use positive class probability
            ensemble_oof_preds = self.meta_learner.predict_proba(oof_scaled)[:, 1]
            ensemble_auc = roc_auc_score(y_train, ensemble_oof_preds)
        else:
            # Multiclass: use all probabilities with ovr strategy
            ensemble_oof_preds = self.meta_learner.predict_proba(oof_scaled)
            ensemble_auc = roc_auc_score(y_train, ensemble_oof_preds, multi_class='ovr', average='macro')
        
        logger.info(f"Ensemble OOF AUC (before calibration): {ensemble_auc:.4f}")
        
        # Apply probability calibration for clinical reliability
        if self.calibration_method is not None:
            logger.info(f"Calibrating ensemble probabilities using {self.calibration_method} method...")
            
            self.calibrated_meta_learner = CalibratedClassifierCV(
                self.meta_learner,
                method=self.calibration_method,
                cv='prefit',  # Use already fitted meta-learner
                n_jobs=-1
            )
            
            # Calibrate using OOF predictions (already out-of-fold, no leakage)
            self.calibrated_meta_learner.fit(oof_scaled, y_train)
            
            # Evaluate calibrated predictions
            if self.is_binary:
                calibrated_oof_preds = self.calibrated_meta_learner.predict_proba(oof_scaled)[:, 1]
                calibrated_auc = roc_auc_score(y_train, calibrated_oof_preds)
                
                # Calculate Brier score (calibration quality metric) - binary only
                from sklearn.metrics import brier_score_loss
                brier_before = brier_score_loss(y_train, ensemble_oof_preds)
                brier_after = brier_score_loss(y_train, calibrated_oof_preds)
            else:
                calibrated_oof_preds = self.calibrated_meta_learner.predict_proba(oof_scaled)
                calibrated_auc = roc_auc_score(y_train, calibrated_oof_preds, multi_class='ovr', average='macro')
                
                # Multiclass Brier score
                from sklearn.metrics import brier_score_loss
                brier_before = np.mean(np.sum((np.eye(self.n_classes)[y_train] - self.meta_learner.predict_proba(oof_scaled)) ** 2, axis=1))
                brier_after = np.mean(np.sum((np.eye(self.n_classes)[y_train] - calibrated_oof_preds) ** 2, axis=1))
            
            logger.info(f"  Calibration results:")
            logger.info(f"    AUC after calibration: {calibrated_auc:.4f}")
            logger.info(f"    Brier score before: {brier_before:.4f}")
            logger.info(f"    Brier score after:  {brier_after:.4f} (lower is better)")
            
            if brier_after < brier_before:
                logger.info(f"  ✓ Calibration improved probability quality")
                self.is_calibrated = True
            else:
                logger.warning(f"  ⚠️  Calibration did not improve Brier score")
                logger.warning(f"      This can happen with well-calibrated models like Logistic Regression")
        else:
            logger.warning("⚠️  Calibration disabled - probabilities may not be reliable for clinical use")
        
        return self
    
    def predict_proba(
        self,
        base_predictions: Dict[str, np.ndarray]
    ) -> np.ndarray:
        """
        Make probability predictions using stacking ensemble
        Uses calibrated meta-learner if available (recommended for clinical use)
        
        Args:
            base_predictions: Dictionary mapping model_name -> predictions
            
        Returns:
            Probability predictions from ensemble (calibrated if enabled)
        """
        # Build prediction matrix
        pred_matrix = np.column_stack([
            base_predictions[name] for name in self.base_model_names
        ])
        
        # Scale and predict
        pred_scaled = self.meta_scaler.transform(pred_matrix)
        
        # Use calibrated meta-learner if available
        if self.is_calibrated and self.calibrated_meta_learner is not None:
            ensemble_probs = self.calibrated_meta_learner.predict_proba(pred_scaled)
        else:
            ensemble_probs = self.meta_learner.predict_proba(pred_scaled)
        
        # For binary classification, return only positive class probability for backward compatibility
        if self.is_binary:
            return ensemble_probs[:, 1]
        else:
            return ensemble_probs
    
    def get_meta_weights(self) -> Dict[str, float]:
        """Get meta-learner weights for each base model"""
        return self.meta_weights
