"""
MinIO Service for ML Model Storage
Handles model persistence, versioning, and retrieval
"""
import io
import joblib
import json
import re
from datetime import datetime
from typing import Optional, Dict, Any, List
from minio import Minio
from minio.error import S3Error
import logging

logger = logging.getLogger(__name__)


class MinIOService:
    """Service for storing and retrieving ML models from MinIO"""
    
    # NMRR Compliance: Forbidden patterns in metadata
    FORBIDDEN_ID_PATTERNS = [
        r'patient[_\s]?id',
        r'ic[_\s]?number',
        r'nric',
        r'passport',
        r'medical[_\s]?record[_\s]?number',
        r'mrn',
        r'identity',
        r'identification',
        r'person[_\s]?id',
        r'user[_\s]?id',
        r'full[_\s]?name',
        r'phone[_\s]?number',
        r'email[_\s]?address',
        r'address',
        r'birthdate',
        r'date[_\s]?of[_\s]?birth',
        r'dob'
    ]
    
    def __init__(
        self,
        endpoint: str = "localhost:9000",
        access_key: str = "minioadmin",
        secret_key: str = "minioadmin",
        secure: bool = False
    ):
        """
        Initialize MinIO client
        
        Args:
            endpoint: MinIO server endpoint
            access_key: MinIO access key
            secret_key: MinIO secret key
            secure: Whether to use HTTPS
        """
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        self.models_bucket = "ml-models"
        self.artifacts_bucket = "ml-artifacts"
        
        # Data pipeline buckets
        self.raw_data_bucket = "usm-raw-data"
        self.preprocessed_bucket = "usm-preprocessed"
        self.ml_datasets_bucket = "ml-datasets"
        self.scorecards_bucket = "clinical-scorecards"
        self.predictions_bucket = "predictions"
        self.analytics_bucket = "analytics"
        
        self._ensure_buckets_exist()
    
    def _ensure_buckets_exist(self):
        """Create buckets if they don't exist"""
        buckets = [
            self.models_bucket,
            self.artifacts_bucket,
            self.raw_data_bucket,
            self.preprocessed_bucket,
            self.ml_datasets_bucket,
            self.scorecards_bucket,
            self.predictions_bucket,
            self.analytics_bucket
        ]
        
        try:
            for bucket in buckets:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
                    logger.info(f"Created bucket: {bucket}")
        except S3Error as e:
            logger.error(f"Error creating buckets: {e}")
            raise
    
    def _check_nmrr_compliance(self, metadata: Dict[str, Any]) -> None:
        """
        Check metadata for NMRR compliance violations
        
        CRITICAL: Ensures no patient identifiers are stored in model artifacts
        
        Args:
            metadata: Metadata dictionary to check
        
        Raises:
            ValueError: If forbidden patterns are detected
        """
        violations = []
        
        def check_dict_recursively(d: Dict, path: str = ""):
            """Recursively check dictionary keys and values"""
            for key, value in d.items():
                current_path = f"{path}.{key}" if path else key
                
                # Check if key name contains forbidden patterns
                key_lower = str(key).lower()
                for pattern in self.FORBIDDEN_ID_PATTERNS:
                    if re.search(pattern, key_lower, re.IGNORECASE):
                        violations.append(f"Forbidden identifier in key: {current_path} (matches pattern: {pattern})")
                
                # Recursively check nested dictionaries
                if isinstance(value, dict):
                    check_dict_recursively(value, current_path)
                elif isinstance(value, list):
                    for idx, item in enumerate(value):
                        if isinstance(item, dict):
                            check_dict_recursively(item, f"{current_path}[{idx}]")
                        elif isinstance(item, str):
                            # Check string values in lists
                            for pattern in self.FORBIDDEN_ID_PATTERNS:
                                if re.search(pattern, item.lower(), re.IGNORECASE):
                                    violations.append(f"Forbidden identifier in value: {current_path}[{idx}]")
        
        # Check metadata
        check_dict_recursively(metadata)
        
        if violations:
            error_msg = f"NMRR COMPLIANCE VIOLATION: Patient identifiers detected in metadata!\n"
            error_msg += "\n".join([f"  - {v}" for v in violations])
            error_msg += "\n\nEnsure all patient identifiers are removed before model storage."
            error_msg += "\nAllowed: feature names, aggregate statistics, model parameters"
            error_msg += "\nForbidden: patient IDs, names, contact info, birthdates"
            
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.debug("✓ NMRR compliance check passed - no patient identifiers detected")
    
    def save_model(
        self,
        model: Any,
        model_name: str,
        version: str,
        fold_id: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Save a trained model to MinIO
        
        Args:
            model: Trained model object
            model_name: Name of the model (e.g., 'xgboost', 'ensemble')
            version: Model version (e.g., 'v1', 'v2')
            fold_id: Fold number if this is a CV fold model
            metadata: Additional metadata to store
        
        Returns:
            MinIO object path
        """
        try:
            # Construct object path
            if fold_id is not None:
                object_name = f"{model_name}/{version}/fold_{fold_id}.pkl"
            else:
                object_name = f"{model_name}/{version}/model.pkl"
            
            # Serialize model to bytes
            buffer = io.BytesIO()
            joblib.dump(model, buffer)
            buffer.seek(0)
            
            # Upload to MinIO
            self.client.put_object(
                self.models_bucket,
                object_name,
                buffer,
                length=buffer.getbuffer().nbytes,
                content_type="application/octet-stream"
            )
            
            # Save metadata if provided
            if metadata:
                # CRITICAL: Check for NMRR compliance violations
                self._check_nmrr_compliance(metadata)
                
                metadata_obj = f"{model_name}/{version}/metadata.json"
                metadata_bytes = json.dumps(metadata, indent=2).encode('utf-8')
                self.client.put_object(
                    self.models_bucket,
                    metadata_obj,
                    io.BytesIO(metadata_bytes),
                    length=len(metadata_bytes),
                    content_type="application/json"
                )
            
            logger.info(f"Saved model to MinIO: {object_name}")
            return object_name
        
        except Exception as e:
            logger.error(f"Error saving model to MinIO: {e}")
            raise
    
    def load_model(
        self,
        model_name: str,
        version: str,
        fold_id: Optional[int] = None
    ) -> Any:
        """
        Load a trained model from MinIO
        
        Args:
            model_name: Name of the model
            version: Model version
            fold_id: Fold number if loading a CV fold model
        
        Returns:
            Loaded model object
        """
        try:
            # Construct object path
            if fold_id is not None:
                object_name = f"{model_name}/{version}/fold_{fold_id}.pkl"
            else:
                object_name = f"{model_name}/{version}/model.pkl"
            
            # Download from MinIO
            response = self.client.get_object(self.models_bucket, object_name)
            model_bytes = response.read()
            response.close()
            response.release_conn()
            
            # Deserialize model
            model = joblib.load(io.BytesIO(model_bytes))
            
            logger.info(f"Loaded model from MinIO: {object_name}")
            return model
        
        except Exception as e:
            logger.error(f"Error loading model from MinIO: {e}")
            raise
    
    def load_all_folds(
        self,
        model_name: str,
        version: str,
        n_folds: int = 5
    ) -> List[Any]:
        """
        Load all fold models for a given model version
        
        Args:
            model_name: Name of the model
            version: Model version
            n_folds: Number of folds to load
        
        Returns:
            List of fold models
        """
        fold_models = []
        for fold_id in range(n_folds):
            model = self.load_model(model_name, version, fold_id)
            fold_models.append(model)
        return fold_models
    
    def load_metadata(
        self,
        model_name: str,
        version: str
    ) -> Dict:
        """
        Load model metadata from MinIO
        
        Args:
            model_name: Name of the model
            version: Model version
        
        Returns:
            Metadata dictionary
        """
        try:
            object_name = f"{model_name}/{version}/metadata.json"
            response = self.client.get_object(self.models_bucket, object_name)
            metadata_bytes = response.read()
            response.close()
            response.release_conn()
            
            metadata = json.loads(metadata_bytes.decode('utf-8'))
            return metadata
        
        except Exception as e:
            logger.error(f"Error loading metadata from MinIO: {e}")
            return {}
    
    def save_artifact(
        self,
        artifact_data: bytes,
        artifact_name: str,
        model_name: str,
        version: str,
        content_type: str = "image/png"
    ) -> str:
        """
        Save model artifacts (plots, reports, SHAP values) to MinIO
        
        Args:
            artifact_data: Artifact data as bytes
            artifact_name: Name of the artifact (e.g., 'shap_summary.png')
            model_name: Associated model name
            version: Model version
            content_type: MIME type
        
        Returns:
            MinIO object path
        """
        try:
            object_name = f"{model_name}/{version}/artifacts/{artifact_name}"
            
            self.client.put_object(
                self.artifacts_bucket,
                object_name,
                io.BytesIO(artifact_data),
                length=len(artifact_data),
                content_type=content_type
            )
            
            logger.info(f"Saved artifact to MinIO: {object_name}")
            return object_name
        
        except Exception as e:
            logger.error(f"Error saving artifact to MinIO: {e}")
            raise
    
    def list_model_versions(self, model_name: str) -> List[str]:
        """
        List all versions of a model
        
        Args:
            model_name: Name of the model
        
        Returns:
            List of version strings
        """
        try:
            objects = self.client.list_objects(
                self.models_bucket,
                prefix=f"{model_name}/",
                recursive=False
            )
            versions = set()
            for obj in objects:
                # Extract version from path: model_name/v1/...
                parts = obj.object_name.split('/')
                if len(parts) >= 2:
                    versions.add(parts[1])
            
            return sorted(list(versions))
        
        except Exception as e:
            logger.error(f"Error listing model versions: {e}")
            return []
    
    def delete_model(self, model_name: str, version: str):
        """
        Delete a model version from MinIO
        
        Args:
            model_name: Name of the model
            version: Model version to delete
        """
        try:
            # List all objects with this prefix
            objects = self.client.list_objects(
                self.models_bucket,
                prefix=f"{model_name}/{version}/",
                recursive=True
            )
            
            # Delete each object
            for obj in objects:
                self.client.remove_object(self.models_bucket, obj.object_name)
            
            logger.info(f"Deleted model: {model_name}/{version}")
        
        except Exception as e:
            logger.error(f"Error deleting model: {e}")
            raise
    
    def save_preprocessed_data(
        self,
        df_csv: bytes,
        batch_id: str,
        stage: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Save preprocessed data to MinIO
        
        Args:
            df_csv: CSV data as bytes
            batch_id: Batch/session ID
            stage: Preprocessing stage (e.g., 'after_imputation', 'after_outlier_handling', 'final')
            metadata: Optional metadata
        
        Returns:
            MinIO object path
        """
        try:
            # Create bucket if doesn't exist
            bucket_name = "usm-preprocessed"
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
            
            # Save CSV
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            object_name = f"batch_{batch_id}/{stage}_{timestamp}.csv"
            
            self.client.put_object(
                bucket_name,
                object_name,
                io.BytesIO(df_csv),
                length=len(df_csv),
                content_type="text/csv"
            )
            
            # Save metadata if provided
            if metadata:
                self._check_nmrr_compliance(metadata)
                metadata_obj = f"batch_{batch_id}/{stage}_{timestamp}_metadata.json"
                metadata_bytes = json.dumps(metadata, indent=2).encode('utf-8')
                self.client.put_object(
                    bucket_name,
                    metadata_obj,
                    io.BytesIO(metadata_bytes),
                    length=len(metadata_bytes),
                    content_type="application/json"
                )
            
            logger.info(f"✓ Saved preprocessed data to MinIO: {object_name}")
            return object_name
        
        except Exception as e:
            logger.error(f"Error saving preprocessed data to MinIO: {e}")
            raise
    
    def save_ml_dataset(
        self,
        dataset_pickle: bytes,
        batch_id: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Save ML-ready dataset (train/test split) to MinIO
        
        Args:
            dataset_pickle: Pickled dataset (X_train, X_test, y_train, y_test)
            batch_id: Batch ID
            metadata: Dataset metadata
        
        Returns:
            MinIO object path
        """
        try:
            bucket_name = "ml-datasets"
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            object_name = f"dataset_{batch_id}/dataset_{timestamp}.pkl"
            
            self.client.put_object(
                bucket_name,
                object_name,
                io.BytesIO(dataset_pickle),
                length=len(dataset_pickle),
                content_type="application/octet-stream"
            )
            
            # Save metadata
            if metadata:
                self._check_nmrr_compliance(metadata)
                metadata_obj = f"dataset_{batch_id}/metadata_{timestamp}.json"
                metadata_bytes = json.dumps(metadata, indent=2).encode('utf-8')
                self.client.put_object(
                    bucket_name,
                    metadata_obj,
                    io.BytesIO(metadata_bytes),
                    length=len(metadata_bytes),
                    content_type="application/json"
                )
            
            logger.info(f"✓ Saved ML dataset to MinIO: {object_name}")
            return object_name
        
        except Exception as e:
            logger.error(f"Error saving ML dataset to MinIO: {e}")
            raise
    
    def save_scorecard_artifacts(
        self,
        scorecard_id: str,
        artifacts: Dict[str, bytes],
        metadata: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Save scorecard artifacts (bin tables, thresholds, reports) to MinIO
        
        Args:
            scorecard_id: Scorecard ID
            artifacts: Dictionary of {filename: bytes_data}
            metadata: Scorecard metadata
        
        Returns:
            Dictionary of {filename: minio_path}
        """
        try:
            bucket_name = "clinical-scorecards"
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
            
            saved_paths = {}
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            for filename, data in artifacts.items():
                object_name = f"scorecard_{scorecard_id}/{timestamp}_{filename}"
                
                # Determine content type
                if filename.endswith('.csv'):
                    content_type = "text/csv"
                elif filename.endswith('.json'):
                    content_type = "application/json"
                else:
                    content_type = "application/octet-stream"
                
                self.client.put_object(
                    bucket_name,
                    object_name,
                    io.BytesIO(data),
                    length=len(data),
                    content_type=content_type
                )
                
                saved_paths[filename] = object_name
            
            # Save metadata
            if metadata:
                self._check_nmrr_compliance(metadata)
                metadata_obj = f"scorecard_{scorecard_id}/metadata_{timestamp}.json"
                metadata_bytes = json.dumps(metadata, indent=2).encode('utf-8')
                self.client.put_object(
                    bucket_name,
                    metadata_obj,
                    io.BytesIO(metadata_bytes),
                    length=len(metadata_bytes),
                    content_type="application/json"
                )
            
            logger.info(f"✓ Saved {len(artifacts)} scorecard artifacts to MinIO")
            return saved_paths
        
        except Exception as e:
            logger.error(f"Error saving scorecard artifacts to MinIO: {e}")
            raise
    
    def save_prediction_results(
        self,
        predictions_csv: bytes,
        batch_id: str,
        model_name: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Save batch prediction results to MinIO
        
        Args:
            predictions_csv: Predictions as CSV bytes
            batch_id: Batch ID
            model_name: Model used for predictions
            metadata: Prediction metadata
        
        Returns:
            MinIO object path
        """
        try:
            bucket_name = "predictions"
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            object_name = f"batch_{batch_id}/predictions_{model_name}_{timestamp}.csv"
            
            self.client.put_object(
                bucket_name,
                object_name,
                io.BytesIO(predictions_csv),
                length=len(predictions_csv),
                content_type="text/csv"
            )
            
            # Save metadata
            if metadata:
                self._check_nmrr_compliance(metadata)
                metadata_obj = f"batch_{batch_id}/predictions_{model_name}_{timestamp}_metadata.json"
                metadata_bytes = json.dumps(metadata, indent=2).encode('utf-8')
                self.client.put_object(
                    bucket_name,
                    metadata_obj,
                    io.BytesIO(metadata_bytes),
                    length=len(metadata_bytes),
                    content_type="application/json"
                )
            
            logger.info(f"✓ Saved prediction results to MinIO: {object_name}")
            return object_name
        
        except Exception as e:
            logger.error(f"Error saving predictions to MinIO: {e}")
            raise
    
    def save_eda_artifact(
        self,
        artifact_data: bytes,
        batch_id: str,
        artifact_name: str,
        artifact_type: str = "plot",
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Save EDA/visualization artifacts to MinIO
        
        Args:
            artifact_data: Artifact bytes (PNG, JSON, etc.)
            batch_id: Batch ID
            artifact_name: Name of artifact (e.g., 'correlation_matrix.png')
            artifact_type: Type ('plot', 'json', 'csv')
            metadata: Artifact metadata
        
        Returns:
            MinIO object path
        """
        try:
            bucket_name = "analytics"
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            object_name = f"eda_{batch_id}/{artifact_type}/{timestamp}_{artifact_name}"
            
            # Determine content type
            if artifact_name.endswith('.png'):
                content_type = "image/png"
            elif artifact_name.endswith('.json'):
                content_type = "application/json"
            elif artifact_name.endswith('.csv'):
                content_type = "text/csv"
            else:
                content_type = "application/octet-stream"
            
            self.client.put_object(
                bucket_name,
                object_name,
                io.BytesIO(artifact_data),
                length=len(artifact_data),
                content_type=content_type
            )
            
            # Save metadata
            if metadata:
                self._check_nmrr_compliance(metadata)
                metadata_obj = f"eda_{batch_id}/{artifact_type}/{timestamp}_{artifact_name}_metadata.json"
                metadata_bytes = json.dumps(metadata, indent=2).encode('utf-8')
                self.client.put_object(
                    bucket_name,
                    metadata_obj,
                    io.BytesIO(metadata_bytes),
                    length=len(metadata_bytes),
                    content_type="application/json"
                )
            
            logger.info(f"✓ Saved EDA artifact to MinIO: {object_name}")
            return object_name
        
        except Exception as e:
            logger.error(f"Error saving EDA artifact to MinIO: {e}")
            raise


# Singleton instance
minio_service = None

def get_minio_service() -> MinIOService:
    """Get or create MinIO service singleton"""
    global minio_service
    if minio_service is None:
        from app.core.config import settings
        minio_service = MinIOService(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
    return minio_service
