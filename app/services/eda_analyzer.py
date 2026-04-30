"""
EDA (Exploratory Data Analysis) Service
Generate comprehensive statistical analysis and visualizations
USMA-33, USMA-32
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class EDAAnalyzer:
    """
    Comprehensive EDA analysis generator
    USMA-33: Develop EDA platform
    """
    
    def __init__(self):
        self.analysis_cache = {}
    
    def generate_summary_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate comprehensive summary statistics
        """
        summary = {
            "dataset_overview": {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "total_cells": df.size,
                "memory_usage_mb": round(df.memory_usage(deep=True).sum() / 1024**2, 2)
            },
            
            "data_types": {
                "numeric_columns": len(df.select_dtypes(include=['int64', 'float64']).columns),
                "categorical_columns": len(df.select_dtypes(include=['object', 'category']).columns),
                "datetime_columns": len(df.select_dtypes(include=['datetime64']).columns),
                "boolean_columns": len(df.select_dtypes(include=['bool']).columns)
            },
            
            "missing_data": {
                "total_missing_cells": int(df.isnull().sum().sum()),
                "missing_percentage": round(df.isnull().sum().sum() / df.size * 100, 2),
                "columns_with_missing": int((df.isnull().sum() > 0).sum()),
                "rows_with_missing": int(df.isnull().any(axis=1).sum())
            },
            
            "duplicates": {
                "duplicate_rows": int(df.duplicated().sum()),
                "duplicate_percentage": round(df.duplicated().sum() / len(df) * 100, 2)
            },
            
            "numeric_summary": self._numeric_summary(df),
            "categorical_summary": self._categorical_summary(df)
        }
        
        return summary
    
    def _numeric_summary(self, df: pd.DataFrame) -> Dict:
        """Generate summary for numeric columns"""
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
        
        if len(numeric_cols) == 0:
            return {"message": "No numeric columns found"}
        
        summary = {}
        for col in numeric_cols:
            col_data = df[col].dropna()
            
            if len(col_data) == 0:
                summary[col] = {"error": "All values are null"}
                continue
            
            summary[col] = {
                "count": int(col_data.count()),
                "mean": float(col_data.mean()),
                "median": float(col_data.median()),
                "mode": float(col_data.mode()[0]) if not col_data.mode().empty else None,
                "std": float(col_data.std()),
                "variance": float(col_data.var()),
                "min": float(col_data.min()),
                "max": float(col_data.max()),
                "range": float(col_data.max() - col_data.min()),
                "q25": float(col_data.quantile(0.25)),
                "q50": float(col_data.quantile(0.50)),
                "q75": float(col_data.quantile(0.75)),
                "iqr": float(col_data.quantile(0.75) - col_data.quantile(0.25)),
                "skewness": float(col_data.skew()),
                "kurtosis": float(col_data.kurtosis()),
                "cv": float(col_data.std() / col_data.mean() * 100) if col_data.mean() != 0 else None,  # Coefficient of variation
            }
        
        return summary
    
    def _categorical_summary(self, df: pd.DataFrame) -> Dict:
        """Generate summary for categorical columns"""
        cat_cols = df.select_dtypes(include=['object', 'category']).columns
        
        if len(cat_cols) == 0:
            return {"message": "No categorical columns found"}
        
        summary = {}
        for col in cat_cols:
            col_data = df[col].dropna()
            
            if len(col_data) == 0:
                summary[col] = {"error": "All values are null"}
                continue
            
            value_counts = col_data.value_counts()
            
            summary[col] = {
                "count": int(col_data.count()),
                "unique_count": int(col_data.nunique()),
                "unique_ratio": round(col_data.nunique() / len(col_data) * 100, 2),
                "mode": str(col_data.mode()[0]) if not col_data.mode().empty else None,
                "mode_frequency": int(value_counts.iloc[0]) if len(value_counts) > 0 else 0,
                "mode_percentage": round(value_counts.iloc[0] / len(col_data) * 100, 2) if len(value_counts) > 0 else 0,
                "top_10_values": {
                    str(k): int(v) for k, v in value_counts.head(10).items()
                },
                "is_high_cardinality": col_data.nunique() > 50
            }
        
        return summary
    
    def generate_univariate_analysis(self, df: pd.DataFrame, column: str) -> Dict[str, Any]:
        """
        Detailed univariate analysis for a single column
        """
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in dataset")
        
        col_data = df[column]
        dtype = str(col_data.dtype)
        
        analysis = {
            "column_name": column,
            "data_type": dtype,
            "total_count": len(col_data),
            "non_null_count": int(col_data.count()),
            "null_count": int(col_data.isnull().sum()),
            "null_percentage": round(col_data.isnull().sum() / len(col_data) * 100, 2)
        }
        
        # Numeric analysis
        if col_data.dtype in ['int64', 'float64']:
            clean_data = col_data.dropna()
            
            analysis.update({
                "statistics": {
                    "mean": float(clean_data.mean()),
                    "median": float(clean_data.median()),
                    "mode": float(clean_data.mode()[0]) if not clean_data.mode().empty else None,
                    "std": float(clean_data.std()),
                    "variance": float(clean_data.var()),
                    "min": float(clean_data.min()),
                    "max": float(clean_data.max()),
                    "range": float(clean_data.max() - clean_data.min()),
                    "q25": float(clean_data.quantile(0.25)),
                    "q50": float(clean_data.quantile(0.50)),
                    "q75": float(clean_data.quantile(0.75)),
                    "iqr": float(clean_data.quantile(0.75) - clean_data.quantile(0.25)),
                    "skewness": float(clean_data.skew()),
                    "kurtosis": float(clean_data.kurtosis())
                },
                
                "distribution": {
                    "is_normal": self._test_normality(clean_data),
                    "histogram_bins": self._calculate_histogram(clean_data, bins=30),
                },
                
                "outliers": self._detect_column_outliers(clean_data)
            })
        
        # Categorical analysis
        else:
            clean_data = col_data.dropna()
            value_counts = clean_data.value_counts()
            
            analysis.update({
                "statistics": {
                    "unique_count": int(clean_data.nunique()),
                    "unique_ratio": round(clean_data.nunique() / len(clean_data) * 100, 2),
                    "mode": str(clean_data.mode()[0]) if not clean_data.mode().empty else None,
                    "mode_frequency": int(value_counts.iloc[0]) if len(value_counts) > 0 else 0
                },
                
                "value_distribution": {
                    str(k): {
                        "count": int(v),
                        "percentage": round(v / len(clean_data) * 100, 2)
                    }
                    for k, v in value_counts.head(20).items()
                },
                
                "cardinality_analysis": {
                    "is_high_cardinality": clean_data.nunique() > 50,
                    "is_binary": clean_data.nunique() == 2,
                    "is_unique_identifier": clean_data.nunique() == len(clean_data)
                }
            })
        
        return analysis
    
    def generate_bivariate_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Bivariate analysis - correlations and relationships
        """
        numeric_df = df.select_dtypes(include=['int64', 'float64'])
        
        if len(numeric_df.columns) < 2:
            return {"error": "Need at least 2 numeric columns for bivariate analysis"}
        
        # Correlation matrix
        corr_matrix = numeric_df.corr()
        
        # Find top correlations
        corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                col1 = corr_matrix.columns[i]
                col2 = corr_matrix.columns[j]
                corr_value = corr_matrix.iloc[i, j]
                
                if not np.isnan(corr_value):
                    corr_pairs.append({
                        "variable_1": col1,
                        "variable_2": col2,
                        "correlation": float(corr_value),
                        "abs_correlation": abs(float(corr_value)),
                        "strength": self._classify_correlation_strength(abs(corr_value))
                    })
        
        # Sort by absolute correlation
        corr_pairs.sort(key=lambda x: x["abs_correlation"], reverse=True)
        
        analysis = {
            "correlation_matrix": {
                "columns": corr_matrix.columns.tolist(),
                "values": corr_matrix.values.tolist()
            },
            "top_correlations": corr_pairs[:20],  # Top 20 correlations
            "high_correlations": [p for p in corr_pairs if p["abs_correlation"] > 0.7],
            "moderate_correlations": [p for p in corr_pairs if 0.4 <= p["abs_correlation"] <= 0.7],
        }
        
        return analysis
    
    def generate_multivariate_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Multivariate analysis - PCA, clustering insights
        """
        numeric_df = df.select_dtypes(include=['int64', 'float64']).dropna()
        
        if len(numeric_df.columns) < 3:
            return {"error": "Need at least 3 numeric columns for multivariate analysis"}
        
        # Variance explained by each feature
        feature_variance = {
            col: {
                "variance": float(numeric_df[col].var()),
                "std": float(numeric_df[col].std()),
                "coefficient_of_variation": float(numeric_df[col].std() / numeric_df[col].mean() * 100) if numeric_df[col].mean() != 0 else None
            }
            for col in numeric_df.columns
        }
        
        analysis = {
            "feature_variance": feature_variance,
            "total_features": len(numeric_df.columns),
            "observations": len(numeric_df)
        }
        
        return analysis
    
    def _test_normality(self, data: pd.Series) -> Dict:
        """Test if data follows normal distribution"""
        if len(data) < 3:
            return {"test": "insufficient_data"}
        
        # Shapiro-Wilk test (max 5000 samples)
        sample_size = min(len(data), 5000)
        sample = data.sample(n=sample_size, random_state=42)
        
        statistic, p_value = stats.shapiro(sample)
        
        return {
            "test": "shapiro_wilk",
            "statistic": float(statistic),
            "p_value": float(p_value),
            "is_normal": p_value > 0.05,
            "interpretation": "Normal distribution" if p_value > 0.05 else "Not normal distribution"
        }
    
    def _calculate_histogram(self, data: pd.Series, bins: int = 30) -> Dict:
        """Calculate histogram data"""
        counts, bin_edges = np.histogram(data, bins=bins)
        
        return {
            "bin_edges": bin_edges.tolist(),
            "counts": counts.tolist(),
            "bin_width": float(bin_edges[1] - bin_edges[0])
        }
    
    def _detect_column_outliers(self, data: pd.Series) -> Dict:
        """Detect outliers using IQR method"""
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = data[(data < lower_bound) | (data > upper_bound)]
        
        return {
            "outlier_count": len(outliers),
            "outlier_percentage": round(len(outliers) / len(data) * 100, 2),
            "lower_bound": float(lower_bound),
            "upper_bound": float(upper_bound),
            "outlier_values": outliers.head(50).tolist()  # Limit to 50
        }
    
    def _classify_correlation_strength(self, corr: float) -> str:
        """Classify correlation strength"""
        if corr >= 0.9:
            return "very_strong"
        elif corr >= 0.7:
            return "strong"
        elif corr >= 0.4:
            return "moderate"
        elif corr >= 0.2:
            return "weak"
        else:
            return "very_weak"
    
    def generate_data_profile_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate comprehensive data profile report
        Combines all analysis types
        """
        return {
            "summary_statistics": self.generate_summary_statistics(df),
            "bivariate_analysis": self.generate_bivariate_analysis(df),
            "multivariate_analysis": self.generate_multivariate_analysis(df)
        }
