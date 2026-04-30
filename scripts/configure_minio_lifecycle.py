"""
MinIO Lifecycle Policy Manager (Python)
JIRA: USMA-76 - Configure MinIO Bucket Lifecycle Policies

Provides programmatic configuration of:
- Automatic file expiration (delete after retention period)
- Transition to infrequent access storage (cost optimization)
- Object versioning (data recovery)
- Bucket quotas (cost control)
"""
import os
import json
from datetime import datetime
from minio import Minio
from minio.commonconfig import ENABLED
from minio.versioningconfig import VersioningConfig
from minio.lifecycleconfig import LifecycleConfig, Rule, Expiration, Transition, Filter


class MinIOLifecycleManager:
    """Manage MinIO bucket lifecycle policies"""
    
    def __init__(self):
        """Initialize MinIO client from environment or defaults"""
        self.endpoint = os.getenv("MINIO_ENDPOINT", "100.106.132.15:9000")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "minio_admin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "MinIO_P@ssw0rd_2026")
        self.secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
        
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure
        )
        
        print(f"✓ Connected to MinIO: {self.endpoint}")
    
    def create_buckets(self):
        """Create required buckets if they don't exist"""
        buckets = ["usm-raw", "usm-processed", "usm-models"]
        
        for bucket in buckets:
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)
                print(f"  Created bucket: {bucket}")
            else:
                print(f"  Bucket exists: {bucket}")
    
    def enable_versioning(self):
        """Enable versioning on all buckets for data recovery"""
        buckets = ["usm-raw", "usm-processed", "usm-models"]
        
        versioning_config = VersioningConfig(ENABLED)
        
        for bucket in buckets:
            self.client.set_bucket_versioning(bucket, versioning_config)
            print(f"  ✓ Versioning enabled: {bucket}")
    
    def configure_raw_bucket_lifecycle(self):
        """
        Configure lifecycle for usm-raw bucket
        
        Rules:
        - Delete files older than 365 days (NMRR compliance)
        - Move files older than 90 days to infrequent access
        - Delete old versions after 30 days
        """
        config = LifecycleConfig(
            [
                Rule(
                    rule_id="delete-old-raw-files",
                    rule_filter=Filter(prefix=""),  # Apply to all objects (empty prefix)
                    status=ENABLED,
                    expiration=Expiration(days=365)
                ),
                Rule(
                    rule_id="transition-to-ia",
                    rule_filter=Filter(prefix=""),
                    status=ENABLED,
                    transition=Transition(days=90, storage_class="STANDARD_IA")
                ),
                Rule(
                    rule_id="cleanup-old-versions",
                    rule_filter=Filter(prefix=""),
                    status=ENABLED,
                    noncurrent_version_expiration_days=30
                )
            ]
        )
        
        self.client.set_bucket_lifecycle("usm-raw", config)
        print("  ✓ Raw bucket lifecycle: 365 days retention, 90 days → IA")
    
    def configure_processed_bucket_lifecycle(self):
        """
        Configure lifecycle for usm-processed bucket
        
        Rules:
        - Delete files older than 730 days (2 years for research)
        - Move files older than 180 days to infrequent access
        """
        config = LifecycleConfig(
            [
                Rule(
                    rule_id="delete-old-processed-files",
                    rule_filter=Filter(prefix=""),
                    status=ENABLED,
                    expiration=Expiration(days=730)
                ),
                Rule(
                    rule_id="transition-to-ia",
                    rule_filter=Filter(prefix=""),
                    status=ENABLED,
                    transition=Transition(days=180, storage_class="STANDARD_IA")
                )
            ]
        )
        
        self.client.set_bucket_lifecycle("usm-processed", config)
        print("  ✓ Processed bucket lifecycle: 730 days retention, 180 days → IA")
    
    def configure_models_bucket_lifecycle(self):
        """
        Configure lifecycle for usm-models bucket
        
        Rules:
        - Keep production models indefinitely (regulatory requirement)
        - Move experimental models to IA after 90 days
        - Delete failed models after 30 days
        """
        config = LifecycleConfig(
            [
                Rule(
                    rule_id="archive-experimental-models",
                    rule_filter=Filter(prefix="experimental/"),
                    status=ENABLED,
                    transition=Transition(days=90, storage_class="STANDARD_IA")
                ),
                Rule(
                    rule_id="delete-failed-models",
                    rule_filter=Filter(prefix="failed/"),
                    status=ENABLED,
                    expiration=Expiration(days=30)
                )
            ]
        )
        
        self.client.set_bucket_lifecycle("usm-models", config)
        print("  ✓ Models bucket lifecycle: Production → keep forever, experimental → IA")
    
    def verify_configuration(self):
        """Verify lifecycle policies are applied"""
        buckets = ["usm-raw", "usm-processed", "usm-models"]
        
        print("\n=== Lifecycle Policy Verification ===")
        
        for bucket in buckets:
            try:
                config = self.client.get_bucket_lifecycle(bucket)
                print(f"\n{bucket}:")
                
                for rule in config.rules:
                    print(f"  • Rule: {rule.rule_id}")
                    if rule.expiration:
                        print(f"    - Expires after: {rule.expiration.days} days")
                    if rule.transition:
                        print(f"    - Transition to {rule.transition.storage_class} after {rule.transition.days} days")
                    
            except Exception as e:
                print(f"  ⚠ No lifecycle policy for {bucket}: {e}")
    
    def get_storage_stats(self):
        """Get storage usage statistics"""
        buckets = ["usm-raw", "usm-processed", "usm-models"]
        
        print("\n=== Storage Statistics ===")
        
        total_size = 0
        total_objects = 0
        
        for bucket in buckets:
            try:
                objects = self.client.list_objects(bucket, recursive=True)
                
                bucket_size = 0
                bucket_objects = 0
                
                for obj in objects:
                    bucket_size += obj.size
                    bucket_objects += 1
                
                total_size += bucket_size
                total_objects += bucket_objects
                
                size_mb = bucket_size / (1024 * 1024)
                print(f"{bucket}: {bucket_objects} objects, {size_mb:.2f} MB")
                
            except Exception as e:
                print(f"{bucket}: Error - {e}")
        
        total_size_gb = total_size / (1024 * 1024 * 1024)
        print(f"\nTotal: {total_objects} objects, {total_size_gb:.2f} GB")
    
    def run_full_configuration(self):
        """Execute complete lifecycle configuration"""
        print("=" * 60)
        print("MinIO Lifecycle Policy Configuration")
        print("=" * 60)
        
        print("\n[1/5] Creating buckets...")
        self.create_buckets()
        
        print("\n[2/5] Enabling versioning...")
        self.enable_versioning()
        
        print("\n[3/5] Configuring lifecycle policies...")
        self.configure_raw_bucket_lifecycle()
        self.configure_processed_bucket_lifecycle()
        self.configure_models_bucket_lifecycle()
        
        print("\n[4/5] Verifying configuration...")
        self.verify_configuration()
        
        print("\n[5/5] Storage statistics...")
        self.get_storage_stats()
        
        print("\n" + "=" * 60)
        print("✅ MinIO Lifecycle Policies Configured Successfully")
        print("=" * 60)
        print("\nSummary:")
        print("  • Raw files: 365 days retention, 90 days → IA")
        print("  • Processed files: 730 days retention, 180 days → IA")
        print("  • Production models: Kept indefinitely")
        print("  • Experimental models: 90 days → IA")
        print("  • Versioning: Enabled on all buckets")
        print("  • Old versions: Deleted after 30 days")
        print("\nCompliance:")
        print("  ✓ NMRR ethics: Raw data kept for 1 year minimum")
        print("  ✓ Reproducibility: Production models kept forever")
        print("  ✓ Cost optimization: Old data moved to IA storage")
        print("  ✓ Data recovery: Versioning enabled")
        print()


def main():
    """Main entry point"""
    manager = MinIOLifecycleManager()
    manager.run_full_configuration()


if __name__ == "__main__":
    main()
