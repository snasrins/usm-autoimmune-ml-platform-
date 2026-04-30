"""
LASSO Feature Selection (Layer 6)
Select most important features using LassoCV
"""
import pandas as pd
import numpy as np
from sklearn.linear_model import LassoCV
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class LassoFeatureSelector:
    """
    Feature selection using LASSO (L1 regularization)
    Reduces feature set from ~100 to 30-50 most important features
    """
    
    def __init__(self, alphas: List[float] = None, cv: int = 5):
        """
        Args:
            alphas: Alpha values to try (regularization strength)
            cv: Number of cross-validation folds
        """
        if alphas is None:
            alphas = [0.0001, 0.001, 0.01, 0.1, 1.0]
        
        self.alphas = alphas
        self.cv = cv
        self.scaler = StandardScaler()
        self.lasso_model = LassoCV(alphas=alphas, cv=cv, random_state=42, max_iter=10000)
        self.selected_features = None
        self.feature_importance = None
        
    def fit(self, X: pd.DataFrame, y: pd.Series) -> 'LassoFeatureSelector':
        """
        Fit LASSO model and select features
        
        Args:
            X: Feature matrix
            y: Target vector
            
        Returns:
            self
        """
        logger.info(f"Starting LASSO feature selection from {X.shape[1]} features...")
        
        # Scale features (required for LASSO)
        X_scaled = self.scaler.fit_transform(X)
        
        # Fit LASSO
        self.lasso_model.fit(X_scaled, y)
        
        # Extract feature importance (absolute coefficients)
        coefficients = np.abs(self.lasso_model.coef_)
        
        # Select features with non-zero coefficients
        selected_mask = coefficients > 0
        self.selected_features = X.columns[selected_mask].tolist()
        
        # Create feature importance dataframe
        self.feature_importance = pd.DataFrame({
            'feature': X.columns,
            'coefficient': self.lasso_model.coef_,
            'abs_coefficient': coefficients,
            'selected': selected_mask
        }).sort_values('abs_coefficient', ascending=False)
        
        logger.info(f"LASSO selected {len(self.selected_features)} features (alpha={self.lasso_model.alpha_:.4f})")
        logger.info(f"Top 10 features: {self.selected_features[:10]}")
        
        return self
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Transform dataset to include only selected features
        
        Args:
            X: Feature matrix
            
        Returns:
            Reduced feature matrix
        """
        if self.selected_features is None:
            raise ValueError("Must call fit() before transform()")
        
        return X[self.selected_features]
    
    def fit_transform(self, X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
        """Fit and transform in one step"""
        return self.fit(X, y).transform(X)
    
    def get_feature_importance_report(self) -> Dict:
        """
        Generate feature importance report for clinical review
        
        Returns:
            Dictionary with feature importance statistics
        """
        if self.feature_importance is None:
            raise ValueError("Must call fit() first")
        
        report = {
            "total_features": len(self.feature_importance),
            "selected_features": len(self.selected_features),
            "reduction_ratio": 1 - (len(self.selected_features) / len(self.feature_importance)),
            "optimal_alpha": self.lasso_model.alpha_,
            "top_10_features": self.feature_importance.head(10).to_dict('records'),
            "selected_feature_list": self.selected_features
        }
        
        return report
