"""
Scorecard Generator with Feature-Level Bin Scoring
Implements research-aligned white-box clinical decision support

Based on research framework:
- Feature binning criteria and scoring system based on target variable distribution
- Combine global weights with local probabilities to calculate feature scores
- Use Youden Index to find optimal risk threshold
- Transparent, interpretable scoring system
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from sklearn.metrics import roc_curve, confusion_matrix
import logging

from .dynamic_binning import DynamicBinning, BinningMethod

logger = logging.getLogger(__name__)


class ScorecardGenerator:
    """
    Generate white-box clinical scorecards with transparent bin-based scoring
    
    Key features:
    1. Dynamic binning of continuous features
    2. Feature-level bin scoring (each bin gets a point value)
    3. Multiplicative scoring (global weights × local probabilities)
    4. Youden Index threshold optimization
    5. Risk stratification with transparent rules
    """
    
    def __init__(
        self,
        binning_method: Union[BinningMethod, str] = BinningMethod.ROLLING_MEAN,
        n_bins: int = 4,
        min_bin_size: int = 5,
        base_points: int = 100,
        use_youden: bool = True
    ):
        """
        Initialize scorecard generator
        
        Args:
            binning_method: Method for creating feature bins
            n_bins: Target number of bins per feature
            min_bin_size: Minimum samples per bin
            base_points: Base score for scaling (default: 100)
            use_youden: Use Youden Index for optimal threshold
        """
        if isinstance(binning_method, str):
            binning_method = BinningMethod(binning_method)
        
        self.binning_method = binning_method
        self.n_bins = n_bins
        self.min_bin_size = min_bin_size
        self.base_points = base_points
        self.use_youden = use_youden
        
        self.binning_ = None
        self.bin_scores_: Dict[str, Dict[int, float]] = {}
        self.feature_weights_: Dict[str, float] = {}
        self.optimal_threshold_: Optional[float] = None
        self.threshold_metrics_: Optional[Dict] = None
        self.score_stats_: Optional[Dict] = None
    
    def fit(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        model,
        feature_names: List[str]
    ) -> 'ScorecardGenerator':
        """
        Fit scorecard on training data
        
        Args:
            X_train: Training features
            y_train: Training target
            model: Trained ML model
            feature_names: List of features to include in scorecard
        
        Returns:
            self
        """
        logger.info("Fitting scorecard generator...")
        
        # Filter to specified features
        X_train_filtered = X_train[feature_names].copy()
        
        # Step 1: Fit dynamic binning
        logger.info(f"Step 1: Fitting {self.binning_method.value} binning...")
        self.binning_ = DynamicBinning(
            method=self.binning_method,
            n_bins=self.n_bins,
            min_bin_size=self.min_bin_size
        )
        self.binning_.fit(X_train_filtered, y_train, features=feature_names)
        
        # Step 2: Transform features to bins
        logger.info("Step 2: Transforming features to bins...")
        X_binned, X_bin_indices = self.binning_.transform(X_train_filtered, return_bins=True)
        
        # Step 3: Calculate feature weights from model
        logger.info("Step 3: Calculating feature weights from model...")
        self.feature_weights_ = self._extract_feature_weights(
            model, feature_names, X_train_filtered, y_train
        )
        
        # Step 4: Calculate bin scores for each feature
        logger.info("Step 4: Calculating bin scores...")
        self.bin_scores_ = self._calculate_bin_scores(
            X_train_filtered, y_train, X_bin_indices, feature_names
        )
        
        # Step 5: Calculate total scores for training set
        logger.info("Step 5: Calculating training set scores...")
        train_scores = self.score(X_train_filtered)
        
        # Step 6: Find optimal threshold using Youden Index
        if self.use_youden:
            logger.info("Step 6: Optimizing threshold with Youden Index...")
            self.optimal_threshold_ = self._optimize_threshold_youden(
                train_scores, y_train
            )
        else:
            # Use median as threshold
            self.optimal_threshold_ = float(np.median(train_scores))
        
        # Step 7: Calculate score statistics
        self.score_stats_ = self._calculate_score_stats(
            train_scores, y_train, self.optimal_threshold_
        )
        
        logger.info(f"Scorecard fitted. Optimal threshold: {self.optimal_threshold_:.2f}")
        
        return self
    
    def score(
        self,
        X: pd.DataFrame,
        return_breakdown: bool = False
    ) -> Union[np.ndarray, Tuple[np.ndarray, pd.DataFrame]]:
        """
        Calculate total scores for samples
        
        Args:
            X: Feature dataframe
            return_breakdown: If True, return feature-level score breakdown
        
        Returns:
            Total scores (and optionally score breakdown per feature)
        """
        if self.binning_ is None:
            raise ValueError("Scorecard not fitted. Call fit() first.")
        
        # Get bin indices for features
        _, X_bin_indices = self.binning_.transform(X, return_bins=True)
        
        # Calculate scores for each feature
        total_scores = np.zeros(len(X))
        breakdown = pd.DataFrame(index=X.index)
        
        for feature in X_bin_indices.columns:
            if feature not in self.bin_scores_:
                continue
            
            bin_indices = X_bin_indices[feature].values
            feature_scores = np.array([
                self.bin_scores_[feature].get(int(idx), 0.0)
                for idx in bin_indices
            ])
            
            total_scores += feature_scores
            breakdown[f"{feature}_score"] = feature_scores
        
        if return_breakdown:
            breakdown['total_score'] = total_scores
            return total_scores, breakdown
        else:
            return total_scores
    
    def predict_risk_group(
        self,
        X: pd.DataFrame,
        threshold: Optional[float] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict risk groups based on scores
        
        Args:
            X: Feature dataframe
            threshold: Score threshold (default: use optimal threshold from training)
        
        Returns:
            Tuple of (risk_groups, scores)
            risk_groups: 0 = Low risk, 1 = High risk
            scores: Total risk scores
        """
        if threshold is None:
            if self.optimal_threshold_ is None:
                raise ValueError("No threshold specified and no optimal threshold fitted")
            threshold = self.optimal_threshold_
        
        scores = self.score(X)
        risk_groups = (scores >= threshold).astype(int)
        
        return risk_groups, scores
    
    def get_scorecard_table(
        self,
        feature: str
    ) -> Optional[pd.DataFrame]:
        """
        Get transparent scorecard table for a feature
        
        Returns DataFrame with:
        - Bin label (e.g., "≤ 1.10", "1.10-5.00")
        - Score (points for that bin)
        - Sample count
        - Target distribution
        
        This is the white-box table that clinicians can use manually
        """
        if feature not in self.bin_scores_:
            return None
        
        bin_labels = self.binning_.get_bin_labels(feature)
        bin_stats = self.binning_.get_bin_stats(feature)
        bin_scores = self.bin_scores_[feature]
        
        table_data = []
        
        for i, label in enumerate(bin_labels):
            row = {
                'Feature': feature,
                'Bin': label,
                'Score': bin_scores.get(i, 0.0),
                'Count': bin_stats['bins'][i]['count'],
                'Percentage': bin_stats['bins'][i]['percentage']
            }
            
            # Add target distribution if available
            if 'target_distribution' in bin_stats['bins'][i]:
                target_dist = bin_stats['bins'][i]['target_distribution']
                for class_name, prob in target_dist.items():
                    row[f'P({class_name})'] = prob
            elif 'target_mean' in bin_stats['bins'][i]:
                row['Target_Mean'] = bin_stats['bins'][i]['target_mean']
            
            table_data.append(row)
        
        return pd.DataFrame(table_data)
    
    def get_all_scorecard_tables(self) -> pd.DataFrame:
        """Get combined scorecard table for all features"""
        all_tables = []
        
        for feature in self.bin_scores_.keys():
            table = self.get_scorecard_table(feature)
            if table is not None:
                all_tables.append(table)
        
        if all_tables:
            return pd.concat(all_tables, ignore_index=True)
        else:
            return pd.DataFrame()
    
    def get_risk_stratification_performance(
        self,
        X_test: pd.DataFrame,
        y_test: pd.Series
    ) -> Dict:
        """
        Calculate risk stratification performance on test set
        
        Returns metrics like:
        - Score range for low/high risk groups
        - Sample count per group
        - Accuracy, sensitivity, specificity per group
        - High risk ratio
        """
        risk_groups, scores = self.predict_risk_group(X_test)
        
        # Convert target to binary if multi-class
        if y_test.nunique() > 2:
            # For SLE: Mild=0, Moderate=1, Severe=2
            # Consider Moderate+Severe as high risk
            y_binary = (y_test >= 1).astype(int)
        else:
            y_binary = y_test.astype(int)
        
        # Separate low and high risk groups
        low_risk_mask = risk_groups == 0
        high_risk_mask = risk_groups == 1
        
        low_risk_scores = scores[low_risk_mask]
        high_risk_scores = scores[high_risk_mask]
        
        # Calculate confusion matrix
        cm = confusion_matrix(y_binary, risk_groups)
        tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)
        
        # Calculate metrics
        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        ppv = tp / (tp + fp) if (tp + fp) > 0 else 0
        npv = tn / (tn + fn) if (tn + fn) > 0 else 0
        accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
        
        result = {
            'threshold': self.optimal_threshold_,
            'total_samples': len(X_test),
            
            'low_risk': {
                'count': int(low_risk_mask.sum()),
                'percentage': float(low_risk_mask.sum() / len(X_test) * 100),
                'score_range': {
                    'min': float(low_risk_scores.min()) if len(low_risk_scores) > 0 else None,
                    'max': float(low_risk_scores.max()) if len(low_risk_scores) > 0 else None,
                    'mean': float(low_risk_scores.mean()) if len(low_risk_scores) > 0 else None
                }
            },
            
            'high_risk': {
                'count': int(high_risk_mask.sum()),
                'percentage': float(high_risk_mask.sum() / len(X_test) * 100),
                'score_range': {
                    'min': float(high_risk_scores.min()) if len(high_risk_scores) > 0 else None,
                    'max': float(high_risk_scores.max()) if len(high_risk_scores) > 0 else None,
                    'mean': float(high_risk_scores.mean()) if len(high_risk_scores) > 0 else None
                },
                'ratio': float(high_risk_mask.sum() / len(X_test))
            },
            
            'performance': {
                'accuracy': float(accuracy),
                'sensitivity': float(sensitivity),
                'specificity': float(specificity),
                'ppv': float(ppv),
                'npv': float(npv),
                'confusion_matrix': {
                    'tn': int(tn),
                    'fp': int(fp),
                    'fn': int(fn),
                    'tp': int(tp)
                }
            }
        }
        
        return result
    
    def _extract_feature_weights(
        self,
        model,
        feature_names: List[str],
        X: pd.DataFrame,
        y: pd.Series
    ) -> Dict[str, float]:
        """
        Extract feature importance weights from model
        
        Uses:
        - feature_importances_ for tree-based models
        - coef_ for linear models
        - Permutation importance as fallback
        """
        weights = {}
        
        if hasattr(model, 'feature_importances_'):
            # Tree-based models
            importances = model.feature_importances_
            
            for feat, imp in zip(feature_names, importances):
                weights[feat] = float(imp)
        
        elif hasattr(model, 'coef_'):
            # Linear models
            coefficients = model.coef_
            
            # Handle multi-class
            if len(coefficients.shape) > 1:
                # Use average absolute coefficient across classes
                coef = np.mean(np.abs(coefficients), axis=0)
            else:
                coef = np.abs(coefficients)
            
            for feat, c in zip(feature_names, coef):
                weights[feat] = float(c)
        
        else:
            # Fallback: use variance as importance
            logger.warning("Model does not have feature_importances_ or coef_, using variance")
            for feat in feature_names:
                weights[feat] = float(X[feat].var())
        
        # Normalize weights to sum to 1
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}
        
        return weights
    
    def _calculate_bin_scores(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        X_bin_indices: pd.DataFrame,
        feature_names: List[str]
    ) -> Dict[str, Dict[int, float]]:
        """
        Calculate point scores for each bin of each feature
        
        Methodology:
        1. For each feature and bin, calculate target distribution
        2. Weight by feature importance
        3. Scale to base_points (e.g., 100)
        
        Result: bin_scores[feature][bin_index] = points
        """
        bin_scores = {}
        
        # Convert target to numeric if needed
        if y.dtype == 'object' or y.dtype.name == 'category':
            y_numeric = pd.Categorical(y).codes
            n_classes = y.nunique()
        else:
            y_numeric = y
            n_classes = y.nunique()
        
        for feature in feature_names:
            if feature not in X_bin_indices.columns:
                continue
            
            bin_indices = X_bin_indices[feature]
            n_bins = bin_indices.nunique()
            
            feature_weight = self.feature_weights_.get(feature, 1.0 / len(feature_names))
            
            bin_scores[feature] = {}
            
            for bin_idx in range(n_bins):
                mask = bin_indices == bin_idx
                
                if mask.sum() == 0:
                    bin_scores[feature][bin_idx] = 0.0
                    continue
                
                # Get target values for this bin
                bin_target = y_numeric[mask]
                
                if n_classes == 2:
                    # Binary: score = probability of positive class
                    prob_positive = (bin_target == 1).mean()
                    raw_score = prob_positive
                
                else:
                    # Multi-class: score = weighted average of class indices
                    # Higher class index = higher severity = higher score
                    raw_score = bin_target.mean() / (n_classes - 1)
                
                # Apply feature weight and scale to base points
                score = raw_score * feature_weight * self.base_points
                
                bin_scores[feature][bin_idx] = float(score)
        
        return bin_scores
    
    def _optimize_threshold_youden(
        self,
        scores: np.ndarray,
        y_true: pd.Series
    ) -> float:
        """
        Find optimal score threshold using Youden Index
        
        Youden's J = Sensitivity + Specificity - 1
        
        Maximizes the balance between detecting true positives
        and avoiding false positives
        """
        # Convert target to binary if multi-class
        if y_true.nunique() > 2:
            # For SLE: Moderate+Severe = high risk (1)
            y_binary = (y_true >= 1).astype(int).values
        else:
            y_binary = y_true.astype(int).values
        
        # Calculate ROC curve
        fpr, tpr, thresholds = roc_curve(y_binary, scores)
        
        # Calculate Youden's J for each threshold
        youden_j = tpr - fpr
        
        # Find threshold that maximizes J
        optimal_idx = np.argmax(youden_j)
        optimal_threshold = float(thresholds[optimal_idx])
        
        # Store metrics
        self.threshold_metrics_ = {
            'youden_j': float(youden_j[optimal_idx]),
            'sensitivity': float(tpr[optimal_idx]),
            'specificity': float(1 - fpr[optimal_idx]),
            'threshold': optimal_threshold
        }
        
        logger.info(
            f"Youden optimal threshold: {optimal_threshold:.2f} "
            f"(J={youden_j[optimal_idx]:.3f}, "
            f"Sens={tpr[optimal_idx]:.3f}, "
            f"Spec={1-fpr[optimal_idx]:.3f})"
        )
        
        return optimal_threshold
    
    def _calculate_score_stats(
        self,
        scores: np.ndarray,
        y_true: pd.Series,
        threshold: float
    ) -> Dict:
        """Calculate score distribution statistics"""
        # Convert target to binary if multi-class
        if y_true.nunique() > 2:
            y_binary = (y_true >= 1).astype(int).values
        else:
            y_binary = y_true.astype(int).values
        
        # Separate scores by true class
        low_risk_scores = scores[y_binary == 0]
        high_risk_scores = scores[y_binary == 1]
        
        stats = {
            'overall': {
                'mean': float(np.mean(scores)),
                'std': float(np.std(scores)),
                'min': float(np.min(scores)),
                'max': float(np.max(scores)),
                'median': float(np.median(scores))
            },
            
            'low_risk_true': {
                'mean': float(np.mean(low_risk_scores)) if len(low_risk_scores) > 0 else None,
                'std': float(np.std(low_risk_scores)) if len(low_risk_scores) > 0 else None,
                'count': int(len(low_risk_scores))
            },
            
            'high_risk_true': {
                'mean': float(np.mean(high_risk_scores)) if len(high_risk_scores) > 0 else None,
                'std': float(np.std(high_risk_scores)) if len(high_risk_scores) > 0 else None,
                'count': int(len(high_risk_scores))
            },
            
            'threshold': threshold
        }
        
        return stats
    
    def to_dict(self) -> Dict:
        """Export scorecard configuration"""
        return {
            'binning_method': self.binning_method.value,
            'n_bins': self.n_bins,
            'min_bin_size': self.min_bin_size,
            'base_points': self.base_points,
            'use_youden': self.use_youden,
            'binning': self.binning_.to_dict() if self.binning_ else None,
            'bin_scores': self.bin_scores_,
            'feature_weights': self.feature_weights_,
            'optimal_threshold': self.optimal_threshold_,
            'threshold_metrics': self.threshold_metrics_,
            'score_stats': self.score_stats_
        }
    
    @classmethod
    def from_dict(cls, config: Dict) -> 'ScorecardGenerator':
        """Load scorecard from configuration"""
        scorecard = cls(
            binning_method=config['binning_method'],
            n_bins=config['n_bins'],
            min_bin_size=config['min_bin_size'],
            base_points=config['base_points'],
            use_youden=config['use_youden']
        )
        
        if config['binning']:
            scorecard.binning_ = DynamicBinning.from_dict(config['binning'])
        
        scorecard.bin_scores_ = config['bin_scores']
        scorecard.feature_weights_ = config['feature_weights']
        scorecard.optimal_threshold_ = config['optimal_threshold']
        scorecard.threshold_metrics_ = config.get('threshold_metrics')
        scorecard.score_stats_ = config.get('score_stats')
        
        return scorecard
    
    # =================================================================
    # CSV EXPORT FUNCTIONS FOR REPORTING
    # =================================================================
    
    def export_bin_tables_to_csv(
        self,
        output_path: str,
        include_stats: bool = True
    ) -> str:
        """
        Export all bin-score tables to CSV file
        
        Creates a comprehensive CSV report with:
        - Feature name
        - Bin range
        - Score points
        - Sample count
        - Target distribution (if available)
        
        Perfect for clinical reports and publications!
        
        Args:
            output_path: Path to save CSV file
            include_stats: Include statistical details
        
        Returns:
            Path to created CSV file
        """
        import csv
        
        all_rows = []
        
        # Header row
        header = [
            'Feature',
            'Bin_Range',
            'Score_Points',
            'Sample_Count',
            'Percentage'
        ]
        
        if include_stats:
            header.extend([
                'Mean_Value',
                'Median_Value',
                'Min_Value',
                'Max_Value'
            ])
        
        # Check if we have target distribution
        has_target_dist = False
        target_classes = []
        
        for feature in self.bin_scores_.keys():
            bin_stats = self.binning_.get_bin_stats(feature)
            if bin_stats and 'bins' in bin_stats:
                first_bin = bin_stats['bins'][0]
                if 'target_distribution' in first_bin:
                    has_target_dist = True
                    target_classes = list(first_bin['target_distribution'].keys())
                    break
        
        if has_target_dist:
            for cls in target_classes:
                header.append(f'P_{cls}')
        
        all_rows.append(header)
        
        # Data rows
        for feature in sorted(self.bin_scores_.keys()):
            bin_labels = self.binning_.get_bin_labels(feature)
            bin_stats = self.binning_.get_bin_stats(feature)
            bin_scores = self.bin_scores_[feature]
            
            if not bin_labels or not bin_stats:
                continue
            
            for i, label in enumerate(bin_labels):
                row = [
                    feature,
                    label,
                    f"{bin_scores.get(i, 0.0):.2f}",
                    bin_stats['bins'][i]['count'],
                    f"{bin_stats['bins'][i]['percentage']:.1f}%"
                ]
                
                if include_stats:
                    row.extend([
                        f"{bin_stats['bins'][i].get('mean', 0):.4f}" if bin_stats['bins'][i].get('mean') is not None else 'N/A',
                        f"{bin_stats['bins'][i].get('median', 0):.4f}" if bin_stats['bins'][i].get('median') is not None else 'N/A',
                        f"{bin_stats['bins'][i].get('min', 0):.4f}" if bin_stats['bins'][i].get('min') is not None else 'N/A',
                        f"{bin_stats['bins'][i].get('max', 0):.4f}" if bin_stats['bins'][i].get('max') is not None else 'N/A'
                    ])
                
                if has_target_dist and 'target_distribution' in bin_stats['bins'][i]:
                    target_dist = bin_stats['bins'][i]['target_distribution']
                    for cls in target_classes:
                        prob = target_dist.get(cls, 0.0)
                        row.append(f"{prob:.3f}")
                
                all_rows.append(row)
        
        # Write to CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(all_rows)
        
        logger.info(f"Exported bin-score tables to {output_path}")
        return output_path
    
    def export_threshold_report_to_csv(
        self,
        output_path: str,
        X_test: Optional[pd.DataFrame] = None,
        y_test: Optional[pd.Series] = None
    ) -> str:
        """
        Export threshold optimization report to CSV
        
        Includes:
        - Optimal threshold from Youden Index
        - Sensitivity, Specificity, J-statistic
        - Score statistics (mean, std, min, max)
        - Risk stratification performance (if test data provided)
        
        Args:
            output_path: Path to save CSV file
            X_test: Optional test data for performance metrics
            y_test: Optional test labels
        
        Returns:
            Path to created CSV file
        """
        import csv
        
        rows = []
        
        # Header
        rows.append(['=== YOUDEN INDEX THRESHOLD OPTIMIZATION ==='])
        rows.append([])
        
        # Threshold metrics
        if self.threshold_metrics_:
            rows.append(['Metric', 'Value'])
            rows.append(['Optimal_Threshold', f"{self.threshold_metrics_['threshold']:.2f}"])
            rows.append(['Youden_J_Statistic', f"{self.threshold_metrics_['youden_j']:.4f}"])
            rows.append(['Sensitivity', f"{self.threshold_metrics_['sensitivity']:.4f}"])
            rows.append(['Specificity', f"{self.threshold_metrics_['specificity']:.4f}"])
            rows.append([])
        
        # Score statistics
        if self.score_stats_:
            rows.append(['=== SCORE STATISTICS ==='])
            rows.append([])
            
            rows.append(['Overall Statistics', ''])
            rows.append(['Mean', f"{self.score_stats_['overall']['mean']:.2f}"])
            rows.append(['Std Dev', f"{self.score_stats_['overall']['std']:.2f}"])
            rows.append(['Min', f"{self.score_stats_['overall']['min']:.2f}"])
            rows.append(['Max', f"{self.score_stats_['overall']['max']:.2f}"])
            rows.append(['Median', f"{self.score_stats_['overall']['median']:.2f}"])
            rows.append([])
            
            rows.append(['Low Risk Group (True)', ''])
            rows.append(['Count', self.score_stats_['low_risk_true']['count']])
            rows.append(['Mean Score', f"{self.score_stats_['low_risk_true']['mean']:.2f}" if self.score_stats_['low_risk_true']['mean'] else 'N/A'])
            rows.append(['Std Dev', f"{self.score_stats_['low_risk_true']['std']:.2f}" if self.score_stats_['low_risk_true']['std'] else 'N/A'])
            rows.append([])
            
            rows.append(['High Risk Group (True)', ''])
            rows.append(['Count', self.score_stats_['high_risk_true']['count']])
            rows.append(['Mean Score', f"{self.score_stats_['high_risk_true']['mean']:.2f}" if self.score_stats_['high_risk_true']['mean'] else 'N/A'])
            rows.append(['Std Dev', f"{self.score_stats_['high_risk_true']['std']:.2f}" if self.score_stats_['high_risk_true']['std'] else 'N/A'])
            rows.append([])
        
        # Test performance
        if X_test is not None and y_test is not None:
            rows.append(['=== RISK STRATIFICATION PERFORMANCE ==='])
            rows.append([])
            
            perf = self.get_risk_stratification_performance(X_test, y_test)
            
            rows.append(['Risk Group', 'Count', 'Percentage', 'Score Range (Min-Max)', 'Mean Score'])
            
            rows.append([
                'Low Risk',
                perf['low_risk']['count'],
                f"{perf['low_risk']['percentage']:.1f}%",
                f"{perf['low_risk']['score_range']['min']:.2f} - {perf['low_risk']['score_range']['max']:.2f}",
                f"{perf['low_risk']['score_range']['mean']:.2f}"
            ])
            
            rows.append([
                'High Risk',
                perf['high_risk']['count'],
                f"{perf['high_risk']['percentage']:.1f}%",
                f"{perf['high_risk']['score_range']['min']:.2f} - {perf['high_risk']['score_range']['max']:.2f}",
                f"{perf['high_risk']['score_range']['mean']:.2f}"
            ])
            
            rows.append([])
            rows.append(['=== PERFORMANCE METRICS ==='])
            rows.append([])
            
            rows.append(['Metric', 'Value'])
            rows.append(['Accuracy', f"{perf['performance']['accuracy']:.4f}"])
            rows.append(['Sensitivity', f"{perf['performance']['sensitivity']:.4f}"])
            rows.append(['Specificity', f"{perf['performance']['specificity']:.4f}"])
            rows.append(['PPV (Precision)', f"{perf['performance']['ppv']:.4f}"])
            rows.append(['NPV', f"{perf['performance']['npv']:.4f}"])
            rows.append([])
            
            rows.append(['Confusion Matrix', ''])
            rows.append(['True Negatives', perf['performance']['confusion_matrix']['tn']])
            rows.append(['False Positives', perf['performance']['confusion_matrix']['fp']])
            rows.append(['False Negatives', perf['performance']['confusion_matrix']['fn']])
            rows.append(['True Positives', perf['performance']['confusion_matrix']['tp']])
        
        # Write to CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        
        logger.info(f"Exported threshold report to {output_path}")
        return output_path
    
    def export_patient_scores_to_csv(
        self,
        X: pd.DataFrame,
        output_path: str,
        include_breakdown: bool = True,
        patient_ids: Optional[List] = None
    ) -> str:
        """
        Export patient scores to CSV
        
        Creates a CSV with:
        - Patient ID (if provided)
        - Total score
        - Risk group
        - Feature-level scores (if include_breakdown=True)
        
        Perfect for clinical reporting and tracking!
        
        Args:
            X: Patient feature data
            output_path: Path to save CSV file
            include_breakdown: Include feature-level score breakdown
            patient_ids: Optional list of patient IDs
        
        Returns:
            Path to created CSV file
        """
        import csv
        
        # Calculate scores
        if include_breakdown:
            total_scores, breakdown = self.score(X, return_breakdown=True)
        else:
            total_scores = self.score(X, return_breakdown=False)
            breakdown = None
        
        # Determine risk groups
        risk_groups, _ = self.predict_risk_group(X)
        
        # Prepare rows
        rows = []
        
        # Header
        header = ['Patient_ID', 'Total_Score', 'Threshold', 'Risk_Group', 'Risk_Level']
        
        if include_breakdown and breakdown is not None:
            # Add feature score columns
            feature_score_cols = [col for col in breakdown.columns if col.endswith('_score') and col != 'total_score']
            header.extend(feature_score_cols)
        
        rows.append(header)
        
        # Data rows
        for i in range(len(X)):
            patient_id = patient_ids[i] if patient_ids else f"Patient_{i+1}"
            risk_group = "High Risk" if risk_groups[i] == 1 else "Low Risk"
            
            row = [
                patient_id,
                f"{total_scores[i]:.2f}",
                f"{self.optimal_threshold_:.2f}",
                risk_group,
                int(risk_groups[i])
            ]
            
            if include_breakdown and breakdown is not None:
                for col in feature_score_cols:
                    row.append(f"{breakdown.iloc[i][col]:.2f}")
            
            rows.append(row)
        
        # Write to CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        
        logger.info(f"Exported {len(X)} patient scores to {output_path}")
        return output_path
    
    def export_comprehensive_report(
        self,
        output_dir: str,
        model_name: str,
        version: str,
        X_test: Optional[pd.DataFrame] = None,
        y_test: Optional[pd.Series] = None
    ) -> Dict[str, str]:
        """
        Export comprehensive scorecard report (multiple CSV files)
        
        Creates:
        1. bin_score_tables.csv - Transparent bin-score tables
        2. threshold_optimization.csv - Youden Index results
        3. test_performance.csv - Risk stratification performance
        4. patient_scores.csv - Individual patient scores (if test data provided)
        
        Args:
            output_dir: Directory to save CSV files
            model_name: Model name for file naming
            version: Model version for file naming
            X_test: Optional test data
            y_test: Optional test labels
        
        Returns:
            Dictionary mapping report type to file path
        """
        import os
        
        # Create output directory if needed
        os.makedirs(output_dir, exist_ok=True)
        
        file_prefix = f"{model_name}_{version}_scorecard"
        
        report_files = {}
        
        # 1. Bin-score tables
        bin_tables_path = os.path.join(output_dir, f"{file_prefix}_bin_tables.csv")
        self.export_bin_tables_to_csv(bin_tables_path, include_stats=True)
        report_files['bin_tables'] = bin_tables_path
        
        # 2. Threshold optimization
        threshold_path = os.path.join(output_dir, f"{file_prefix}_threshold.csv")
        self.export_threshold_report_to_csv(threshold_path, X_test, y_test)
        report_files['threshold'] = threshold_path
        
        # 3. Patient scores (if test data provided)
        if X_test is not None:
            scores_path = os.path.join(output_dir, f"{file_prefix}_patient_scores.csv")
            self.export_patient_scores_to_csv(X_test, scores_path, include_breakdown=True)
            report_files['patient_scores'] = scores_path
        
        logger.info(f"Exported comprehensive scorecard report to {output_dir}")
        logger.info(f"  Files created: {list(report_files.keys())}")
        
        return report_files
