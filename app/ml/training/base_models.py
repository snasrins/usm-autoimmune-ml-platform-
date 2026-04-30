"""
Base Model Trainer (Layer 7)
Implements all 10 base ML algorithms with hyperparameter tuning
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from typing import Dict, List, Tuple, Optional
import logging
import joblib
from pathlib import Path

# Classifiers
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
import xgboost as xgb
import lightgbm as lgb
import catboost as cb
import optuna

logger = logging.getLogger(__name__)


class BaseModelTrainer:
    """
    Train individual base models with hyperparameter optimization
    Generates out-of-fold (OOF) predictions for stacking
    
    Supports separate feature sets:
    - Tree models (XGBoost, LightGBM, CatBoost, RF, AdaBoost, DT): Use raw features
    - Linear/Distance models (SVM, MLP, KNN, LR): Use scaled features
    """
    
    # Model type classification
    TREE_MODELS = ['xgboost', 'lightgbm', 'catboost', 'random_forest', 'adaboost', 'decision_tree', 'gradient_boosting']
    LINEAR_MODELS = ['svm', 'mlp', 'knn', 'logistic_regression', 'ridge_classifier', 'linear_discriminant']
    
    def __init__(self, random_state: int = 42, n_folds: int = 5):
        """
        Args:
            random_state: Random seed for reproducibility
            n_folds: Number of CV folds
        """
        self.random_state = random_state
        self.n_folds = n_folds
        self.skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=random_state)
        self.models = {}
        self.oof_predictions = {}
    
    def _select_features(
        self,
        model_name: str,
        X_train: pd.DataFrame,
        X_train_scaled: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Select appropriate feature set based on model type
        
        Args:
            model_name: Name of the model
            X_train: Raw features (for tree models)
            X_train_scaled: Scaled features (for linear models)
        
        Returns:
            Appropriate feature set for the model
        """
        if model_name in self.LINEAR_MODELS:
            if X_train_scaled is not None:
                logger.info(f"  → Using SCALED features for {model_name} (linear model)")
                return X_train_scaled
            else:
                logger.warning(f"  ⚠️  Scaled features not provided, using raw features for {model_name}")
                return X_train
        else:
            logger.info(f"  → Using RAW features for {model_name} (tree model)")
            return X_train
    
    def _apply_smote_if_needed(
        self,
        X_train_fold: pd.DataFrame,
        y_train_fold: pd.Series,
        apply_smote: bool = True,
        min_minority_ratio: float = 0.2
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Apply SMOTE to handle class imbalance INSIDE CV fold
        
        CRITICAL: This must run INSIDE the CV loop, not before splitting.
        Applying SMOTE before CV creates synthetic samples in both train and val,
        which is data leakage and inflates performance metrics.
        
        Args:
            X_train_fold: Training features for this fold
            y_train_fold: Training labels for this fold
            apply_smote: Whether to apply SMOTE
            min_minority_ratio: Minimum minority class ratio to trigger SMOTE (default 0.2)
        
        Returns:
            Tuple of (resampled X, resampled y)
        """
        if not apply_smote:
            return X_train_fold, y_train_fold
        
        # Check class imbalance
        class_counts = y_train_fold.value_counts()
        minority_class = class_counts.min()
        majority_class = class_counts.max()
        minority_ratio = minority_class / majority_class
        
        if minority_ratio < min_minority_ratio:
            logger.warning(f"  ⚠️  Class imbalance detected: {minority_ratio:.2%}")
            logger.warning(f"      Class distribution: {class_counts.to_dict()}")
            
            try:
                from imblearn.over_sampling import SMOTE
                
                smote = SMOTE(
                    sampling_strategy='auto',  # Balance to 1:1 ratio
                    random_state=self.random_state,
                    k_neighbors=min(5, minority_class - 1)  # Adjust k for small minority class
                )
                
                X_resampled, y_resampled = smote.fit_resample(X_train_fold, y_train_fold)
                
                logger.info(f"  ✓ SMOTE applied inside fold:")
                logger.info(f"      Before: {len(y_train_fold)} samples")
                logger.info(f"      After:  {len(y_resampled)} samples")
                logger.info(f"      New distribution: {pd.Series(y_resampled).value_counts().to_dict()}")
                
                # Convert back to DataFrame/Series
                X_resampled = pd.DataFrame(X_resampled, columns=X_train_fold.columns)
                y_resampled = pd.Series(y_resampled, name=y_train_fold.name)
                
                return X_resampled, y_resampled
                
            except ImportError:
                logger.error("  ❌ imbalanced-learn not installed. Install with: pip install imbalanced-learn")
                logger.warning("  Proceeding without SMOTE (performance may suffer)")
                return X_train_fold, y_train_fold
            except Exception as e:
                logger.error(f"  ❌ SMOTE failed: {e}")
                logger.warning("  Proceeding without SMOTE")
                return X_train_fold, y_train_fold
        else:
            logger.info(f"  ✓ Class balance acceptable ({minority_ratio:.2%}), skipping SMOTE")
            return X_train_fold, y_train_fold
        
    def train_xgboost(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        n_trials: int = 100,
        cat_features: List[str] = None,
        X_test: pd.DataFrame = None,
        y_test: pd.Series = None
    ) -> Dict:
        """
        Train XGBoost with Optuna hyperparameter tuning
        
        Args:
            X_train, y_train: Training data
            n_trials: Number of Optuna trials
            cat_features: Categorical features
            X_test, y_test: Optional test data for evaluation
            
        Returns:
            Dictionary with trained models, OOF predictions, and metrics
        """
        logger.info("Training XGBoost...")
        
        # Detect if binary or multi-class
        n_classes = len(np.unique(y_train))
        is_binary = n_classes == 2
        scoring_metric = 'roc_auc' if is_binary else 'roc_auc_ovr'
        
        logger.info(f"  → Detected {n_classes} classes ({'binary' if is_binary else 'multi-class'})")
        
        def objective(trial):
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 100, 500),
                'max_depth': trial.suggest_int('max_depth', 3, 7),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1, log=True),
                'subsample': trial.suggest_float('subsample', 0.7, 0.9),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.7, 0.9),
                'reg_alpha': trial.suggest_float('reg_alpha', 0.01, 1.0, log=True),
                'reg_lambda': trial.suggest_float('reg_lambda', 0.1, 10.0, log=True),
                'eval_metric': 'auc',
                'random_state': self.random_state,
                'use_label_encoder': False
            }
            
            # Add scale_pos_weight only for binary classification
            if is_binary:
                n_pos = (y_train == 1).sum()
                n_neg = (y_train == 0).sum()
                params['scale_pos_weight'] = n_neg / n_pos if n_pos > 0 else 1.0
            
            model = xgb.XGBClassifier(**params)
            score = cross_val_score(model, X_train, y_train, cv=self.skf, scoring=scoring_metric).mean()
            return score
        
        # Hyperparameter optimization
        study = optuna.create_study(direction='maximize', study_name='xgboost')
        study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
        
        best_params = study.best_params
        best_params.update({
            'eval_metric': 'auc',
            'random_state': self.random_state,
            'use_label_encoder': False
        })
        
        # Add scale_pos_weight only for binary classification
        if is_binary:
            best_params['scale_pos_weight'] = (y_train == 0).sum() / (y_train == 1).sum()
        
        logger.info(f"Best XGBoost params: {best_params}")
        logger.info(f"Best CV AUC: {study.best_value:.4f}")
        
        # Train on all folds and generate OOF predictions
        oof_preds, fold_models = self._train_with_cv(
            X_train, y_train,
            model_class=xgb.XGBClassifier,
            params=best_params
        )
        
        result = {
            'model_name': 'xgboost',
            'fold_models': fold_models,
            'oof_predictions': oof_preds,
            'oof_auc': self._calculate_auc(y_train, oof_preds),
            'best_params': best_params,
            'cv_auc': study.best_value
        }
        
        # Evaluate on test set if provided
        if X_test is not None and y_test is not None:
            from sklearn.metrics import precision_score, recall_score, f1_score, brier_score_loss, roc_auc_score
            
            # Use the first fold model for test evaluation (or ensemble them)
            test_model = fold_models[0]  # Simple approach: use first fold
            test_proba = test_model.predict_proba(X_test)
            
            # Handle binary vs multi-class
            if is_binary:
                test_proba_pos = test_proba[:, 1]  # Probability of positive class
                test_auc = roc_auc_score(y_test, test_proba_pos)
                test_brier = brier_score_loss(y_test, test_proba_pos)
                test_pred = (test_proba_pos >= 0.5).astype(int)
                avg_method = 'binary'
            else:
                # Multi-class: use OVR AUC and macro-averaged metrics
                test_auc = roc_auc_score(y_test, test_proba, multi_class='ovr', average='macro')
                test_pred = np.argmax(test_proba, axis=1)
                # For multi-class Brier score, use squared error on probability matrix
                test_brier = np.mean(np.sum((np.eye(n_classes)[y_test] - test_proba) ** 2, axis=1))
                avg_method = 'macro'
            
            # Calculate classification metrics
            test_precision = precision_score(y_test, test_pred, average=avg_method, zero_division=0)
            test_recall = recall_score(y_test, test_pred, average=avg_method, zero_division=0)
            test_f1 = f1_score(y_test, test_pred, average=avg_method, zero_division=0)
            
            result.update({
                'test_auc': test_auc,
                'test_precision': test_precision,
                'test_recall': test_recall,
                'test_f1': test_f1,
                'test_brier_score': test_brier
            })
            
            logger.info(f"XGBoost Test AUC: {test_auc:.4f}, F1: {test_f1:.4f}")
        
        self.models['xgboost'] = result
        self.oof_predictions['xgboost'] = oof_preds
        
        logger.info(f"XGBoost OOF AUC: {result['oof_auc']:.4f}")
        
        return result
    
    def train_lightgbm(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        n_trials: int = 100,
        X_test: Optional[pd.DataFrame] = None,
        y_test: Optional[pd.Series] = None
    ) -> Dict:
        """Train LightGBM with Optuna"""
        logger.info("Training LightGBM...")
        
        # Detect if binary or multi-class
        n_classes = len(np.unique(y_train))
        is_binary = n_classes == 2
        scoring_metric = 'roc_auc' if is_binary else 'roc_auc_ovr'
        
        logger.info(f"  → Detected {n_classes} classes ({'binary' if is_binary else 'multi-class'})")
        
        def objective(trial):
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 100, 500),
                'num_leaves': trial.suggest_int('num_leaves', 15, 31),
                'max_depth': trial.suggest_int('max_depth', 4, 7),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1, log=True),
                'subsample': trial.suggest_float('subsample', 0.7, 0.9),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.7, 0.9),
                'min_child_samples': trial.suggest_int('min_child_samples', 5, 10),
                'reg_alpha': trial.suggest_float('reg_alpha', 0.01, 1.0, log=True),
                'reg_lambda': trial.suggest_float('reg_lambda', 0.1, 10.0, log=True),
                'random_state': self.random_state
            }
            
            # Only add class_weight for binary
            if is_binary:
                params['class_weight'] = 'balanced'
            
            model = lgb.LGBMClassifier(**params)
            score = cross_val_score(model, X_train, y_train, cv=self.skf, scoring=scoring_metric).mean()
            return score
        
        study = optuna.create_study(direction='maximize', study_name='lightgbm')
        study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
        
        best_params = study.best_params
        best_params.update({'random_state': self.random_state})
        
        # Only add class_weight for binary
        if is_binary:
            best_params['class_weight'] = 'balanced'
        
        logger.info(f"Best LightGBM params: {best_params}")
        logger.info(f"Best CV AUC: {study.best_value:.4f}")
        
        oof_preds, fold_models = self._train_with_cv(
            X_train, y_train,
            model_class=lgb.LGBMClassifier,
            params=best_params
        )
        
        result = {
            'model_name': 'lightgbm',
            'fold_models': fold_models,
            'oof_predictions': oof_preds,
            'oof_auc': self._calculate_auc(y_train, oof_preds),
            'best_params': best_params,
            'cv_auc': study.best_value
        }
        
        # Evaluate on test set if provided
        if X_test is not None and y_test is not None:
            from sklearn.metrics import precision_score, recall_score, f1_score, brier_score_loss, roc_auc_score
            
            test_model = fold_models[0]
            test_proba = test_model.predict_proba(X_test)
            
            # Handle binary vs multi-class
            if is_binary:
                test_proba_pos = test_proba[:, 1]
                test_auc = roc_auc_score(y_test, test_proba_pos)
                test_brier = brier_score_loss(y_test, test_proba_pos)
                test_pred = (test_proba_pos >= 0.5).astype(int)
                avg_method = 'binary'
            else:
                test_auc = roc_auc_score(y_test, test_proba, multi_class='ovr', average='macro')
                test_pred = np.argmax(test_proba, axis=1)
                test_brier = np.mean(np.sum((np.eye(n_classes)[y_test] - test_proba) ** 2, axis=1))
                avg_method = 'macro'
            
            test_precision = precision_score(y_test, test_pred, average=avg_method, zero_division=0)
            test_recall = recall_score(y_test, test_pred, average=avg_method, zero_division=0)
            test_f1 = f1_score(y_test, test_pred, average=avg_method, zero_division=0)
            
            result.update({
                'test_auc': test_auc,
                'test_precision': test_precision,
                'test_recall': test_recall,
                'test_f1': test_f1,
                'test_brier_score': test_brier
            })
            
            logger.info(f"LightGBM Test AUC: {test_auc:.4f}, F1: {test_f1:.4f}")
        
        self.models['lightgbm'] = result
        self.oof_predictions['lightgbm'] = oof_preds
        
        logger.info(f"LightGBM OOF AUC: {result['oof_auc']:.4f}")
        
        return result
    
    def train_catboost(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        cat_features: List[str] = None,
        n_trials: int = 100,
        X_test: Optional[pd.DataFrame] = None,
        y_test: Optional[pd.Series] = None
    ) -> Dict:
        """Train CatBoost with categorical feature support"""
        logger.info("Training CatBoost...")
        
        # Detect binary vs multiclass
        n_classes = len(np.unique(y_train))
        is_binary = n_classes == 2
        logger.info(f"  → Detected {n_classes} classes ({'binary' if is_binary else 'multi-class'})")
        
        # Identify categorical feature indices
        if cat_features is None:
            cat_features = X_train.select_dtypes(include=['object', 'category']).columns.tolist()
        
        cat_indices = [X_train.columns.get_loc(c) for c in cat_features if c in X_train.columns]
        
        def objective(trial):
            params = {
                'iterations': trial.suggest_int('iterations', 100, 500),
                'depth': trial.suggest_int('depth', 4, 8),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1, log=True),
                'l2_leaf_reg': trial.suggest_float('l2_leaf_reg', 1.0, 10.0),
                'auto_class_weights': 'Balanced',
                'eval_metric': 'AUC',
                'random_seed': self.random_state,
                'verbose': False
            }
            
            model = cb.CatBoostClassifier(**params)
            
            # CatBoost requires special CV handling for categorical features
            scores = []
            for train_idx, val_idx in self.skf.split(X_train, y_train):
                # CRITICAL: Verify no data leakage
                assert len(set(train_idx) & set(val_idx)) == 0, "DATA LEAKAGE: train and val indices overlap!"
                
                X_tr, X_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
                y_tr, y_val = y_train.iloc[train_idx], y_train.iloc[val_idx]
                
                model.fit(X_tr, y_tr, cat_features=cat_indices, eval_set=(X_val, y_val), verbose=False)
                score = model.score(X_val, y_val)
                scores.append(score)
            
            return np.mean(scores)
        
        study = optuna.create_study(direction='maximize', study_name='catboost')
        study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
        
        best_params = study.best_params
        best_params.update({
            'auto_class_weights': 'Balanced',
            'eval_metric': 'AUC',
            'random_seed': self.random_state,
            'verbose': False
        })
        
        # Train with CV
        if is_binary:
            oof_preds = np.zeros(len(X_train))
        else:
            oof_preds = np.zeros((len(X_train), n_classes))
        
        fold_models = []
        
        for fold_idx, (train_idx, val_idx) in enumerate(self.skf.split(X_train, y_train)):
            # CRITICAL: Verify no data leakage
            assert len(set(train_idx) & set(val_idx)) == 0, f"DATA LEAKAGE in Fold {fold_idx}: train and val overlap!"
            
            X_tr, X_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
            y_tr, y_val = y_train.iloc[train_idx], y_train.iloc[val_idx]
            
            model = cb.CatBoostClassifier(**best_params)
            model.fit(X_tr, y_tr, cat_features=cat_indices, eval_set=(X_val, y_val), verbose=False)
            
            # Store predictions based on binary vs multiclass
            if is_binary:
                oof_preds[val_idx] = model.predict_proba(X_val)[:, 1]
            else:
                oof_preds[val_idx] = model.predict_proba(X_val)
            
            fold_models.append(model)
            
            logger.info(f"CatBoost Fold {fold_idx + 1} completed")
        
        result = {
            'model_name': 'catboost',
            'fold_models': fold_models,
            'oof_predictions': oof_preds,
            'oof_auc': self._calculate_auc(y_train, oof_preds),
            'best_params': best_params,
            'cv_auc': study.best_value,
            'cat_features': cat_features
        }
        
        # Evaluate on test set if provided
        if X_test is not None and y_test is not None:
            test_model = fold_models[0]
            test_proba = test_model.predict_proba(X_test)
            
            # Handle binary vs multiclass
            if is_binary:
                test_proba_pos = test_proba[:, 1]
                test_auc = self._calculate_auc(y_test, test_proba_pos)
                test_pred = (test_proba_pos >= 0.5).astype(int)
            else:
                # Multiclass: use full probability matrix for AUC
                test_auc = self._calculate_auc(y_test, test_proba)
                test_pred = np.argmax(test_proba, axis=1)
            
            from sklearn.metrics import precision_score, recall_score, f1_score
            test_precision = precision_score(y_test, test_pred, average='weighted', zero_division=0)
            test_recall = recall_score(y_test, test_pred, average='weighted', zero_division=0)
            test_f1 = f1_score(y_test, test_pred, average='weighted', zero_division=0)
            
            result.update({
                'test_auc': test_auc,
                'test_precision': test_precision,
                'test_recall': test_recall,
                'test_f1': test_f1
            })
            
            logger.info(f"CatBoost Test AUC: {test_auc:.4f}, F1: {test_f1:.4f}")
        
        self.models['catboost'] = result
        self.oof_predictions['catboost'] = oof_preds
        
        logger.info(f"CatBoost OOF AUC: {result['oof_auc']:.4f}")
        
        return result
    
    def _train_with_cv(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        model_class,
        params: Dict
    ) -> Tuple[np.ndarray, List]:
        """
        Generic CV training function
        Returns OOF predictions and list of trained fold models
        """
        oof_preds = np.zeros(len(X_train))
        fold_models = []
        
        for fold_idx, (train_idx, val_idx) in enumerate(self.skf.split(X_train, y_train)):
            # CRITICAL: Verify no data leakage
            assert len(set(train_idx) & set(val_idx)) == 0, f"DATA LEAKAGE in Fold {fold_idx}: train and val overlap!"
            
            X_tr, X_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
            y_tr, y_val = y_train.iloc[train_idx], y_train.iloc[val_idx]
            
            model = model_class(**params)
            model.fit(X_tr, y_tr)
            
            oof_preds[val_idx] = model.predict_proba(X_val)[:, 1]
            fold_models.append(model)
            
            logger.debug(f"Fold {fold_idx + 1} completed")
        
        return oof_preds, fold_models
    
    def _calculate_auc(self, y_true: pd.Series, y_pred: np.ndarray) -> float:
        """Calculate AUC-ROC score"""
        from sklearn.metrics import roc_auc_score
        try:
            return roc_auc_score(y_true, y_pred)
        except ValueError:
            return 0.0
    
    def train_random_forest(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        n_trials: int = 100,
        X_test: Optional[pd.DataFrame] = None,
        y_test: Optional[pd.Series] = None
    ) -> Dict:
        """Train Random Forest with Optuna"""
        logger.info("Training Random Forest...")
        
        # Detect if binary or multi-class
        n_classes = len(np.unique(y_train))
        is_binary = n_classes == 2
        scoring_metric = 'roc_auc' if is_binary else 'roc_auc_ovr'
        
        logger.info(f"  → Detected {n_classes} classes ({'binary' if is_binary else 'multi-class'})")
        
        def objective(trial):
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 100, 500),
                'max_depth': trial.suggest_int('max_depth', 5, 15),
                'min_samples_split': trial.suggest_int('min_samples_split', 2, 10),
                'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 5),
                'max_features': trial.suggest_categorical('max_features', ['sqrt', 'log2', None]),
                'random_state': self.random_state,
                'n_jobs': -1
            }
            
            # Only add class_weight for binary
            if is_binary:
                params['class_weight'] = 'balanced'
            
            model = RandomForestClassifier(**params)
            score = cross_val_score(model, X_train, y_train, cv=self.skf, scoring=scoring_metric).mean()
            return score
        
        study = optuna.create_study(direction='maximize', study_name='random_forest')
        study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
        
        best_params = study.best_params
        best_params.update({'random_state': self.random_state, 'n_jobs': -1})
        
        # Only add class_weight for binary
        if is_binary:
            best_params['class_weight'] = 'balanced'
        
        logger.info(f"Best Random Forest params: {best_params}")
        logger.info(f"Best CV AUC: {study.best_value:.4f}")
        
        oof_preds, fold_models = self._train_with_cv(
            X_train, y_train,
            model_class=RandomForestClassifier,
            params=best_params
        )
        
        result = {
            'model_name': 'random_forest',
            'fold_models': fold_models,
            'oof_predictions': oof_preds,
            'oof_auc': self._calculate_auc(y_train, oof_preds),
            'best_params': best_params,
            'cv_auc': study.best_value
        }
        
        # Evaluate on test set if provided
        if X_test is not None and y_test is not None:
            from sklearn.metrics import precision_score, recall_score, f1_score, brier_score_loss, roc_auc_score
            
            test_model = fold_models[0]
            test_proba = test_model.predict_proba(X_test)
            
            # Handle binary vs multi-class
            if is_binary:
                test_proba_pos = test_proba[:, 1]
                test_auc = roc_auc_score(y_test, test_proba_pos)
                test_brier = brier_score_loss(y_test, test_proba_pos)
                test_pred = (test_proba_pos >= 0.5).astype(int)
                avg_method = 'binary'
            else:
                test_auc = roc_auc_score(y_test, test_proba, multi_class='ovr', average='macro')
                test_pred = np.argmax(test_proba, axis=1)
                test_brier = np.mean(np.sum((np.eye(n_classes)[y_test] - test_proba) ** 2, axis=1))
                avg_method = 'macro'
            
            test_precision = precision_score(y_test, test_pred, average=avg_method, zero_division=0)
            test_recall = recall_score(y_test, test_pred, average=avg_method, zero_division=0)
            test_f1 = f1_score(y_test, test_pred, average=avg_method, zero_division=0)
            
            result.update({
                'test_auc': test_auc,
                'test_precision': test_precision,
                'test_recall': test_recall,
                'test_f1': test_f1,
                'test_brier_score': test_brier
            })
            
            logger.info(f"Random Forest Test AUC: {test_auc:.4f}, F1: {test_f1:.4f}")
        
        self.models['random_forest'] = result
        self.oof_predictions['random_forest'] = oof_preds
        
        logger.info(f"Random Forest OOF AUC: {result['oof_auc']:.4f}")
        
        return result
    
    def train_adaboost(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        n_trials: int = 50,
        X_test: Optional[pd.DataFrame] = None,
        y_test: Optional[pd.Series] = None
    ) -> Dict:
        """Train AdaBoost with Decision Tree stumps"""
        logger.info("Training AdaBoost...")
        
        def objective(trial):
            # Base estimator: Decision Tree stump
            base_max_depth = trial.suggest_int('base_max_depth', 1, 3)
            base_estimator = DecisionTreeClassifier(max_depth=base_max_depth, random_state=self.random_state)
            
            params = {
                'estimator': base_estimator,
                'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                'learning_rate': trial.suggest_float('learning_rate', 0.1, 1.0, log=True),
                'algorithm': 'SAMME.R',
                'random_state': self.random_state
            }
            
            model = AdaBoostClassifier(**params)
            score = cross_val_score(model, X_train, y_train, cv=self.skf, scoring='roc_auc_ovr').mean()
            return score
        
        study = optuna.create_study(direction='maximize', study_name='adaboost')
        study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
        
        best_params = study.best_params
        base_max_depth = best_params.pop('base_max_depth')
        base_estimator = DecisionTreeClassifier(max_depth=base_max_depth, random_state=self.random_state)
        best_params.update({
            'estimator': base_estimator,
            'algorithm': 'SAMME.R',
            'random_state': self.random_state
        })
        
        logger.info(f"Best AdaBoost params: {best_params}")
        logger.info(f"Best CV AUC: {study.best_value:.4f}")
        
        oof_preds, fold_models = self._train_with_cv(
            X_train, y_train,
            model_class=AdaBoostClassifier,
            params=best_params
        )
        
        result = {
            'model_name': 'adaboost',
            'fold_models': fold_models,
            'oof_predictions': oof_preds,
            'oof_auc': self._calculate_auc(y_train, oof_preds),
            'best_params': best_params,
            'cv_auc': study.best_value
        }
        
        # Evaluate on test set if provided
        if X_test is not None and y_test is not None:
            test_model = fold_models[0]
            test_proba = test_model.predict_proba(X_test)[:, 1]
            test_auc = self._calculate_auc(y_test, test_proba)
            
            test_pred = (test_proba >= 0.5).astype(int)
            from sklearn.metrics import precision_score, recall_score, f1_score
            test_precision = precision_score(y_test, test_pred, average='weighted', zero_division=0)
            test_recall = recall_score(y_test, test_pred, average='weighted', zero_division=0)
            test_f1 = f1_score(y_test, test_pred, average='weighted', zero_division=0)
            
            result.update({
                'test_auc': test_auc,
                'test_precision': test_precision,
                'test_recall': test_recall,
                'test_f1': test_f1
            })
            
            logger.info(f"AdaBoost Test AUC: {test_auc:.4f}, F1: {test_f1:.4f}")
        
        self.models['adaboost'] = result
        self.oof_predictions['adaboost'] = oof_preds
        
        logger.info(f"AdaBoost OOF AUC: {result['oof_auc']:.4f}")
        
        return result
    
    def train_svm(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        n_trials: int = 50,
        X_train_scaled: Optional[pd.DataFrame] = None,
        X_test: Optional[pd.DataFrame] = None,
        y_test: Optional[pd.Series] = None,
        X_test_scaled: Optional[pd.DataFrame] = None
    ) -> Dict:
        """
        Train SVM with scaled features (REQUIRES probability=True)
        
        Args:
            X_train: Raw features (fallback if X_train_scaled not provided)
            y_train: Target variable
            n_trials: Number of Optuna trials
            X_train_scaled: Pre-scaled features (recommended for SVM)
        """
        logger.info("Training SVM...")
        
        # Use pre-scaled features if available, otherwise scale now
        if X_train_scaled is not None:
            logger.info("  → Using PRE-SCALED features from dataset generator")
            X_scaled = X_train_scaled
            scaler = None  # Already scaled
        else:
            logger.warning("  ⚠️  X_train_scaled not provided, scaling raw features now")
            scaler = StandardScaler()
            X_scaled = pd.DataFrame(
                scaler.fit_transform(X_train),
                columns=X_train.columns,
                index=X_train.index
            )
        
        def objective(trial):
            params = {
                'C': trial.suggest_float('C', 0.01, 100, log=True),
                'kernel': trial.suggest_categorical('kernel', ['rbf', 'linear']),
                'gamma': trial.suggest_categorical('gamma', ['scale', 'auto']),
                'probability': True,  # CRITICAL for stacking
                'class_weight': 'balanced',
                'random_state': self.random_state
            }
            
            model = SVC(**params)
            score = cross_val_score(model, X_scaled, y_train, cv=self.skf, scoring='roc_auc_ovr').mean()
            return score
        
        study = optuna.create_study(direction='maximize', study_name='svm')
        study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
        
        best_params = study.best_params
        best_params.update({
            'probability': True,
            'class_weight': 'balanced',
            'random_state': self.random_state
        })
        
        logger.info(f"Best SVM params: {best_params}")
        logger.info(f"Best CV AUC: {study.best_value:.4f}")
        
        oof_preds, fold_models = self._train_with_cv(
            X_scaled, y_train,
            model_class=SVC,
            params=best_params
        )
        
        result = {
            'model_name': 'svm',
            'fold_models': fold_models,
            'oof_predictions': oof_preds,
            'oof_auc': self._calculate_auc(y_train, oof_preds),
            'best_params': best_params,
            'cv_auc': study.best_value,
            'scaler': scaler  # Store scaler for test predictions
        }
        
        # Evaluate on test set if provided
        if X_test is not None and y_test is not None:
            # Use pre-scaled test features if available
            if X_test_scaled is not None:
                X_test_eval = X_test_scaled
            else:
                # Scale test features with training scaler
                if scaler is not None:
                    X_test_eval = pd.DataFrame(
                        scaler.transform(X_test),
                        columns=X_test.columns,
                        index=X_test.index
                    )
                else:
                    logger.warning("No scaler available for test evaluation")
                    X_test_eval = X_test
            
            test_model = fold_models[0]
            test_proba = test_model.predict_proba(X_test_eval)[:, 1]
            test_auc = self._calculate_auc(y_test, test_proba)
            
            test_pred = (test_proba >= 0.5).astype(int)
            from sklearn.metrics import precision_score, recall_score, f1_score
            test_precision = precision_score(y_test, test_pred, average='weighted', zero_division=0)
            test_recall = recall_score(y_test, test_pred, average='weighted', zero_division=0)
            test_f1 = f1_score(y_test, test_pred, average='weighted', zero_division=0)
            
            result.update({
                'test_auc': test_auc,
                'test_precision': test_precision,
                'test_recall': test_recall,
                'test_f1': test_f1
            })
            
            logger.info(f"SVM Test AUC: {test_auc:.4f}, F1: {test_f1:.4f}")
        
        self.models['svm'] = result
        self.oof_predictions['svm'] = oof_preds
        
        logger.info(f"SVM OOF AUC: {result['oof_auc']:.4f}")
        
        return result
    
    def train_mlp(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        n_trials: int = 50,
        X_train_scaled: Optional[pd.DataFrame] = None,
        X_test: Optional[pd.DataFrame] = None,
        y_test: Optional[pd.Series] = None,
        X_test_scaled: Optional[pd.DataFrame] = None
    ) -> Dict:
        """
        Train MLP Neural Network with scaled features
        
        Args:
            X_train: Raw features
            y_train: Target variable
            n_trials: Number of Optuna trials
            X_train_scaled: Pre-scaled features (recommended for MLP)
        """
        logger.info("Training MLP...")
        
        # Use pre-scaled features if available
        if X_train_scaled is not None:
            logger.info("  → Using PRE-SCALED features from dataset generator")
            X_scaled = X_train_scaled
            scaler = None
        else:
            logger.warning("  ⚠️  X_train_scaled not provided, scaling raw features now")
            scaler = StandardScaler()
            X_scaled = pd.DataFrame(
                scaler.fit_transform(X_train),
            columns=X_train.columns,
            index=X_train.index
        )
        
        def objective(trial):
            # Hidden layer architecture
            n_layers = trial.suggest_int('n_layers', 1, 3)
            hidden_layer_sizes = []
            for i in range(n_layers):
                hidden_layer_sizes.append(trial.suggest_int(f'n_units_l{i}', 16, 128, step=16))
            
            params = {
                'hidden_layer_sizes': tuple(hidden_layer_sizes),
                'activation': trial.suggest_categorical('activation', ['relu', 'tanh']),
                'alpha': trial.suggest_float('alpha', 0.001, 0.1, log=True),
                'learning_rate_init': trial.suggest_float('learning_rate_init', 0.0001, 0.01, log=True),
                'early_stopping': True,
                'n_iter_no_change': 20,
                'max_iter': 300,
                'random_state': self.random_state
            }
            
            model = MLPClassifier(**params)
            score = cross_val_score(model, X_scaled, y_train, cv=self.skf, scoring='roc_auc_ovr').mean()
            return score
        
        study = optuna.create_study(direction='maximize', study_name='mlp')
        study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
        
        best_params = study.best_params
        
        # Reconstruct hidden layer sizes from trial params
        n_layers = best_params.pop('n_layers')
        hidden_layer_sizes = tuple([best_params.pop(f'n_units_l{i}') for i in range(n_layers)])
        best_params['hidden_layer_sizes'] = hidden_layer_sizes
        best_params.update({
            'early_stopping': True,
            'n_iter_no_change': 20,
            'max_iter': 300,
            'random_state': self.random_state
        })
        
        logger.info(f"Best MLP params: {best_params}")
        logger.info(f"Best CV AUC: {study.best_value:.4f}")
        
        oof_preds, fold_models = self._train_with_cv(
            X_scaled, y_train,
            model_class=MLPClassifier,
            params=best_params
        )
        
        result = {
            'model_name': 'mlp',
            'fold_models': fold_models,
            'oof_predictions': oof_preds,
            'oof_auc': self._calculate_auc(y_train, oof_preds),
            'best_params': best_params,
            'cv_auc': study.best_value,
            'scaler': scaler
        }
        
        # Evaluate on test set if provided
        if X_test is not None and y_test is not None:
            # Use pre-scaled test features if available
            if X_test_scaled is not None:
                X_test_eval = X_test_scaled
            else:
                # Scale test features with training scaler
                if scaler is not None:
                    X_test_eval = pd.DataFrame(
                        scaler.transform(X_test),
                        columns=X_test.columns,
                        index=X_test.index
                    )
                else:
                    logger.warning("No scaler available for test evaluation")
                    X_test_eval = X_test
            
            test_model = fold_models[0]
            test_proba = test_model.predict_proba(X_test_eval)[:, 1]
            test_auc = self._calculate_auc(y_test, test_proba)
            
            test_pred = (test_proba >= 0.5).astype(int)
            from sklearn.metrics import precision_score, recall_score, f1_score
            test_precision = precision_score(y_test, test_pred, average='weighted', zero_division=0)
            test_recall = recall_score(y_test, test_pred, average='weighted', zero_division=0)
            test_f1 = f1_score(y_test, test_pred, average='weighted', zero_division=0)
            
            result.update({
                'test_auc': test_auc,
                'test_precision': test_precision,
                'test_recall': test_recall,
                'test_f1': test_f1
            })
            
            logger.info(f"MLP Test AUC: {test_auc:.4f}, F1: {test_f1:.4f}")
        
        self.models['mlp'] = result
        self.oof_predictions['mlp'] = oof_preds
        
        logger.info(f"MLP OOF AUC: {result['oof_auc']:.4f}")
        
        return result
    
    def train_knn(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        n_trials: int = 30,
        X_train_scaled: Optional[pd.DataFrame] = None,
        X_test: Optional[pd.DataFrame] = None,
        y_test: Optional[pd.Series] = None,
        X_test_scaled: Optional[pd.DataFrame] = None
    ) -> Dict:
        """
        Train KNN with scaled features
        
        Args:
            X_train: Raw features
            y_train: Target variable
            n_trials: Number of Optuna trials
            X_train_scaled: Pre-scaled features (CRITICAL for KNN - distance-based)
        """
        logger.info("Training KNN...")
        
        # Use pre-scaled features if available
        if X_train_scaled is not None:
            logger.info("  → Using PRE-SCALED features from dataset generator")
            X_scaled = X_train_scaled
            scaler = None
        else:
            logger.warning("  ⚠️  X_train_scaled not provided, scaling raw features now")
            scaler = StandardScaler()
            X_scaled = pd.DataFrame(
                scaler.fit_transform(X_train),
            columns=X_train.columns,
            index=X_train.index
        )
        
        def objective(trial):
            params = {
                'n_neighbors': trial.suggest_int('n_neighbors', 3, 20),
                'weights': trial.suggest_categorical('weights', ['uniform', 'distance']),
                'metric': trial.suggest_categorical('metric', ['minkowski', 'manhattan', 'euclidean']),
                'p': trial.suggest_int('p', 1, 2),
                'n_jobs': -1
            }
            
            model = KNeighborsClassifier(**params)
            score = cross_val_score(model, X_scaled, y_train, cv=self.skf, scoring='roc_auc_ovr').mean()
            return score
        
        study = optuna.create_study(direction='maximize', study_name='knn')
        study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
        
        best_params = study.best_params
        best_params['n_jobs'] = -1
        
        logger.info(f"Best KNN params: {best_params}")
        logger.info(f"Best CV AUC: {study.best_value:.4f}")
        
        oof_preds, fold_models = self._train_with_cv(
            X_scaled, y_train,
            model_class=KNeighborsClassifier,
            params=best_params
        )
        
        result = {
            'model_name': 'knn',
            'fold_models': fold_models,
            'oof_predictions': oof_preds,
            'oof_auc': self._calculate_auc(y_train, oof_preds),
            'best_params': best_params,
            'cv_auc': study.best_value,
            'scaler': scaler
        }
        
        # Evaluate on test set if provided
        if X_test is not None and y_test is not None:
            # Use pre-scaled test features if available
            if X_test_scaled is not None:
                X_test_eval = X_test_scaled
            else:
                # Scale test features with training scaler
                if scaler is not None:
                    X_test_eval = pd.DataFrame(
                        scaler.transform(X_test),
                        columns=X_test.columns,
                        index=X_test.index
                    )
                else:
                    logger.warning("No scaler available for test evaluation")
                    X_test_eval = X_test
            
            test_model = fold_models[0]
            test_proba = test_model.predict_proba(X_test_eval)[:, 1]
            test_auc = self._calculate_auc(y_test, test_proba)
            
            test_pred = (test_proba >= 0.5).astype(int)
            from sklearn.metrics import precision_score, recall_score, f1_score
            test_precision = precision_score(y_test, test_pred, average='weighted', zero_division=0)
            test_recall = recall_score(y_test, test_pred, average='weighted', zero_division=0)
            test_f1 = f1_score(y_test, test_pred, average='weighted', zero_division=0)
            
            result.update({
                'test_auc': test_auc,
                'test_precision': test_precision,
                'test_recall': test_recall,
                'test_f1': test_f1
            })
            
            logger.info(f"KNN Test AUC: {test_auc:.4f}, F1: {test_f1:.4f}")
        
        self.models['knn'] = result
        self.oof_predictions['knn'] = oof_preds
        
        logger.info(f"KNN OOF AUC: {result['oof_auc']:.4f}")
        
        return result
    
    def train_decision_tree(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        n_trials: int = 50,
        X_test: Optional[pd.DataFrame] = None,
        y_test: Optional[pd.Series] = None
    ) -> Dict:
        """Train Decision Tree with pruning"""
        logger.info("Training Decision Tree...")
        
        def objective(trial):
            params = {
                'max_depth': trial.suggest_int('max_depth', 3, 7),
                'min_samples_split': trial.suggest_int('min_samples_split', 2, 10),
                'min_samples_leaf': trial.suggest_int('min_samples_leaf', 3, 10),
                'criterion': trial.suggest_categorical('criterion', ['gini', 'entropy']),
                'class_weight': 'balanced',
                'random_state': self.random_state
            }
            
            model = DecisionTreeClassifier(**params)
            score = cross_val_score(model, X_train, y_train, cv=self.skf, scoring='roc_auc_ovr').mean()
            return score
        
        study = optuna.create_study(direction='maximize', study_name='decision_tree')
        study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
        
        best_params = study.best_params
        best_params.update({'class_weight': 'balanced', 'random_state': self.random_state})
        
        logger.info(f"Best Decision Tree params: {best_params}")
        logger.info(f"Best CV AUC: {study.best_value:.4f}")
        
        oof_preds, fold_models = self._train_with_cv(
            X_train, y_train,
            model_class=DecisionTreeClassifier,
            params=best_params
        )
        
        result = {
            'model_name': 'decision_tree',
            'fold_models': fold_models,
            'oof_predictions': oof_preds,
            'oof_auc': self._calculate_auc(y_train, oof_preds),
            'best_params': best_params,
            'cv_auc': study.best_value
        }
        
        # Evaluate on test set if provided
        if X_test is not None and y_test is not None:
            test_model = fold_models[0]
            test_proba = test_model.predict_proba(X_test)[:, 1]
            test_auc = self._calculate_auc(y_test, test_proba)
            
            test_pred = (test_proba >= 0.5).astype(int)
            from sklearn.metrics import precision_score, recall_score, f1_score
            test_precision = precision_score(y_test, test_pred, average='weighted', zero_division=0)
            test_recall = recall_score(y_test, test_pred, average='weighted', zero_division=0)
            test_f1 = f1_score(y_test, test_pred, average='weighted', zero_division=0)
            
            result.update({
                'test_auc': test_auc,
                'test_precision': test_precision,
                'test_recall': test_recall,
                'test_f1': test_f1
            })
            
            logger.info(f"Decision Tree Test AUC: {test_auc:.4f}, F1: {test_f1:.4f}")
        
        self.models['decision_tree'] = result
        self.oof_predictions['decision_tree'] = oof_preds
        
        logger.info(f"Decision Tree OOF AUC: {result['oof_auc']:.4f}")
        
        return result
    
    def train_logistic_regression(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        n_trials: int = 50,
        X_train_scaled: Optional[pd.DataFrame] = None,
        X_test: Optional[pd.DataFrame] = None,
        y_test: Optional[pd.Series] = None,
        X_test_scaled: Optional[pd.DataFrame] = None
    ) -> Dict:
        """
        Train Logistic Regression with scaled features
        
        Args:
            X_train: Raw features
            y_train: Target variable
            n_trials: Number of Optuna trials
            X_train_scaled: Pre-scaled features (recommended for LR)
            X_test, y_test: Optional test data
            X_test_scaled: Pre-scaled test features
        """
        logger.info("Training Logistic Regression...")
        
        # Use pre-scaled features if available
        if X_train_scaled is not None:
            logger.info("  → Using PRE-SCALED features from dataset generator")
            X_scaled = X_train_scaled
            scaler = None
        else:
            logger.warning("  ⚠️  X_train_scaled not provided, scaling raw features now")
            scaler = StandardScaler()
            X_scaled = pd.DataFrame(
                scaler.fit_transform(X_train),
                columns=X_train.columns,
                index=X_train.index
            )
        
        def objective(trial):
            params = {
                'C': trial.suggest_float('C', 0.01, 10, log=True),
                'penalty': trial.suggest_categorical('penalty', ['l1', 'l2']),
                'solver': 'saga',  # Supports both L1 and L2
                'max_iter': 1000,
                'class_weight': 'balanced',
                'random_state': self.random_state,
                'n_jobs': -1
            }
            
            model = LogisticRegression(**params)
            score = cross_val_score(model, X_scaled, y_train, cv=self.skf, scoring='roc_auc_ovr').mean()
            return score
        
        study = optuna.create_study(direction='maximize', study_name='logistic_regression')
        study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
        
        best_params = study.best_params
        best_params.update({
            'solver': 'saga',
            'max_iter': 1000,
            'class_weight': 'balanced',
            'random_state': self.random_state,
            'n_jobs': -1
        })
        
        logger.info(f"Best Logistic Regression params: {best_params}")
        logger.info(f"Best CV AUC: {study.best_value:.4f}")
        
        oof_preds, fold_models = self._train_with_cv(
            X_scaled, y_train,
            model_class=LogisticRegression,
            params=best_params
        )
        
        result = {
            'model_name': 'logistic_regression',
            'fold_models': fold_models,
            'oof_predictions': oof_preds,
            'oof_auc': self._calculate_auc(y_train, oof_preds),
            'best_params': best_params,
            'cv_auc': study.best_value,
            'scaler': scaler
        }
        
        # Evaluate on test set if provided
        if X_test is not None and y_test is not None:
            # Use pre-scaled test features if available
            if X_test_scaled is not None:
                X_test_eval = X_test_scaled
            else:
                # Scale test features with training scaler
                if scaler is not None:
                    X_test_eval = pd.DataFrame(
                        scaler.transform(X_test),
                        columns=X_test.columns,
                        index=X_test.index
                    )
                else:
                    logger.warning("No scaler available for test evaluation")
                    X_test_eval = X_test
            
            test_model = fold_models[0]
            test_proba = test_model.predict_proba(X_test_eval)[:, 1]
            test_auc = self._calculate_auc(y_test, test_proba)
            
            test_pred = (test_proba >= 0.5).astype(int)
            from sklearn.metrics import precision_score, recall_score, f1_score
            test_precision = precision_score(y_test, test_pred, average='weighted', zero_division=0)
            test_recall = recall_score(y_test, test_pred, average='weighted', zero_division=0)
            test_f1 = f1_score(y_test, test_pred, average='weighted', zero_division=0)
            
            result.update({
                'test_auc': test_auc,
                'test_precision': test_precision,
                'test_recall': test_recall,
                'test_f1': test_f1
            })
            
            logger.info(f"Logistic Regression Test AUC: {test_auc:.4f}, F1: {test_f1:.4f}")
        
        self.models['logistic_regression'] = result
        self.oof_predictions['logistic_regression'] = oof_preds
        
        logger.info(f"Logistic Regression OOF AUC: {result['oof_auc']:.4f}")
        
        return result
    
    def train_ridge_classifier(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: Optional[pd.DataFrame] = None,
        y_test: Optional[pd.Series] = None,
        X_train_scaled: Optional[pd.DataFrame] = None,
        X_test_scaled: Optional[pd.DataFrame] = None,
        n_trials: int = 100
    ) -> Dict:
        """
        Train Ridge Classifier with Optuna hyperparameter optimization
        Uses scaled features (LINEAR_MODEL)
        
        Ridge is similar to Logistic Regression but uses L2 regularization
        Good for multicollinearity and high-dimensional data
        """
        from sklearn.linear_model import RidgeClassifier
        from sklearn.metrics import roc_auc_score, make_scorer, precision_score, recall_score, f1_score, brier_score_loss
        
        logger.info("Training Ridge Classifier...")
        
        # Use scaled features if provided, otherwise scale here
        if X_train_scaled is not None:
            X_train_use = X_train_scaled
            scaler = None
        else:
            scaler = StandardScaler()
            X_train_use = pd.DataFrame(
                scaler.fit_transform(X_train),
                columns=X_train.columns,
                index=X_train.index
            )
        
        # Detect number of classes
        n_classes = len(np.unique(y_train))
        is_multiclass = n_classes > 2
        
        # Ridge Classifier doesn't support predict_proba, use accuracy instead
        scoring = 'accuracy'
        
        # Optuna objective
        def objective(trial):
            params = {
                'alpha': trial.suggest_float('alpha', 0.001, 100.0, log=True),
                'fit_intercept': trial.suggest_categorical('fit_intercept', [True, False]),
                'solver': trial.suggest_categorical('solver', ['auto', 'svd', 'cholesky', 'lsqr']),
                'random_state': self.random_state
            }
            
            model = RidgeClassifier(**params)
            
            # Cross-validation
            cv_scores = cross_val_score(
                model,
                X_train_use,
                y_train,
                cv=self.n_folds,
                scoring=scoring,
                n_jobs=-1
            )
            
            return cv_scores.mean()
        
        # Optimize
        study = optuna.create_study(direction='maximize', sampler=optuna.samplers.TPESampler(seed=self.random_state))
        study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
        
        best_params = study.best_params
        logger.info(f"Best Ridge params: {best_params}")
        
        # Train final model with best params - generate OOF predictions
        kf = StratifiedKFold(n_splits=self.n_folds, shuffle=True, random_state=self.random_state)
        
        if is_multiclass:
            oof_preds = np.zeros((len(y_train), n_classes))
        else:
            oof_preds = np.zeros(len(y_train))
        
        fold_models = []
        
        for fold, (train_idx, val_idx) in enumerate(kf.split(X_train_use, y_train)):
            X_tr, X_val = X_train_use.iloc[train_idx], X_train_use.iloc[val_idx]
            y_tr, y_val = y_train.iloc[train_idx], y_train.iloc[val_idx]
            
            model = RidgeClassifier(**best_params, random_state=self.random_state)
            model.fit(X_tr, y_tr)
            
            # Ridge returns decision function, not probabilities
            # We need to convert to probabilities for OOF
            if is_multiclass:
                decision = model.decision_function(X_val)
                # Softmax to convert to probabilities
                exp_scores = np.exp(decision - np.max(decision, axis=1, keepdims=True))
                val_proba = exp_scores / np.sum(exp_scores, axis=1, keepdims=True)
                oof_preds[val_idx] = val_proba
            else:
                decision = model.decision_function(X_val)
                # Sigmoid to convert to probabilities
                val_proba = 1 / (1 + np.exp(-decision))
                oof_preds[val_idx] = val_proba
            
            fold_models.append(model)
        
        result = {
            'model_name': 'ridge_classifier',
            'fold_models': fold_models,
            'oof_predictions': oof_preds,
            'oof_auc': self._calculate_auc(y_train, oof_preds),
            'best_params': best_params,
            'cv_auc': study.best_value,
            'scaler': scaler,
            'n_classes': n_classes
        }
        
        # Evaluate on test set if provided
        if X_test is not None and y_test is not None:
            if X_test_scaled is not None:
                X_test_eval = X_test_scaled
            else:
                if scaler is not None:
                    X_test_eval = pd.DataFrame(
                        scaler.transform(X_test),
                        columns=X_test.columns,
                        index=X_test.index
                    )
                else:
                    X_test_eval = X_test
            
            test_model = fold_models[0]
            if is_multiclass:
                decision = test_model.decision_function(X_test_eval)
                exp_scores = np.exp(decision - np.max(decision, axis=1, keepdims=True))
                test_proba = exp_scores / np.sum(exp_scores, axis=1, keepdims=True)
            else:
                decision = test_model.decision_function(X_test_eval)
                test_proba = 1 / (1 + np.exp(-decision))
            
            test_auc = self._calculate_auc(y_test, test_proba)
            
            test_pred = test_model.predict(X_test_eval)
            test_precision = precision_score(y_test, test_pred, average='macro', zero_division=0)
            test_recall = recall_score(y_test, test_pred, average='macro', zero_division=0)
            test_f1 = f1_score(y_test, test_pred, average='macro', zero_division=0)
            
            # Brier score
            if is_multiclass:
                # For multiclass, average Brier across classes
                test_brier = np.mean([brier_score_loss((y_test == i).astype(int), test_proba[:, i]) for i in range(n_classes)])
            else:
                test_brier = brier_score_loss(y_test, test_proba)
            
            result.update({
                'test_auc': test_auc,
                'test_precision': test_precision,
                'test_recall': test_recall,
                'test_f1': test_f1,
                'test_brier_score': test_brier
            })
            
            logger.info(f"Ridge Classifier Test AUC: {test_auc:.4f}, F1: {test_f1:.4f}")
        
        self.models['ridge_classifier'] = result
        self.oof_predictions['ridge_classifier'] = oof_preds
        
        logger.info(f"Ridge Classifier OOF AUC: {result['oof_auc']:.4f}")
        
        return result
    
    def train_linear_discriminant(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: Optional[pd.DataFrame] = None,
        y_test: Optional[pd.Series] = None,
        X_train_scaled: Optional[pd.DataFrame] = None,
        X_test_scaled: Optional[pd.DataFrame] = None,
        n_trials: int = 100
    ) -> Dict:
        """
        Train Linear Discriminant Analysis with Optuna hyperparameter optimization
        Uses scaled features (LINEAR_MODEL)
        
        LDA assumes Gaussian distributions and works well when classes are linearly separable
        Good for dimensionality reduction and classification
        """
        from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
        from sklearn.metrics import roc_auc_score, make_scorer, precision_score, recall_score, f1_score, brier_score_loss
        
        logger.info("Training Linear Discriminant Analysis...")
        
        # Use scaled features if provided, otherwise scale here
        if X_train_scaled is not None:
            X_train_use = X_train_scaled
            scaler = None
        else:
            scaler = StandardScaler()
            X_train_use = pd.DataFrame(
                scaler.fit_transform(X_train),
                columns=X_train.columns,
                index=X_train.index
            )
        
        # Detect number of classes
        n_classes = len(np.unique(y_train))
        is_multiclass = n_classes > 2
        
        # Choose scoring metric
        if is_multiclass:
            scoring = make_scorer(roc_auc_score, needs_proba=True, multi_class='ovr', average='macro')
        else:
            scoring = 'roc_auc'
        
        # Optuna objective
        def objective(trial):
            params = {
                'solver': trial.suggest_categorical('solver', ['svd', 'lsqr', 'eigen']),
                'shrinkage': None if trial.params['solver'] == 'svd' else trial.suggest_categorical('shrinkage', [None, 'auto']),
                'store_covariance': trial.suggest_categorical('store_covariance', [True, False])
            }
            
            # Remove None shrinkage if solver supports it
            if params['solver'] != 'svd' and params['shrinkage'] is None:
                params['shrinkage'] = 'auto'
            
            model = LinearDiscriminantAnalysis(**params)
            
            # Cross-validation
            cv_scores = cross_val_score(
                model,
                X_train_use,
                y_train,
                cv=self.n_folds,
                scoring=scoring,
                n_jobs=-1
            )
            
            return cv_scores.mean()
        
        # Optimize
        study = optuna.create_study(direction='maximize', sampler=optuna.samplers.TPESampler(seed=self.random_state))
        study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
        
        best_params = study.best_params
        logger.info(f"Best LDA params: {best_params}")
        
        # Train final model with best params - generate OOF predictions
        kf = StratifiedKFold(n_splits=self.n_folds, shuffle=True, random_state=self.random_state)
        
        if is_multiclass:
            oof_preds = np.zeros((len(y_train), n_classes))
        else:
            oof_preds = np.zeros(len(y_train))
        
        fold_models = []
        
        for fold, (train_idx, val_idx) in enumerate(kf.split(X_train_use, y_train)):
            X_tr, X_val = X_train_use.iloc[train_idx], X_train_use.iloc[val_idx]
            y_tr, y_val = y_train.iloc[train_idx], y_train.iloc[val_idx]
            
            model = LinearDiscriminantAnalysis(**best_params)
            model.fit(X_tr, y_tr)
            
            val_proba = model.predict_proba(X_val)
            
            if is_multiclass:
                oof_preds[val_idx] = val_proba
            else:
                oof_preds[val_idx] = val_proba[:, 1]
            
            fold_models.append(model)
        
        result = {
            'model_name': 'linear_discriminant',
            'fold_models': fold_models,
            'oof_predictions': oof_preds,
            'oof_auc': self._calculate_auc(y_train, oof_preds),
            'best_params': best_params,
            'cv_auc': study.best_value,
            'scaler': scaler,
            'n_classes': n_classes
        }
        
        # Evaluate on test set if provided
        if X_test is not None and y_test is not None:
            if X_test_scaled is not None:
                X_test_eval = X_test_scaled
            else:
                if scaler is not None:
                    X_test_eval = pd.DataFrame(
                        scaler.transform(X_test),
                        columns=X_test.columns,
                        index=X_test.index
                    )
                else:
                    X_test_eval = X_test
            
            test_model = fold_models[0]
            test_proba = test_model.predict_proba(X_test_eval)
            
            if is_multiclass:
                test_auc = self._calculate_auc(y_test, test_proba)
            else:
                test_auc = self._calculate_auc(y_test, test_proba[:, 1])
            
            test_pred = test_model.predict(X_test_eval)
            test_precision = precision_score(y_test, test_pred, average='macro', zero_division=0)
            test_recall = recall_score(y_test, test_pred, average='macro', zero_division=0)
            test_f1 = f1_score(y_test, test_pred, average='macro', zero_division=0)
            
            # Brier score
            if is_multiclass:
                test_brier = np.mean([brier_score_loss((y_test == i).astype(int), test_proba[:, i]) for i in range(n_classes)])
            else:
                test_brier = brier_score_loss(y_test, test_proba[:, 1])
            
            result.update({
                'test_auc': test_auc,
                'test_precision': test_precision,
                'test_recall': test_recall,
                'test_f1': test_f1,
                'test_brier_score': test_brier
            })
            
            logger.info(f"Linear Discriminant Test AUC: {test_auc:.4f}, F1: {test_f1:.4f}")
        
        self.models['linear_discriminant'] = result
        self.oof_predictions['linear_discriminant'] = oof_preds
        
        logger.info(f"Linear Discriminant OOF AUC: {result['oof_auc']:.4f}")
        
        return result
    
    def train_gradient_boosting(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: Optional[pd.DataFrame] = None,
        y_test: Optional[pd.Series] = None,
        n_trials: int = 100
    ) -> Dict:
        """
        Train Gradient Boosting Classifier with Optuna hyperparameter optimization
        Uses raw features (TREE_MODEL)
        
        Sklearn's GradientBoosting - classical gradient boosting implementation
        Slower than XGBoost/LightGBM but sometimes more stable
        """
        from sklearn.ensemble import GradientBoostingClassifier
        from sklearn.metrics import roc_auc_score, make_scorer, precision_score, recall_score, f1_score, brier_score_loss
        
        logger.info("Training Gradient Boosting...")
        
        # Detect number of classes
        n_classes = len(np.unique(y_train))
        is_multiclass = n_classes > 2
        
        # Choose scoring metric
        if is_multiclass:
            scoring = make_scorer(roc_auc_score, needs_proba=True, multi_class='ovr', average='macro')
        else:
            scoring = 'roc_auc'
        
        # Optuna objective
        def objective(trial):
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'max_depth': trial.suggest_int('max_depth', 3, 10),
                'min_samples_split': trial.suggest_int('min_samples_split', 2, 20),
                'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 10),
                'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                'max_features': trial.suggest_categorical('max_features', ['sqrt', 'log2', None]),
                'random_state': self.random_state
            }
            
            model = GradientBoostingClassifier(**params)
            
            # Cross-validation
            cv_scores = cross_val_score(
                model,
                X_train,
                y_train,
                cv=self.n_folds,
                scoring=scoring,
                n_jobs=-1
            )
            
            return cv_scores.mean()
        
        # Optimize
        study = optuna.create_study(direction='maximize', sampler=optuna.samplers.TPESampler(seed=self.random_state))
        study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
        
        best_params = study.best_params
        logger.info(f"Best Gradient Boosting params: {best_params}")
        
        # Train final model with best params - generate OOF predictions
        kf = StratifiedKFold(n_splits=self.n_folds, shuffle=True, random_state=self.random_state)
        
        if is_multiclass:
            oof_preds = np.zeros((len(y_train), n_classes))
        else:
            oof_preds = np.zeros(len(y_train))
        
        fold_models = []
        
        for fold, (train_idx, val_idx) in enumerate(kf.split(X_train, y_train)):
            X_tr, X_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
            y_tr, y_val = y_train.iloc[train_idx], y_train.iloc[val_idx]
            
            model = GradientBoostingClassifier(**best_params, random_state=self.random_state)
            model.fit(X_tr, y_tr)
            
            val_proba = model.predict_proba(X_val)
            
            if is_multiclass:
                oof_preds[val_idx] = val_proba
            else:
                oof_preds[val_idx] = val_proba[:, 1]
            
            fold_models.append(model)
        
        result = {
            'model_name': 'gradient_boosting',
            'fold_models': fold_models,
            'oof_predictions': oof_preds,
            'oof_auc': self._calculate_auc(y_train, oof_preds),
            'best_params': best_params,
            'cv_auc': study.best_value,
            'n_classes': n_classes
        }
        
        # Evaluate on test set if provided
        if X_test is not None and y_test is not None:
            test_model = fold_models[0]
            test_proba = test_model.predict_proba(X_test)
            
            if is_multiclass:
                test_auc = self._calculate_auc(y_test, test_proba)
            else:
                test_auc = self._calculate_auc(y_test, test_proba[:, 1])
            
            test_pred = test_model.predict(X_test)
            test_precision = precision_score(y_test, test_pred, average='macro', zero_division=0)
            test_recall = recall_score(y_test, test_pred, average='macro', zero_division=0)
            test_f1 = f1_score(y_test, test_pred, average='macro', zero_division=0)
            
            # Brier score
            if is_multiclass:
                test_brier = np.mean([brier_score_loss((y_test == i).astype(int), test_proba[:, i]) for i in range(n_classes)])
            else:
                test_brier = brier_score_loss(y_test, test_proba[:, 1])
            
            result.update({
                'test_auc': test_auc,
                'test_precision': test_precision,
                'test_recall': test_recall,
                'test_f1': test_f1,
                'test_brier_score': test_brier
            })
            
            logger.info(f"Gradient Boosting Test AUC: {test_auc:.4f}, F1: {test_f1:.4f}")
        
        self.models['gradient_boosting'] = result
        self.oof_predictions['gradient_boosting'] = oof_preds
        
        logger.info(f"Gradient Boosting OOF AUC: {result['oof_auc']:.4f}")
        
        return result
