"""
Dynamic Binning Algorithm for Clinical Scorecard System
Implements research-aligned binning strategies including rolling mean algorithm

Based on research framework:
- Replace subjective or equal-width bins
- Use rolling mean algorithm to find meaningful cut-points
- Capture nonlinear relationships accurately
- Data-driven bin creation
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class BinningMethod(Enum):
    """Binning strategies for continuous features"""
    ROLLING_MEAN = "rolling_mean"  # Research study approach
    QUANTILE = "quantile"  # Equal-frequency bins
    EQUAL_WIDTH = "equal_width"  # Equal-width bins
    TARGET_BASED = "target_based"  # Maximize target separation
    TREE_BASED = "tree_based"  # Decision tree-based splits


class DynamicBinning:
    """
    Dynamic feature binning for transparent clinical scorecards
    
    Implements multiple binning strategies with focus on rolling mean algorithm
    from the research study.
    """
    
    def __init__(
        self,
        method: Union[BinningMethod, str] = BinningMethod.ROLLING_MEAN,
        n_bins: int = 4,
        min_bin_size: int = 5,
        window_size: Optional[int] = None
    ):
        """
        Initialize dynamic binning
        
        Args:
            method: Binning method to use
            n_bins: Target number of bins (may be adjusted based on data)
            min_bin_size: Minimum samples per bin
            window_size: Window size for rolling mean (default: len(data) // n_bins)
        """
        if isinstance(method, str):
            method = BinningMethod(method)
        
        self.method = method
        self.n_bins = n_bins
        self.min_bin_size = min_bin_size
        self.window_size = window_size
        self.bin_edges_: Dict[str, List[float]] = {}
        self.bin_labels_: Dict[str, List[str]] = {}
        self.bin_stats_: Dict[str, Dict] = {}
    
    def fit(
        self,
        X: pd.DataFrame,
        y: Optional[pd.Series] = None,
        features: Optional[List[str]] = None
    ) -> 'DynamicBinning':
        """
        Fit binning strategy on training data
        
        Args:
            X: Feature dataframe
            y: Target variable (required for target-based binning)
            features: List of features to bin (default: all numeric)
        
        Returns:
            self
        """
        if features is None:
            # Auto-detect numeric features
            features = X.select_dtypes(include=[np.number]).columns.tolist()
        
        logger.info(f"Fitting {self.method.value} binning for {len(features)} features")
        
        for feature in features:
            if feature not in X.columns:
                logger.warning(f"Feature {feature} not in dataframe, skipping")
                continue
            
            feature_data = X[feature].dropna()
            
            if len(feature_data) < self.min_bin_size:
                logger.warning(f"Feature {feature} has too few samples, skipping")
                continue
            
            # Create bins based on method
            if self.method == BinningMethod.ROLLING_MEAN:
                edges, labels, stats = self._rolling_mean_binning(
                    feature_data, y, feature
                )
            
            elif self.method == BinningMethod.QUANTILE:
                edges, labels, stats = self._quantile_binning(
                    feature_data, feature
                )
            
            elif self.method == BinningMethod.EQUAL_WIDTH:
                edges, labels, stats = self._equal_width_binning(
                    feature_data, feature
                )
            
            elif self.method == BinningMethod.TARGET_BASED:
                if y is None:
                    raise ValueError("Target-based binning requires target variable y")
                edges, labels, stats = self._target_based_binning(
                    feature_data, y, feature
                )
            
            elif self.method == BinningMethod.TREE_BASED:
                if y is None:
                    raise ValueError("Tree-based binning requires target variable y")
                edges, labels, stats = self._tree_based_binning(
                    feature_data, y, feature
                )
            
            else:
                raise ValueError(f"Unknown binning method: {self.method}")
            
            self.bin_edges_[feature] = edges
            self.bin_labels_[feature] = labels
            self.bin_stats_[feature] = stats
        
        logger.info(f"Binning fitted for {len(self.bin_edges_)} features")
        return self
    
    def transform(
        self,
        X: pd.DataFrame,
        return_bins: bool = True
    ) -> Union[pd.DataFrame, Tuple[pd.DataFrame, pd.DataFrame]]:
        """
        Transform features to bins
        
        Args:
            X: Feature dataframe
            return_bins: If True, return both binned data and bin indices
        
        Returns:
            Binned dataframe (and optionally bin indices)
        """
        X_binned = X.copy()
        X_bin_indices = pd.DataFrame(index=X.index)
        
        for feature in self.bin_edges_.keys():
            if feature not in X.columns:
                continue
            
            edges = self.bin_edges_[feature]
            labels = self.bin_labels_[feature]
            
            # Assign to bins
            bin_indices = np.digitize(X[feature], edges, right=False)
            
            # Handle edge cases
            bin_indices = np.clip(bin_indices, 0, len(labels) - 1)
            
            # Create binned column
            X_binned[f"{feature}_bin"] = [labels[i] for i in bin_indices]
            X_bin_indices[feature] = bin_indices
        
        if return_bins:
            return X_binned, X_bin_indices
        else:
            return X_binned
    
    def fit_transform(
        self,
        X: pd.DataFrame,
        y: Optional[pd.Series] = None,
        features: Optional[List[str]] = None,
        return_bins: bool = True
    ) -> Union[pd.DataFrame, Tuple[pd.DataFrame, pd.DataFrame]]:
        """Fit and transform in one step"""
        self.fit(X, y, features)
        return self.transform(X, return_bins)
    
    def _rolling_mean_binning(
        self,
        data: pd.Series,
        y: Optional[pd.Series],
        feature_name: str
    ) -> Tuple[List[float], List[str], Dict]:
        """
        Rolling mean algorithm to find meaningful cut-points
        
        Research approach:
        1. Sort feature values
        2. Calculate rolling mean of target variable
        3. Find points where rolling mean changes significantly
        4. Use these as bin edges
        
        This captures nonlinear relationships between feature and target
        """
        sorted_data = data.sort_values()
        
        # Determine window size
        if self.window_size is not None:
            window = self.window_size
        else:
            window = max(self.min_bin_size, len(data) // (self.n_bins * 2))
        
        if y is not None:
            # Align target with sorted feature
            y_sorted = y.loc[sorted_data.index]
            
            # Convert target to numeric if needed
            if y_sorted.dtype == 'object' or y_sorted.dtype.name == 'category':
                y_numeric = pd.Categorical(y_sorted).codes
            else:
                y_numeric = y_sorted
            
            # Calculate rolling mean
            rolling_mean = pd.Series(y_numeric.values).rolling(
                window=window, 
                center=True, 
                min_periods=1
            ).mean()
            
            # Find change points (where rolling mean changes significantly)
            mean_diff = np.abs(np.diff(rolling_mean))
            mean_diff_smoothed = pd.Series(mean_diff).rolling(
                window=window // 2, 
                center=True, 
                min_periods=1
            ).mean()
            
            # Find peaks in the difference (significant changes)
            threshold = np.percentile(mean_diff_smoothed, 75)
            change_points = np.where(mean_diff_smoothed > threshold)[0]
            
            # Select n_bins-1 change points
            if len(change_points) > self.n_bins - 1:
                # Select evenly spaced change points
                indices = np.linspace(0, len(change_points) - 1, self.n_bins - 1, dtype=int)
                change_points = change_points[indices]
            
            # Create bin edges from change points
            if len(change_points) > 0:
                edges = [sorted_data.iloc[0] - 1e-6]  # Start edge
                for cp in change_points:
                    edges.append(sorted_data.iloc[cp])
                edges.append(sorted_data.iloc[-1] + 1e-6)  # End edge
            else:
                # Fallback to quantile binning
                edges = self._quantile_binning(data, feature_name)[0]
        
        else:
            # Without target, use quantile binning
            logger.warning(f"No target provided for rolling mean binning of {feature_name}, using quantile")
            return self._quantile_binning(data, feature_name)
        
        # Create bin labels
        labels = []
        for i in range(len(edges) - 1):
            if i == 0:
                labels.append(f"≤ {edges[i+1]:.2f}")
            elif i == len(edges) - 2:
                labels.append(f"> {edges[i]:.2f}")
            else:
                labels.append(f"{edges[i]:.2f}-{edges[i+1]:.2f}")
        
        # Calculate bin statistics
        bin_indices = np.digitize(data, edges, right=False)
        bin_indices = np.clip(bin_indices, 0, len(labels) - 1)
        
        stats = self._calculate_bin_stats(data, y, bin_indices, labels)
        
        return edges, labels, stats
    
    def _quantile_binning(
        self,
        data: pd.Series,
        feature_name: str
    ) -> Tuple[List[float], List[str], Dict]:
        """Equal-frequency binning using quantiles"""
        quantiles = np.linspace(0, 1, self.n_bins + 1)
        edges = data.quantile(quantiles).values.tolist()
        
        # Remove duplicates (can happen with discrete data)
        edges = sorted(list(set(edges)))
        
        # Create labels
        labels = []
        for i in range(len(edges) - 1):
            if i == 0:
                labels.append(f"≤ {edges[i+1]:.2f}")
            elif i == len(edges) - 2:
                labels.append(f"> {edges[i]:.2f}")
            else:
                labels.append(f"{edges[i]:.2f}-{edges[i+1]:.2f}")
        
        # Calculate statistics
        bin_indices = np.digitize(data, edges, right=False)
        bin_indices = np.clip(bin_indices, 0, len(labels) - 1)
        
        stats = self._calculate_bin_stats(data, None, bin_indices, labels)
        
        return edges, labels, stats
    
    def _equal_width_binning(
        self,
        data: pd.Series,
        feature_name: str
    ) -> Tuple[List[float], List[str], Dict]:
        """Equal-width binning"""
        min_val = data.min()
        max_val = data.max()
        width = (max_val - min_val) / self.n_bins
        
        edges = [min_val + i * width for i in range(self.n_bins + 1)]
        
        # Create labels
        labels = []
        for i in range(len(edges) - 1):
            if i == 0:
                labels.append(f"≤ {edges[i+1]:.2f}")
            elif i == len(edges) - 2:
                labels.append(f"> {edges[i]:.2f}")
            else:
                labels.append(f"{edges[i]:.2f}-{edges[i+1]:.2f}")
        
        # Calculate statistics
        bin_indices = np.digitize(data, edges, right=False)
        bin_indices = np.clip(bin_indices, 0, len(labels) - 1)
        
        stats = self._calculate_bin_stats(data, None, bin_indices, labels)
        
        return edges, labels, stats
    
    def _target_based_binning(
        self,
        data: pd.Series,
        y: pd.Series,
        feature_name: str
    ) -> Tuple[List[float], List[str], Dict]:
        """
        Binning that maximizes separation between target classes
        
        Sorts data and finds split points that maximize target separation
        """
        # Align data and target
        aligned_data = data.loc[y.index]
        
        # Convert target to numeric
        if y.dtype == 'object' or y.dtype.name == 'category':
            y_numeric = pd.Categorical(y).codes
        else:
            y_numeric = y
        
        # Sort by feature value
        sorted_indices = aligned_data.argsort()
        sorted_data = aligned_data.iloc[sorted_indices]
        sorted_target = y_numeric.iloc[sorted_indices]
        
        # Find optimal split points using variance reduction
        edges = [sorted_data.iloc[0] - 1e-6]
        
        for _ in range(self.n_bins - 1):
            best_split = None
            best_variance_reduction = -np.inf
            
            # Try each potential split point
            for i in range(self.min_bin_size, len(sorted_data) - self.min_bin_size):
                if sorted_data.iloc[i] == sorted_data.iloc[i-1]:
                    continue  # Skip duplicate values
                
                # Calculate variance reduction
                left_target = sorted_target.iloc[:i]
                right_target = sorted_target.iloc[i:]
                
                total_var = sorted_target.var()
                left_var = left_target.var() if len(left_target) > 1 else 0
                right_var = right_target.var() if len(right_target) > 1 else 0
                
                weighted_var = (len(left_target) * left_var + len(right_target) * right_var) / len(sorted_target)
                variance_reduction = total_var - weighted_var
                
                if variance_reduction > best_variance_reduction:
                    best_variance_reduction = variance_reduction
                    best_split = sorted_data.iloc[i]
            
            if best_split is not None:
                edges.append(best_split)
        
        edges.append(sorted_data.iloc[-1] + 1e-6)
        edges = sorted(edges)
        
        # Create labels
        labels = []
        for i in range(len(edges) - 1):
            if i == 0:
                labels.append(f"≤ {edges[i+1]:.2f}")
            elif i == len(edges) - 2:
                labels.append(f"> {edges[i]:.2f}")
            else:
                labels.append(f"{edges[i]:.2f}-{edges[i+1]:.2f}")
        
        # Calculate statistics
        bin_indices = np.digitize(data, edges, right=False)
        bin_indices = np.clip(bin_indices, 0, len(labels) - 1)
        
        stats = self._calculate_bin_stats(data, y, bin_indices, labels)
        
        return edges, labels, stats
    
    def _tree_based_binning(
        self,
        data: pd.Series,
        y: pd.Series,
        feature_name: str
    ) -> Tuple[List[float], List[str], Dict]:
        """
        Use decision tree to find optimal splits
        """
        from sklearn.tree import DecisionTreeClassifier
        
        # Prepare data
        X = data.values.reshape(-1, 1)
        
        # Convert target to numeric if needed
        if y.dtype == 'object' or y.dtype.name == 'category':
            y_numeric = pd.Categorical(y).codes
        else:
            y_numeric = y.values
        
        # Fit decision tree
        tree = DecisionTreeClassifier(
            max_leaf_nodes=self.n_bins,
            min_samples_leaf=self.min_bin_size,
            random_state=42
        )
        tree.fit(X, y_numeric)
        
        # Extract split points
        tree_structure = tree.tree_
        thresholds = tree_structure.threshold
        features = tree_structure.feature
        
        # Get thresholds for this feature (feature index is 0)
        split_points = sorted([t for t, f in zip(thresholds, features) if f == 0 and t != -2])
        
        # Create edges
        edges = [data.min() - 1e-6] + split_points + [data.max() + 1e-6]
        
        # Create labels
        labels = []
        for i in range(len(edges) - 1):
            if i == 0:
                labels.append(f"≤ {edges[i+1]:.2f}")
            elif i == len(edges) - 2:
                labels.append(f"> {edges[i]:.2f}")
            else:
                labels.append(f"{edges[i]:.2f}-{edges[i+1]:.2f}")
        
        # Calculate statistics
        bin_indices = np.digitize(data, edges, right=False)
        bin_indices = np.clip(bin_indices, 0, len(labels) - 1)
        
        stats = self._calculate_bin_stats(data, y, bin_indices, labels)
        
        return edges, labels, stats
    
    def _calculate_bin_stats(
        self,
        data: pd.Series,
        y: Optional[pd.Series],
        bin_indices: np.ndarray,
        labels: List[str]
    ) -> Dict:
        """Calculate statistics for each bin"""
        stats = {
            'n_bins': len(labels),
            'bins': {}
        }
        
        for i, label in enumerate(labels):
            mask = bin_indices == i
            bin_data = data[mask]
            
            bin_stats = {
                'label': label,
                'count': int(mask.sum()),
                'percentage': float(mask.sum() / len(data) * 100),
                'min': float(bin_data.min()) if len(bin_data) > 0 else None,
                'max': float(bin_data.max()) if len(bin_data) > 0 else None,
                'mean': float(bin_data.mean()) if len(bin_data) > 0 else None,
                'median': float(bin_data.median()) if len(bin_data) > 0 else None
            }
            
            # Add target statistics if available
            if y is not None:
                bin_target = y[mask]
                
                if len(bin_target) > 0:
                    # Handle both numeric and categorical targets
                    if bin_target.dtype == 'object' or bin_target.dtype.name == 'category':
                        target_dist = bin_target.value_counts(normalize=True).to_dict()
                        bin_stats['target_distribution'] = {
                            str(k): float(v) for k, v in target_dist.items()
                        }
                    else:
                        bin_stats['target_mean'] = float(bin_target.mean())
                        bin_stats['target_std'] = float(bin_target.std()) if len(bin_target) > 1 else 0.0
            
            stats['bins'][i] = bin_stats
        
        return stats
    
    def get_bin_edges(self, feature: str) -> Optional[List[float]]:
        """Get bin edges for a feature"""
        return self.bin_edges_.get(feature)
    
    def get_bin_labels(self, feature: str) -> Optional[List[str]]:
        """Get bin labels for a feature"""
        return self.bin_labels_.get(feature)
    
    def get_bin_stats(self, feature: str) -> Optional[Dict]:
        """Get bin statistics for a feature"""
        return self.bin_stats_.get(feature)
    
    def to_dict(self) -> Dict:
        """Export binning configuration to dictionary"""
        return {
            'method': self.method.value,
            'n_bins': self.n_bins,
            'min_bin_size': self.min_bin_size,
            'window_size': self.window_size,
            'bin_edges': self.bin_edges_,
            'bin_labels': self.bin_labels_,
            'bin_stats': self.bin_stats_
        }
    
    @classmethod
    def from_dict(cls, config: Dict) -> 'DynamicBinning':
        """Load binning configuration from dictionary"""
        binning = cls(
            method=config['method'],
            n_bins=config['n_bins'],
            min_bin_size=config['min_bin_size'],
            window_size=config.get('window_size')
        )
        
        binning.bin_edges_ = config['bin_edges']
        binning.bin_labels_ = config['bin_labels']
        binning.bin_stats_ = config['bin_stats']
        
        return binning
