"""
Model Evaluation (Layer 8)
Comprehensive evaluation metrics and visualizations
"""
import pandas as pd
import numpy as np
from sklearn.metrics import (
    roc_auc_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_curve,
    precision_recall_curve, brier_score_loss
)
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional
import logging
from pathlib import Path
import io

# SHAP for model interpretability
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logging.warning("SHAP not available - interpretability features disabled")

logger = logging.getLogger(__name__)


class ModelEvaluator:
    """
    Comprehensive model evaluation with metrics and visualizations
    """
    
    def __init__(self):
        """Initialize evaluator"""
        self.metrics = {}
        
    def evaluate_model(
        self,
        y_true: pd.Series,
        y_pred_proba: np.ndarray,
        model_name: str,
        threshold: float = 0.5
    ) -> Dict:
        """
        Evaluate a single model on test set
        
        Args:
            y_true: True labels
            y_pred_proba: Predicted probabilities
            model_name: Name of model
            threshold: Classification threshold
            
        Returns:
            Dictionary of evaluation metrics
        """
        logger.info(f"Evaluating {model_name}...")
        
        # Convert probabilities to binary predictions
        y_pred = (y_pred_proba >= threshold).astype(int)
        
        # Calculate metrics
        metrics = {
            'model_name': model_name,
            'auc_roc': roc_auc_score(y_true, y_pred_proba),
            'precision': precision_score(y_true, y_pred, zero_division=0),
            'recall': recall_score(y_true, y_pred, zero_division=0),
            'f1_score': f1_score(y_true, y_pred, zero_division=0),
            'brier_score': brier_score_loss(y_true, y_pred_proba),
            'threshold': threshold
        }
        
        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        if cm.shape == (2, 2):
            tn, fp, fn, tp = cm.ravel()
            metrics.update({
                'true_negatives': int(tn),
                'false_positives': int(fp),
                'false_negatives': int(fn),
                'true_positives': int(tp),
                'specificity': tn / (tn + fp) if (tn + fp) > 0 else 0.0
            })
        
        self.metrics[model_name] = metrics
        
        logger.info(f"{model_name} - AUC: {metrics['auc_roc']:.4f}, "
                   f"F1: {metrics['f1_score']:.4f}, "
                   f"Precision: {metrics['precision']:.4f}, "
                   f"Recall: {metrics['recall']:.4f}")
        
        return metrics
    
    def compare_models(
        self,
        results: Dict[str, Dict]
    ) -> pd.DataFrame:
        """
        Create comparison table of all models with Brier score prominence
        
        Args:
            results: Dictionary mapping model_name -> evaluation metrics
            
        Returns:
            DataFrame with model comparison
        """
        comparison_df = pd.DataFrame(results).T
        
        # Sort by AUC-ROC
        comparison_df = comparison_df.sort_values('auc_roc', ascending=False)
        
        # Add calibration warning flag (Brier score > 0.25 indicates poor calibration)
        if 'brier_score' in comparison_df.columns:
            comparison_df['calibration_warning'] = comparison_df['brier_score'] > 0.25
        
        logger.info("\n" + "="*80)
        logger.info("MODEL COMPARISON")
        logger.info("="*80)
        
        # Display key metrics INCLUDING Brier score for calibration assessment
        display_cols = ['auc_roc', 'f1_score', 'precision', 'recall']
        if 'brier_score' in comparison_df.columns:
            display_cols.append('brier_score')
        if 'calibration_warning' in comparison_df.columns:
            display_cols.append('calibration_warning')
        
        logger.info(comparison_df[display_cols].to_string())
        
        # Highlight calibration issues
        if 'calibration_warning' in comparison_df.columns:
            poorly_calibrated = comparison_df[comparison_df['calibration_warning']]
            if not poorly_calibrated.empty:
                logger.warning("\n⚠️  CALIBRATION WARNING:")
                logger.warning(f"Models with Brier score > 0.25 (poorly calibrated):")
                for model_name in poorly_calibrated.index:
                    brier = poorly_calibrated.loc[model_name, 'brier_score']
                    logger.warning(f"  - {model_name}: Brier = {brier:.4f}")
                logger.warning("Consider probability calibration (Platt scaling, isotonic regression)")
        
        logger.info("="*80)
        
        return comparison_df
    
    def plot_roc_curves(
        self,
        y_true: pd.Series,
        predictions: Dict[str, np.ndarray],
        save_path: Optional[Path] = None
    ) -> plt.Figure:
        """
        Plot ROC curves for multiple models
        
        Args:
            y_true: True labels
            predictions: Dictionary mapping model_name -> predicted probabilities
            save_path: Path to save plot
            
        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=(10, 8))
        
        for model_name, y_pred_proba in predictions.items():
            fpr, tpr, _ = roc_curve(y_true, y_pred_proba)
            auc = roc_auc_score(y_true, y_pred_proba)
            ax.plot(fpr, tpr, label=f'{model_name} (AUC={auc:.3f})')
        
        # Plot diagonal
        ax.plot([0, 1], [0, 1], 'k--', label='Random (AUC=0.500)')
        
        ax.set_xlabel('False Positive Rate')
        ax.set_ylabel('True Positive Rate')
        ax.set_title('ROC Curves - Model Comparison')
        ax.legend(loc='lower right')
        ax.grid(alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"ROC curve saved to {save_path}")
        
        return fig
    
    def plot_precision_recall_curves(
        self,
        y_true: pd.Series,
        predictions: Dict[str, np.ndarray],
        save_path: Optional[Path] = None
    ) -> plt.Figure:
        """Plot Precision-Recall curves"""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        for model_name, y_pred_proba in predictions.items():
            precision, recall, _ = precision_recall_curve(y_true, y_pred_proba)
            ax.plot(recall, precision, label=model_name)
        
        ax.set_xlabel('Recall')
        ax.set_ylabel('Precision')
        ax.set_title('Precision-Recall Curves - Model Comparison')
        ax.legend()
        ax.grid(alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"PR curve saved to {save_path}")
        
        return fig
    
    def plot_confusion_matrix(
        self,
        y_true: pd.Series,
        y_pred: np.ndarray,
        model_name: str,
        save_path: Optional[Path] = None
    ) -> plt.Figure:
        """Plot confusion matrix heatmap"""
        cm = confusion_matrix(y_true, y_pred)
        
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax)
        ax.set_xlabel('Predicted')
        ax.set_ylabel('Actual')
        ax.set_title(f'Confusion Matrix - {model_name}')
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig
    
    def calculate_calibration_metrics(
        self,
        y_true: pd.Series,
        y_pred_proba: np.ndarray,
        n_bins: int = 10
    ) -> Dict:
        """
        Calculate calibration metrics (reliability diagram data)
        
        Returns:
            Dictionary with bin information for calibration plot
        """
        from sklearn.calibration import calibration_curve
        
        prob_true, prob_pred = calibration_curve(
            y_true, y_pred_proba,
            n_bins=n_bins,
            strategy='uniform'
        )
        
        return {
            'prob_true': prob_true.tolist(),
            'prob_pred': prob_pred.tolist(),
            'brier_score': brier_score_loss(y_true, y_pred_proba)
        }
    
    def generate_evaluation_report(
        self,
        y_test: pd.Series,
        test_predictions: Dict[str, np.ndarray],
        output_dir: Path
    ) -> Dict:
        """
        Generate comprehensive evaluation report with all metrics and plots
        
        Args:
            y_test: Test labels
            test_predictions: Dictionary of model predictions
            output_dir: Directory to save output files
            
        Returns:
            Complete evaluation report
        """
        logger.info("Generating comprehensive evaluation report...")
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Evaluate all models
        all_metrics = {}
        for model_name, y_pred_proba in test_predictions.items():
            metrics = self.evaluate_model(y_test, y_pred_proba, model_name)
            all_metrics[model_name] = metrics
        
        # Model comparison table
        comparison_df = self.compare_models(all_metrics)
        comparison_df.to_csv(output_dir / 'model_comparison.csv')
        
        # Plot ROC curves
        self.plot_roc_curves(y_test, test_predictions, output_dir / 'roc_curves.png')
        
        # Plot PR curves
        self.plot_precision_recall_curves(y_test, test_predictions, output_dir / 'pr_curves.png')
        
        # Close all figures to free memory
        plt.close('all')
        
        return {
            'metrics': all_metrics,
            'comparison_table': comparison_df.to_dict(),
            'output_directory': str(output_dir)
        }
    
    def generate_shap_explanations(
        self,
        model: any,
        X_train: pd.DataFrame,
        X_test: pd.DataFrame,
        model_name: str,
        output_dir: Optional[Path] = None,
        max_display: int = 20
    ) -> Dict:
        """
        Generate SHAP explanations for model interpretability
        
        Args:
            model: Trained model
            X_train: Training data (background for SHAP)
            X_test: Test data to explain
            model_name: Name of the model
            output_dir: Directory to save plots
            max_display: Maximum features to show in plots
        
        Returns:
            Dictionary with SHAP values and plot paths
        """
        if not SHAP_AVAILABLE:
            logger.warning("SHAP not installed - skipping explanations")
            return {'error': 'SHAP not available'}
        
        logger.info(f"Generating SHAP explanations for {model_name}...")
        
        try:
            # Choose appropriate explainer based on model type
            if model_name in ['xgboost', 'lightgbm', 'catboost', 
                             'random_forest', 'decision_tree']:
                # TreeExplainer for tree-based models (much faster)
                explainer = shap.TreeExplainer(model)
                shap_values = explainer.shap_values(X_test)
                
                # For binary classification, take positive class
                if isinstance(shap_values, list):
                    shap_values = shap_values[1]
            else:
                # KernelExplainer or LinearExplainer for other models
                # Use subset of training data as background
                background = shap.sample(X_train, min(100, len(X_train)))
                explainer = shap.KernelExplainer(model.predict_proba, background)
                shap_values = explainer.shap_values(X_test)
                
                if isinstance(shap_values, list):
                    shap_values = shap_values[1]
            
            # Generate SHAP summary plot (bee swarm)
            fig_summary = plt.figure(figsize=(12, 8))
            shap.summary_plot(
                shap_values, X_test,
                max_display=max_display,
                show=False
            )
            plt.title(f'SHAP Feature Importance - {model_name}')
            plt.tight_layout()
            
            summary_path = None
            if output_dir:
                output_dir = Path(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                summary_path = output_dir / f'{model_name}_shap_summary.png'
                fig_summary.savefig(summary_path, dpi=300, bbox_inches='tight')
                logger.info(f"SHAP summary plot saved to {summary_path}")
            
            plt.close(fig_summary)
            
            # Generate SHAP bar plot (mean absolute SHAP values)
            fig_bar = plt.figure(figsize=(10, 8))
            shap.summary_plot(
                shap_values, X_test,
                plot_type='bar',
                max_display=max_display,
                show=False
            )
            plt.title(f'SHAP Feature Importance (Bar) - {model_name}')
            plt.tight_layout()
            
            bar_path = None
            if output_dir:
                bar_path = output_dir / f'{model_name}_shap_bar.png'
                fig_bar.savefig(bar_path, dpi=300, bbox_inches='tight')
                logger.info(f"SHAP bar plot saved to {bar_path}")
            
            plt.close(fig_bar)
            
            # Calculate feature importance from SHAP values
            feature_importance = pd.DataFrame({
                'feature': X_test.columns,
                'mean_abs_shap': np.abs(shap_values).mean(axis=0)
            }).sort_values('mean_abs_shap', ascending=False)
            
            if output_dir:
                importance_path = output_dir / f'{model_name}_shap_importance.csv'
                feature_importance.to_csv(importance_path, index=False)
            
            return {
                'shap_values': shap_values.tolist() if isinstance(shap_values, np.ndarray) else shap_values,
                'feature_importance': feature_importance.to_dict('records'),
                'summary_plot': str(summary_path) if summary_path else None,
                'bar_plot': str(bar_path) if bar_path else None,
                'top_features': feature_importance.head(10)['feature'].tolist()
            }
        
        except Exception as e:
            logger.error(f"Error generating SHAP explanations: {e}")
            return {'error': str(e)}
    
    def plot_feature_importance(
        self,
        model: any,
        feature_names: List[str],
        model_name: str,
        top_k: int = 20,
        save_path: Optional[Path] = None
    ) -> plt.Figure:
        """
        Plot feature importance from tree-based models
        
        Args:
            model: Trained tree-based model (XGBoost, LightGBM, etc.)
            feature_names: List of feature names
            model_name: Name of the model
            top_k: Number of top features to display
            save_path: Path to save plot
        
        Returns:
            Matplotlib figure
        """
        try:
            # Extract feature importance
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
            elif hasattr(model, 'get_score'):
                # XGBoost
                importance_dict = model.get_score(importance_type='gain')
                importances = [importance_dict.get(f, 0) for f in feature_names]
            else:
                logger.warning(f"Model {model_name} does not have feature_importances_")
                return None
            
            # Create DataFrame
            importance_df = pd.DataFrame({
                'feature': feature_names,
                'importance': importances
            }).sort_values('importance', ascending=False).head(top_k)
            
            # Plot
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.barh(range(len(importance_df)), importance_df['importance'])
            ax.set_yticks(range(len(importance_df)))
            ax.set_yticklabels(importance_df['feature'])
            ax.set_xlabel('Feature Importance')
            ax.set_title(f'Top {top_k} Features - {model_name}')
            ax.invert_yaxis()
            ax.grid(alpha=0.3, axis='x')
            
            plt.tight_layout()
            
            if save_path:
                fig.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"Feature importance plot saved to {save_path}")
            
            return fig
        
        except Exception as e:
            logger.error(f"Error plotting feature importance: {e}")
            return None
    
    def plot_calibration_curve(
        self,
        y_true: pd.Series,
        predictions: Dict[str, np.ndarray],
        n_bins: int = 10,
        save_path: Optional[Path] = None
    ) -> plt.Figure:
        """
        Plot calibration curves (reliability diagrams) for multiple models
        
        Args:
            y_true: True labels
            predictions: Dictionary of model predictions
            n_bins: Number of bins for calibration
            save_path: Path to save plot
        
        Returns:
            Matplotlib figure
        """
        from sklearn.calibration import calibration_curve
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        for model_name, y_pred_proba in predictions.items():
            prob_true, prob_pred = calibration_curve(
                y_true, y_pred_proba,
                n_bins=n_bins,
                strategy='uniform'
            )
            
            brier = brier_score_loss(y_true, y_pred_proba)
            ax.plot(prob_pred, prob_true,
                   marker='o',
                   label=f'{model_name} (Brier={brier:.3f})')
        
        # Plot perfect calibration line
        ax.plot([0, 1], [0, 1], 'k--', label='Perfectly Calibrated')
        
        ax.set_xlabel('Mean Predicted Probability')
        ax.set_ylabel('Fraction of Positives')
        ax.set_title('Calibration Curves (Reliability Diagrams)')
        ax.legend()
        ax.grid(alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Calibration curve saved to {save_path}")
        
        return fig
