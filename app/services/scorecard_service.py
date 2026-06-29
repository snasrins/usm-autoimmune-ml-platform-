"""
Clinical Scorecard Service (USMA-47)
Converts ML predictions to transparent clinical risk scores

Implements the "Scoring" section from the research framework:
- Score Card Construction
- Risk Group Classification  
- Feature-level scoring
- Transparent bins for clinical decision support
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from sqlalchemy.orm import Session
import logging
import json

from app.services.minio_service import get_minio_service
from app.ml.feature_engineering_pipeline import FeatureEngineeringPipeline
from app.ml.scorecard.scorecard_generator import ScorecardGenerator
from app.ml.scorecard.dynamic_binning import BinningMethod

logger = logging.getLogger(__name__)


class ClinicalScorecardService:
    """
    Service for converting ML predictions to clinical scorecards
    
    Scorecards provide:
    1. Risk scores (0-100 scale)
    2. Risk groups (Low, Moderate, High, Very High)
    3. Feature contributions (which features drive the score)
    4. Transparent clinical interpretation
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.minio = get_minio_service()
    
    def generate_scorecard(
        self,
        model_name: str,
        version: str,
        patient_data: Dict,
        include_feature_scores: bool = True
    ) -> Dict:
        """
        Generate clinical scorecard for a patient prediction
        
        Args:
            model_name: Name of trained model
            version: Model version
            patient_data: Patient features
            include_feature_scores: Include individual feature scores
        
        Returns:
            Dictionary with scorecard information
        """
        try:
            logger.info(f"Generating scorecard for {model_name}/{version}")
            
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
            
            # Load model and get prediction (try fold_0..fold_4 first, then model.pkl)
            max_folds = 10
            model = None
            for fold_id in range(max_folds):
                try:
                    model = self.minio.load_model(model_name, version, fold_id=fold_id)
                    break
                except Exception:
                    continue
            if model is None:
                try:
                    model = self.minio.load_model(model_name, version)
                except Exception:
                    raise ValueError(
                        f"No model artifacts found in MinIO for {model_name}/{version}. Please retrain this model."
                    )
            prediction_proba = model.predict_proba(X)[0]
            
            # Get class mapping
            class_mapping = metadata.get('class_mapping', {})
            idx_to_class = {v: k for k, v in class_mapping.items()}
            
            # Determine predicted class
            predicted_class_idx = int(np.argmax(prediction_proba))
            predicted_class = idx_to_class.get(predicted_class_idx, f"Class_{predicted_class_idx}")
            confidence = float(prediction_proba[predicted_class_idx])
            
            # Convert probability to risk score (0-100 scale)
            risk_score = self._probability_to_risk_score(
                prediction_proba,
                predicted_class_idx,
                class_mapping
            )
            
            # Determine risk group
            risk_group = self._determine_risk_group(risk_score, predicted_class)
            
            # Build scorecard
            scorecard = {
                'model_name': model_name,
                'version': version,
                'predicted_class': predicted_class,
                'confidence': confidence,
                'risk_score': risk_score,
                'risk_group': risk_group['group'],
                'risk_level': risk_group['level'],
                'risk_description': risk_group['description'],
                'clinical_recommendation': risk_group['recommendation'],
                'probability_distribution': {
                    idx_to_class.get(i, f"Class_{i}"): float(prediction_proba[i])
                    for i in range(len(prediction_proba))
                }
            }
            
            # Add feature scores if requested
            if include_feature_scores:
                feature_scores = self._calculate_feature_scores(
                    X,
                    feature_names,
                    model,
                    predicted_class_idx
                )
                scorecard['feature_scores'] = feature_scores
                scorecard['top_contributing_features'] = feature_scores[:5]
            
            logger.info(f"Scorecard generated: Risk Score={risk_score:.1f}, Group={risk_group['group']}")
            
            return scorecard
        
        except Exception as e:
            logger.error(f"Error generating scorecard: {e}")
            raise
    
    def _probability_to_risk_score(
        self,
        probabilities: np.ndarray,
        predicted_class_idx: int,
        class_mapping: Dict
    ) -> float:
        """
        Convert model probabilities to a 0-100 risk score
        
        For SLE severity (Mild, Moderate, Severe):
        - Mild: 0-33
        - Moderate: 34-66
        - Severe: 67-100
        
        The score within each range reflects confidence
        """
        n_classes = len(probabilities)
        
        if n_classes == 2:
            # Binary classification: direct mapping
            return float(probabilities[1] * 100)
        
        elif n_classes == 3:
            # 3-class SLE severity
            # Map classes to score ranges
            class_ranges = {
                0: (0, 33),      # Mild
                1: (34, 66),     # Moderate
                2: (67, 100)     # Severe
            }
            
            range_start, range_end = class_ranges[predicted_class_idx]
            range_width = range_end - range_start
            
            # Within the range, position based on confidence
            confidence = probabilities[predicted_class_idx]
            
            # Scale confidence to position within range
            # Higher confidence -> closer to range center
            score = range_start + (range_width * confidence)
            
            return float(score)
        
        else:
            # Multi-class: generic mapping
            score_per_class = 100 / n_classes
            base_score = predicted_class_idx * score_per_class
            confidence_adjustment = probabilities[predicted_class_idx] * score_per_class
            
            return float(base_score + confidence_adjustment)
    
    def _determine_risk_group(
        self,
        risk_score: float,
        predicted_class: str
    ) -> Dict:
        """
        Determine risk group and clinical recommendations
        
        Returns dict with:
        - group: Risk group name
        - level: Numeric level (1-4)
        - description: Clinical description
        - recommendation: Clinical action recommendation
        """
        if risk_score < 25:
            return {
                'group': 'Low Risk',
                'level': 1,
                'description': 'Mild disease activity with minimal organ involvement',
                'recommendation': 'Routine monitoring, maintain current therapy',
                'color': '#28a745',  # Green
                'icon': '✓'
            }
        
        elif risk_score < 50:
            return {
                'group': 'Moderate Risk',
                'level': 2,
                'description': 'Moderate disease activity, close monitoring required',
                'recommendation': 'Consider therapy adjustment, monitor SLEDAI score',
                'color': '#ffc107',  # Yellow
                'icon': '⚠'
            }
        
        elif risk_score < 75:
            return {
                'group': 'High Risk',
                'level': 3,
                'description': 'Significant disease activity, potential organ involvement',
                'recommendation': 'Therapy escalation recommended, frequent monitoring',
                'color': '#fd7e14',  # Orange
                'icon': '⚠⚠'
            }
        
        else:
            return {
                'group': 'Very High Risk',
                'level': 4,
                'description': 'Severe disease activity, major organ involvement likely',
                'recommendation': 'Urgent intervention required, consider hospitalization',
                'color': '#dc3545',  # Red
                'icon': '⚠⚠⚠'
            }
    
    def _calculate_feature_scores(
        self,
        X: pd.DataFrame,
        feature_names: List[str],
        model,
        predicted_class_idx: int
    ) -> List[Dict]:
        """
        Calculate individual feature contributions to the score
        
        Uses feature importance or coefficients depending on model type
        
        Returns list of features sorted by contribution (descending)
        """
        try:
            feature_scores = []
            
            # Get feature values
            feature_values = X.iloc[0].values
            
            # Try to get feature importance from model
            if hasattr(model, 'feature_importances_'):
                # Tree-based models
                importances = model.feature_importances_
                
                for i, (name, value, importance) in enumerate(zip(feature_names, feature_values, importances)):
                    # Normalize importance to 0-100 scale
                    score = float(importance * 100)
                    
                    feature_scores.append({
                        'feature': name,
                        'value': float(value),
                        'importance': float(importance),
                        'score': score,
                        'contribution': 'positive' if score > 0 else 'neutral'
                    })
            
            elif hasattr(model, 'coef_'):
                # Linear models
                coefficients = model.coef_
                
                # Handle multi-class
                if len(coefficients.shape) > 1:
                    coef = coefficients[predicted_class_idx]
                else:
                    coef = coefficients
                
                for i, (name, value, coefficient) in enumerate(zip(feature_names, feature_values, coef)):
                    # Feature score = coefficient * feature value
                    contribution = float(coefficient * value)
                    score = abs(contribution) * 10  # Scale to ~0-100
                    
                    feature_scores.append({
                        'feature': name,
                        'value': float(value),
                        'coefficient': float(coefficient),
                        'score': score,
                        'contribution': 'positive' if contribution > 0 else 'negative'
                    })
            
            else:
                # Model doesn't support feature importance
                # Use simple heuristic based on feature values
                for i, (name, value) in enumerate(zip(feature_names, feature_values)):
                    score = abs(float(value)) * 10
                    
                    feature_scores.append({
                        'feature': name,
                        'value': float(value),
                        'score': min(score, 100),
                        'contribution': 'positive' if value > 0 else 'neutral'
                    })
            
            # Sort by score (descending)
            feature_scores.sort(key=lambda x: x['score'], reverse=True)
            
            return feature_scores
        
        except Exception as e:
            logger.warning(f"Error calculating feature scores: {e}")
            return []
    
    def get_risk_group_statistics(
        self,
        model_name: str,
        version: str,
        test_data: pd.DataFrame,
        test_labels: pd.Series
    ) -> Dict:
        """
        Calculate risk group distribution and statistics for a test set
        
        Args:
            model_name: Name of trained model
            version: Model version
            test_data: Test feature data
            test_labels: True labels
        
        Returns:
            Dictionary with risk group statistics
        """
        try:
            # Generate scorecards for all test patients
            scorecards = []
            
            for idx in range(len(test_data)):
                patient_data = test_data.iloc[idx].to_dict()
                
                scorecard = self.generate_scorecard(
                    model_name=model_name,
                    version=version,
                    patient_data=patient_data,
                    include_feature_scores=False
                )
                
                scorecard['true_label'] = int(test_labels.iloc[idx])
                scorecards.append(scorecard)
            
            # Calculate statistics by risk group
            risk_groups = {}
            
            for sc in scorecards:
                group = sc['risk_group']
                
                if group not in risk_groups:
                    risk_groups[group] = {
                        'count': 0,
                        'correct_predictions': 0,
                        'scores': [],
                        'true_positive_rate': 0.0,
                        'false_positive_rate': 0.0
                    }
                
                risk_groups[group]['count'] += 1
                risk_groups[group]['scores'].append(sc['risk_score'])
                
                # Check if prediction matches true label
                predicted_idx = sc['predicted_class']
                true_idx = sc['true_label']
                
                if predicted_idx == true_idx:
                    risk_groups[group]['correct_predictions'] += 1
            
            # Calculate accuracy per group
            for group, stats in risk_groups.items():
                stats['accuracy'] = stats['correct_predictions'] / stats['count'] if stats['count'] > 0 else 0
                stats['avg_score'] = float(np.mean(stats['scores']))
                stats['min_score'] = float(np.min(stats['scores']))
                stats['max_score'] = float(np.max(stats['scores']))
            
            result = {
                'model_name': model_name,
                'version': version,
                'total_samples': len(scorecards),
                'risk_groups': risk_groups,
                'score_distribution': {
                    'mean': float(np.mean([sc['risk_score'] for sc in scorecards])),
                    'std': float(np.std([sc['risk_score'] for sc in scorecards])),
                    'min': float(np.min([sc['risk_score'] for sc in scorecards])),
                    'max': float(np.max([sc['risk_score'] for sc in scorecards]))
                }
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Error calculating risk group statistics: {e}")
            raise
    
    # =================================================================
    # RESEARCH-GRADE DYNAMIC SCORECARD SYSTEM
    # =================================================================
    
    def generate_dynamic_scorecard(
        self,
        model_name: str,
        version: str,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: Optional[pd.DataFrame] = None,
        y_test: Optional[pd.Series] = None,
        binning_method: Union[BinningMethod, str] = BinningMethod.ROLLING_MEAN,
        n_bins: int = 4,
        use_youden: bool = True
    ) -> Dict:
        """
        Generate research-grade white-box scorecard with dynamic binning
        
        This implements the sophisticated scorecard system from research:
        - Dynamic binning with rolling mean algorithm
        - Feature-level bin scoring (transparent point values)
        - Youden Index threshold optimization
        - Multiplicative scoring (global weights × local probabilities)
        - Risk stratification performance metrics
        
        Args:
            model_name: Name of trained model
            version: Model version
            X_train: Training features
            y_train: Training target
            X_test: Optional test features for validation
            y_test: Optional test target for validation
            binning_method: Binning strategy (default: rolling_mean)
            n_bins: Target number of bins per feature
            use_youden: Use Youden Index for optimal threshold
        
        Returns:
            Dict containing:
            - scorecard_config: Complete scorecard configuration
            - bin_tables: Transparent bin-score tables
            - optimal_threshold: Data-driven risk cutoff
            - train_performance: Training set metrics
            - test_performance: Test set metrics (if provided)
        """
        try:
            logger.info(f"Generating dynamic scorecard for {model_name}/{version}")
            
            # Load model and metadata
            model = self.minio.load_model(model_name, version)
            metadata = self.minio.load_metadata(model_name, version)
            feature_names = metadata.get('feature_names', [])
            
            # Initialize scorecard generator
            scorecard_gen = ScorecardGenerator(
                binning_method=binning_method,
                n_bins=n_bins,
                use_youden=use_youden
            )
            
            # Fit scorecard on training data
            logger.info("Fitting scorecard with dynamic binning...")
            scorecard_gen.fit(
                X_train=X_train[feature_names],
                y_train=y_train,
                model=model,
                feature_names=feature_names
            )
            
            # Get bin-score tables (white-box transparency)
            bin_tables = scorecard_gen.get_all_scorecard_tables()
            
            # Calculate scores for training set
            train_scores, train_breakdown = scorecard_gen.score(
                X_train[feature_names],
                return_breakdown=True
            )
            
            # Get training performance
            train_performance = {
                'score_stats': scorecard_gen.score_stats_,
                'optimal_threshold': scorecard_gen.optimal_threshold_,
                'threshold_metrics': scorecard_gen.threshold_metrics_
            }
            
            result = {
                'model_name': model_name,
                'version': version,
                'scorecard_config': scorecard_gen.to_dict(),
                'bin_tables': bin_tables.to_dict(orient='records'),
                'optimal_threshold': scorecard_gen.optimal_threshold_,
                'train_performance': train_performance
            }
            
            # Calculate test performance if test data provided
            if X_test is not None and y_test is not None:
                logger.info("Calculating test set performance...")
                test_performance = scorecard_gen.get_risk_stratification_performance(
                    X_test[feature_names],
                    y_test
                )
                result['test_performance'] = test_performance
            
            # Save scorecard to MinIO
            logger.info("Saving scorecard to MinIO...")
            scorecard_key = f"{model_name}/{version}/scorecard.json"
            self.minio.minio_client.put_object(
                Bucket=self.minio.model_bucket,
                Key=scorecard_key,
                Body=json.dumps(result, indent=2).encode('utf-8'),
                ContentType='application/json'
            )
            
            logger.info(f"Dynamic scorecard generated and saved: {scorecard_key}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error generating dynamic scorecard: {e}")
            raise
    
    def score_patient_dynamic(
        self,
        model_name: str,
        version: str,
        patient_data: Dict,
        return_breakdown: bool = True
    ) -> Dict:
        """
        Score a patient using the dynamic scorecard system
        
        Returns:
        - total_score: Transparent risk score
        - risk_group: Low/High risk based on optimal threshold
        - feature_scores: Individual feature contributions (if requested)
        - bin_assignments: Which bin each feature falls into
        """
        try:
            # Load scorecard configuration
            scorecard_key = f"{model_name}/{version}/scorecard.json"
            scorecard_data = self.minio.minio_client.get_object(
                Bucket=self.minio.model_bucket,
                Key=scorecard_key
            )
            scorecard_config = json.loads(scorecard_data['Body'].read().decode('utf-8'))
            
            # Reconstruct scorecard generator
            scorecard_gen = ScorecardGenerator.from_dict(scorecard_config['scorecard_config'])
            
            # Prepare patient data
            metadata = self.minio.load_metadata(model_name, version)
            feature_names = metadata.get('feature_names', [])
            
            df = pd.DataFrame([patient_data])
            
            # Apply feature engineering
            if 'feature_pipeline_config' in metadata:
                pipeline = FeatureEngineeringPipeline.from_config(metadata['feature_pipeline_config'])
                df = pipeline.transform(df, is_inference=True)
            
            # Ensure all features present
            for feat in feature_names:
                if feat not in df.columns:
                    df[feat] = 0
            
            # Calculate score
            if return_breakdown:
                total_score, breakdown = scorecard_gen.score(
                    df[feature_names],
                    return_breakdown=True
                )
                total_score = float(total_score[0])
            else:
                total_score = float(scorecard_gen.score(df[feature_names])[0])
                breakdown = None
            
            # Determine risk group
            risk_groups, _ = scorecard_gen.predict_risk_group(df[feature_names])
            risk_group = "High Risk" if risk_groups[0] == 1 else "Low Risk"
            
            result = {
                'model_name': model_name,
                'version': version,
                'total_score': total_score,
                'optimal_threshold': scorecard_gen.optimal_threshold_,
                'risk_group': risk_group,
                'risk_level': 1 if risk_group == "High Risk" else 0
            }
            
            if return_breakdown:
                result['feature_scores'] = breakdown.iloc[0].to_dict()
            
            return result
        
        except Exception as e:
            logger.error(f"Error scoring patient with dynamic scorecard: {e}")
            raise
    
    # =================================================================
    # CSV EXPORT FUNCTIONS FOR CLINICAL REPORTING
    # =================================================================
    
    def export_scorecard_reports(
        self,
        model_name: str,
        version: str,
        output_dir: str,
        X_test: Optional[pd.DataFrame] = None,
        y_test: Optional[pd.Series] = None
    ) -> Dict[str, str]:
        """
        Export comprehensive scorecard reports to CSV files
        
        This is a service wrapper that:
        1. Loads the scorecard from MinIO
        2. Generates multiple CSV reports
        3. Returns paths to all generated files
        
        Perfect for clinical documentation and publication!
        
        Args:
            model_name: Model name
            version: Model version
            output_dir: Directory to save CSV files
            X_test: Optional test data for patient scoring
            y_test: Optional test labels for performance metrics
        
        Returns:
            Dictionary mapping report type to file path
            {
                'bin_tables': 'path/to/bin_tables.csv',
                'threshold': 'path/to/threshold.csv',
                'patient_scores': 'path/to/patient_scores.csv'
            }
        """
        try:
            logger.info(f"Exporting scorecard reports for {model_name}/{version}")
            
            # Load scorecard configuration
            scorecard_key = f"{model_name}/{version}/scorecard.json"
            scorecard_data = self.minio.minio_client.get_object(
                Bucket=self.minio.model_bucket,
                Key=scorecard_key
            )
            scorecard_config = json.loads(scorecard_data['Body'].read().decode('utf-8'))
            
            # Reconstruct scorecard generator
            from app.ml.scorecard.scorecard_generator import ScorecardGenerator
            scorecard_gen = ScorecardGenerator.from_dict(scorecard_config['scorecard_config'])
            
            # Export comprehensive report
            report_files = scorecard_gen.export_comprehensive_report(
                output_dir=output_dir,
                model_name=model_name,
                version=version,
                X_test=X_test,
                y_test=y_test
            )
            
            logger.info(f"Scorecard reports exported successfully to {output_dir}")
            
            return report_files
        
        except Exception as e:
            logger.error(f"Error exporting scorecard reports: {e}")
            raise
    
    def export_bin_tables_csv(
        self,
        model_name: str,
        version: str,
        output_path: str
    ) -> str:
        """
        Export only bin-score tables to CSV
        
        This is the most important table for clinicians - shows
        transparent bins and point values for manual calculation.
        
        Args:
            model_name: Model name
            version: Model version
            output_path: Path to save CSV file
        
        Returns:
            Path to created CSV file
        """
        try:
            # Load scorecard
            scorecard_key = f"{model_name}/{version}/scorecard.json"
            scorecard_data = self.minio.minio_client.get_object(
                Bucket=self.minio.model_bucket,
                Key=scorecard_key
            )
            scorecard_config = json.loads(scorecard_data['Body'].read().decode('utf-8'))
            
            # Reconstruct scorecard generator
            from app.ml.scorecard.scorecard_generator import ScorecardGenerator
            scorecard_gen = ScorecardGenerator.from_dict(scorecard_config['scorecard_config'])
            
            # Export bin tables
            result_path = scorecard_gen.export_bin_tables_to_csv(
                output_path=output_path,
                include_stats=True
            )
            
            logger.info(f"Bin-score tables exported to {result_path}")
            
            return result_path
        
        except Exception as e:
            logger.error(f"Error exporting bin tables: {e}")
            raise
    
    def export_patient_scores_csv(
        self,
        model_name: str,
        version: str,
        patient_data_list: List[Dict],
        output_path: str,
        patient_ids: Optional[List] = None
    ) -> str:
        """
        Export patient scores to CSV for clinical tracking
        
        Args:
            model_name: Model name
            version: Model version
            patient_data_list: List of patient feature dictionaries
            output_path: Path to save CSV file
            patient_ids: Optional list of patient IDs
        
        Returns:
            Path to created CSV file
        """
        try:
            # Load scorecard and model metadata
            scorecard_key = f"{model_name}/{version}/scorecard.json"
            scorecard_data = self.minio.minio_client.get_object(
                Bucket=self.minio.model_bucket,
                Key=scorecard_key
            )
            scorecard_config = json.loads(scorecard_data['Body'].read().decode('utf-8'))
            
            metadata = self.minio.load_metadata(model_name, version)
            feature_names = metadata.get('feature_names', [])
            
            # Reconstruct scorecard generator
            from app.ml.scorecard.scorecard_generator import ScorecardGenerator
            scorecard_gen = ScorecardGenerator.from_dict(scorecard_config['scorecard_config'])
            
            # Prepare patient data
            patient_dfs = []
            for patient_data in patient_data_list:
                df = pd.DataFrame([patient_data])
                
                # Apply feature engineering
                if 'feature_pipeline_config' in metadata:
                    from app.ml.feature_engineering_pipeline import FeatureEngineeringPipeline
                    pipeline = FeatureEngineeringPipeline.from_config(metadata['feature_pipeline_config'])
                    df = pipeline.transform(df, is_inference=True)
                
                # Ensure all features present
                for feat in feature_names:
                    if feat not in df.columns:
                        df[feat] = 0
                
                patient_dfs.append(df[feature_names])
            
            # Combine all patients
            X = pd.concat(patient_dfs, ignore_index=True)
            
            # Export scores
            result_path = scorecard_gen.export_patient_scores_to_csv(
                X=X,
                output_path=output_path,
                include_breakdown=True,
                patient_ids=patient_ids
            )
            
            logger.info(f"Patient scores exported to {result_path}")
            
            return result_path
        
        except Exception as e:
            logger.error(f"Error exporting patient scores: {e}")
            raise


