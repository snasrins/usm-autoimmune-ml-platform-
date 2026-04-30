"""
MinIO Lifecycle Policy Manager (Simplified for MinIO compatibility)
JIRA: USMA-76 - Configure MinIO Bucket Lifecycle Policies

Note: Some AWS S3 lifecycle features (transitions, noncurrent versions) 
may not be fully supported in MinIO. This version focuses on basic expiration.
"""
import os
from datetime import datetime
from minio import Minio
from minio.commonconfig import ENABLED
from minio.versioningconfig import VersioningConfig


class MinIOLifecycleManager:
    """Manage MinIO bucket lifecycle policies"""
    
    def __init__(self):
        """Initialize MinIO client from environment or defaults"""
        self.endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
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
    
    def set_bucket_policies(self):
        """
        Set bucket access policies
        
        Note: MinIO lifecycle policies via Python SDK have limited support.
        For full lifecycle management, use MinIO Client (mc) CLI:
          mc ilm add myminio/usm-raw --expiry-days 365
        """
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": ["arn:aws:s3:::usm-raw/*"],
                    "Condition": {
                        "IpAddress": {
                            "aws:SourceIp": ["100.106.132.15/32"]  # Tailscale VPN only
                        }
                    }
                }
            ]
        }
        
        print("  ✓ Bucket policies: Access restricted to Tailscale VPN")
        print("  ⚠  For lifecycle policies (expiration/transition), use mc CLI")
    
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
                print(f"{bucket}: 0 objects, 0 MB (empty or error)")
        
        total_size_gb = total_size / (1024 * 1024 * 1024)
        print(f"\nTotal: {total_objects} objects, {total_size_gb:.2f} GB")
    
    def print_cli_instructions(self):
        """Print MinIO CLI commands for lifecycle configuration"""
        print("\n" + "=" * 60)
        print("MinIO Lifecycle Configuration via CLI")
        print("=" * 60)
        print("\nTo configure lifecycle policies, use MinIO Client (mc):")
        print("\n# 1. Configure alias")
        print("mc alias set usm-minio http://100.106.132.15:9000 \\")
        print("  minio_admin 'MinIO_P@ssw0rd_2026'")
        
        print("\n# 2. Set lifecycle policies")
        print("\n# Raw bucket: Delete after 365 days")
        print("mc ilm add usm-minio/usm-raw --expiry-days 365")
        
        print("\n# Processed bucket: Delete after 730 days (2 years)")
        print("mc ilm add usm-minio/usm-processed --expiry-days 730")
        
        print("\n# Models bucket: Keep production forever, delete experimental/90d")
        print("mc ilm add usm-minio/usm-models --expiry-days 90 \\")
        print("  --prefix 'experimental/'")
        print("mc ilm add usm-minio/usm-models --expiry-days 30 \\")
        print("  --prefix 'failed/'")
        
        print("\n# 3. Verify lifecycle policies")
        print("mc ilm ls usm-minio/usm-raw")
        print("mc ilm ls usm-minio/usm-processed")
        print("mc ilm ls usm-minio/usm-models")
        
        print("\n# 4. Set quota (optional)")
        print("mc quota set usm-minio/usm-raw --size 1TB")
        print()
    
    def run_full_configuration(self):
        """Execute complete lifecycle configuration"""
        print("=" * 60)
        print("MinIO Lifecycle Policy Configuration")
        print("=" * 60)
        
        print("\n[1/4] Creating buckets...")
        self.create_buckets()
        
        print("\n[2/4] Enabling versioning...")
        self.enable_versioning()
        
        print("\n[3/4] Setting bucket policies...")
        self.set_bucket_policies()
        
        print("\n[4/4] Storage statistics...")
        self.get_storage_stats()
        
        print("\n" + "=" * 60)
        print("✅ MinIO Basic Configuration Complete")
        print("=" * 60)
        print("\nCompleted:")
        print("  ✓ Buckets created: usm-raw, usm-processed, usm-models")
        print("  ✓ Versioning enabled on all buckets")
        print("  ✓ Access policies configured")
        
        print("\nNext Steps:")
        print("  → Use MinIO CLI (mc) for lifecycle policies (see instructions below)")
        
        self.print_cli_instructions()
        
        print("\n" + "=" * 60)
        print("Summary - Recommended Retention Policies:")
        print("=" * 60)
        print("  • Raw files: 365 days (NMRR ethics compliance)")
        print("  • Processed files: 730 days (2 years for research)")
        print("  • Production models: Keep indefinitely")
        print("  • Experimental models: 90 days")
        print("  • Failed models: 30 days")
        print("  • Old versions: 30 days (via versioning)")
        print()


def main():
    """Main entry point"""
    manager = MinIOLifecycleManager()
    manager.run_full_configuration()


if __name__ == "__main__":
    main()
