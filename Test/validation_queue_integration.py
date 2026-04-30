#!/usr/bin/env python3
"""
Validation Queue Integration
==============================
Purpose: Store OCR output in PostgreSQL validation_queue for human review
Author: Syarifah Fajriyah
Date: March 24, 2026

Flow:
1. Upload raw PDF to MinIO (usm-raw bucket)
2. Calculate SHA-256 hash (deduplication)
3. Insert metadata into metadata_datasets table
4. Run OCR + NER pipeline
5. Insert results into validation_queue.validation_data JSONB
6. Wait for human approval (CHECKPOINT 2: OCR Output Review)
"""

import os
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from minio import Minio
from minio.error import S3Error


# ═══════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════

# MinIO Configuration (adjust to your setup)
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET_RAW = "usm-raw"  # Raw uploaded files
MINIO_BUCKET_PROCESSED = "usm-processed"  # OCR outputs
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

# PostgreSQL Configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "usm_autoimmune")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")


# ═══════════════════════════════════════════════════════════
#  MINIO CLIENT
# ═══════════════════════════════════════════════════════════

def get_minio_client() -> Minio:
    """Initialize MinIO client with retry logic"""
    try:
        client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )
        # Test connection
        client.bucket_exists(MINIO_BUCKET_RAW)
        return client
    except S3Error as e:
        print(f"⚠️ MinIO connection failed: {e}")
        print(f"   Endpoint: {MINIO_ENDPOINT}")
        print(f"   Using local filesystem as fallback...")
        return None


def ensure_buckets_exist(client: Minio) -> None:
    """Create MinIO buckets if they don't exist"""
    if not client:
        return
    
    try:
        for bucket in [MINIO_BUCKET_RAW, MINIO_BUCKET_PROCESSED]:
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)
                print(f"   ✓ Created MinIO bucket: {bucket}")
    except S3Error as e:
        print(f"⚠️ Bucket creation failed: {e}")


def upload_file_to_minio(client: Minio, file_path: str, bucket: str, object_name: Optional[str] = None) -> Optional[str]:
    """
    Upload file to MinIO and return the object path
    
    Args:
        client: MinIO client instance
        file_path: Local file path
        bucket: Target bucket name
        object_name: Object name in MinIO (defaults to filename with timestamp)
    
    Returns:
        MinIO object path (e.g., "raw/20260324/RLL25428006.pdf")
    """
    if not client:
        print("   ⚠️ MinIO not available, skipping upload")
        return None
    
    try:
        # Generate object name with date-based folder structure
        if not object_name:
            filename = Path(file_path).name
            date_prefix = datetime.now().strftime("%Y%m%d")
            object_name = f"{date_prefix}/{filename}"
        
        # Upload file
        client.fput_object(bucket, object_name, file_path)
        print(f"   ✓ Uploaded to MinIO: s3://{bucket}/{object_name}")
        
        return f"s3://{bucket}/{object_name}"
    
    except S3Error as e:
        print(f"⚠️ MinIO upload failed: {e}")
        return None


# ═══════════════════════════════════════════════════════════
#  FILE UTILITIES
# ═══════════════════════════════════════════════════════════

def calculate_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    """
    Calculate cryptographic hash of file for deduplication
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm (sha256, md5)
    
    Returns:
        Hash string prefixed with algorithm (e.g., "sha256:abc123...")
    """
    hash_obj = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        # Read file in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b''):
            hash_obj.update(chunk)
    
    return f"{algorithm}:{hash_obj.hexdigest()}"


# ═══════════════════════════════════════════════════════════
#  POSTGRESQL CONNECTION
# ═══════════════════════════════════════════════════════════

def get_db_connection():
    """Create PostgreSQL connection with error handling"""
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            cursor_factory=RealDictCursor
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"⚠️ PostgreSQL connection failed: {e}")
        print(f"   Host: {POSTGRES_HOST}:{POSTGRES_PORT}")
        print(f"   Database: {POSTGRES_DB}")
        print(f"   User: {POSTGRES_USER}")
        return None


# ═══════════════════════════════════════════════════════════
#  VALIDATION QUEUE FUNCTIONS
# ═══════════════════════════════════════════════════════════

def insert_to_metadata_datasets(
    conn,
    file_path: str,
    file_type: str,
    file_hash: str,
    minio_path: Optional[str],
    uploaded_by: Optional[int] = None
) -> Optional[uuid.UUID]:
    """
    Insert file metadata into metadata_datasets table
    
    Args:
        conn: PostgreSQL connection
        file_path: Original file path
        file_type: File extension (pdf, txt, jpg, etc.)
        file_hash: SHA-256 hash for deduplication
        minio_path: MinIO object path (s3://bucket/path)
        uploaded_by: User ID (optional - for future multi-user support)
    
    Returns:
        dataset_id (UUID) if successful, None if failed
    """
    if not conn:
        print("⚠️ No database connection available")
        return None
    
    try:
        cursor = conn.cursor()
        
        # Check if file already exists (deduplication)
        cursor.execute(
            "SELECT dataset_id FROM metadata_datasets WHERE file_hash = %s",
            (file_hash,)
        )
        existing = cursor.fetchone()
        
        if existing:
            print(f"   ⚠️ File already exists in database (dataset_id: {existing['dataset_id']})")
            print(f"      Skipping duplicate upload...")
            return existing['dataset_id']
        
        # Insert new record
        dataset_id = uuid.uuid4()
        cursor.execute("""
            INSERT INTO metadata_datasets (
                dataset_id,
                filename,
                file_type,
                file_hash,
                storage_path,
                uploaded_by,
                upload_date,
                status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING dataset_id
        """, (
            dataset_id,
            Path(file_path).name,
            file_type,
            file_hash,
            minio_path or file_path,
            uploaded_by,
            datetime.now(),
            'processing'  # Status: uploaded → processing → awaiting_validation → processed
        ))
        
        conn.commit()
        result = cursor.fetchone()
        print(f"   ✓ Inserted to metadata_datasets (dataset_id: {result['dataset_id']})")
        
        return result['dataset_id']
    
    except psycopg2.Error as e:
        print(f"⚠️ Database insert failed: {e}")
        conn.rollback()
        return None


def insert_to_validation_queue(
    conn,
    dataset_id: uuid.UUID,
    ocr_output: Dict[str, Any],
    stage: str = "ocr_complete"
) -> Optional[uuid.UUID]:
    """
    Insert OCR output into validation_queue for human review (CHECKPOINT 2)
    
    Args:
        conn: PostgreSQL connection
        dataset_id: Foreign key to metadata_datasets
        ocr_output: Complete OCR result (from ProcessingResult.to_postgres_json())
        stage: Validation stage ("ocr_complete", "needs_review", "approved")
    
    Returns:
        validation_id (UUID) if successful
    """
    if not conn:
        print("⚠️ No database connection available")
        return None
    
    try:
        cursor = conn.cursor()
        
        validation_id = uuid.uuid4()
        cursor.execute("""
            INSERT INTO validation_queue (
                validation_id,
                dataset_id,
                stage,
                status,
                validation_data,
                created_at
            ) VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING validation_id
        """, (
            validation_id,
            dataset_id,
            stage,
            'pending_review',  # Status: pending_review → in_review → approved → rejected
            Json(ocr_output),  # Store as JSONB
            datetime.now()
        ))
        
        conn.commit()
        result = cursor.fetchone()
        print(f"   ✓ Inserted to validation_queue (validation_id: {result['validation_id']})")
        print(f"      Stage: {stage}, Status: pending_review")
        print(f"      Entities: {len(ocr_output.get('medical_entities', []))}")
        print(f"      Confidence: {ocr_output['document']['confidence_score']*100:.1f}%")
        
        return result['validation_id']
    
    except psycopg2.Error as e:
        print(f"⚠️ Validation queue insert failed: {e}")
        conn.rollback()
        return None


def update_dataset_status(conn, dataset_id: uuid.UUID, status: str) -> bool:
    """
    Update metadata_datasets status
    
    Status flow: uploaded → processing → awaiting_validation → processed → failed
    """
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE metadata_datasets SET status = %s WHERE dataset_id = %s",
            (status, dataset_id)
        )
        conn.commit()
        print(f"   ✓ Updated dataset status: {status}")
        return True
    
    except psycopg2.Error as e:
        print(f"⚠️ Status update failed: {e}")
        conn.rollback()
        return False


# ═══════════════════════════════════════════════════════════
#  INTEGRATED PIPELINE FUNCTION
# ═══════════════════════════════════════════════════════════

def process_and_store_document(
    file_path: str,
    ocr_processor,  # UnstructuredDataProcessor instance
    uploaded_by: Optional[int] = None
) -> Dict[str, Any]:
    """
    Complete pipeline: Upload → OCR → Validation Queue
    
    This is the main integration function that combines:
    - MinIO storage (Layer 1)
    - OCR processing (Layer 2B)
    - Validation queue (Layer 3 - Checkpoint 2)
    
    Args:
        file_path: Path to PDF/TXT/Image file
        ocr_processor: UnstructuredDataProcessor instance
        uploaded_by: User ID (optional)
    
    Returns:
        Dict with: dataset_id, validation_id, minio_path, file_hash
    """
    
    print("\n" + "="*80)
    print(" INTEGRATED PIPELINE: UPLOAD → OCR → VALIDATION QUEUE")
    print("="*80 + "\n")
    
    result = {
        'success': False,
        'dataset_id': None,
        'validation_id': None,
        'minio_path': None,
        'file_hash': None,
        'entity_count': 0,
        'confidence': 0.0
    }
    
    # STEP 1: Calculate file hash
    print("📊 STEP 1: Calculating file hash...")
    file_hash = calculate_file_hash(file_path)
    result['file_hash'] = file_hash
    print(f"   ✓ Hash: {file_hash[:20]}...")
    
    # STEP 2: Upload to MinIO
    print("\n📦 STEP 2: Uploading to MinIO...")
    minio_client = get_minio_client()
    if minio_client:
        ensure_buckets_exist(minio_client)
        minio_path = upload_file_to_minio(minio_client, file_path, MINIO_BUCKET_RAW)
        result['minio_path'] = minio_path
    else:
        print("   ⚠️ MinIO not available, using local path")
        result['minio_path'] = file_path
    
    # STEP 3: Insert to metadata_datasets
    print("\n💾 STEP 3: Inserting to metadata_datasets...")
    db_conn = get_db_connection()
    if not db_conn:
        print("⚠️ Database not available - OCR results will be saved to JSON only")
        print("   You can manually insert into validation_queue later")
        return result
    
    file_type = Path(file_path).suffix.lstrip('.')
    dataset_id = insert_to_metadata_datasets(
        db_conn,
        file_path,
        file_type,
        file_hash,
        result['minio_path'],
        uploaded_by
    )
    
    if not dataset_id:
        print("⚠️ Failed to insert metadata - aborting pipeline")
        db_conn.close()
        return result
    
    result['dataset_id'] = dataset_id
    
    # STEP 4: Update status to "processing"
    update_dataset_status(db_conn, dataset_id, 'processing')
    
    # STEP 5: Run OCR + NER
    print("\n🔍 STEP 4: Running OCR + NER pipeline...")
    print("   (This may take 7-10 minutes for 6-page PDF)")
    
    try:
        # Process file with existing pipeline
        if file_path.lower().endswith('.pdf'):
            ocr_result = ocr_processor.process_pdf(file_path)
        elif file_path.lower().endswith('.txt'):
            ocr_result = ocr_processor.process_txt(file_path)
        else:
            print(f"⚠️ Unsupported file type: {file_type}")
            update_dataset_status(db_conn, dataset_id, 'failed')
            db_conn.close()
            return result
        
        # Convert to PostgreSQL JSON format
        postgres_json = ocr_result.to_postgres_json()
        result['entity_count'] = len(postgres_json.get('medical_entities', []))
        result['confidence'] = postgres_json['document']['confidence_score']
        
        print(f"   ✓ OCR complete: {result['entity_count']} entities, {result['confidence']*100:.1f}% confidence")
    
    except Exception as e:
        print(f"❌ OCR processing failed: {e}")
        update_dataset_status(db_conn, dataset_id, 'failed')
        db_conn.close()
        return result
    
    # STEP 6: Insert to validation_queue
    print("\n📋 STEP 5: Inserting to validation_queue...")
    validation_id = insert_to_validation_queue(
        db_conn,
        dataset_id,
        postgres_json,
        stage='ocr_complete'
    )
    
    if not validation_id:
        print("⚠️ Failed to insert validation queue")
        update_dataset_status(db_conn, dataset_id, 'failed')
        db_conn.close()
        return result
    
    result['validation_id'] = validation_id
    
    # STEP 7: Update status to "awaiting_validation"
    update_dataset_status(db_conn, dataset_id, 'awaiting_validation')
    
    # STEP 8: Log to audit_trail
    try:
        cursor = db_conn.cursor()
        cursor.execute("""
            INSERT INTO audit_trail (
                trail_id,
                dataset_id,
                action,
                performed_by,
                timestamp,
                details
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            uuid.uuid4(),
            dataset_id,
            'ocr_completed',
            uploaded_by,
            datetime.now(),
            Json({
                'entity_count': result['entity_count'],
                'confidence': result['confidence'],
                'file_hash': file_hash,
                'minio_path': result['minio_path']
            })
        ))
        db_conn.commit()
        print("   ✓ Logged to audit_trail")
    except psycopg2.Error as e:
        print(f"⚠️ Audit trail logging failed: {e}")
    
    db_conn.close()
    
    result['success'] = True
    
    print("\n" + "="*80)
    print(" ✅ PIPELINE COMPLETE")
    print("="*80)
    print(f" • Dataset ID: {result['dataset_id']}")
    print(f" • Validation ID: {result['validation_id']}")
    print(f" • MinIO Path: {result['minio_path']}")
    print(f" • File Hash: {file_hash[:40]}...")
    print(f" • Entities: {result['entity_count']}")
    print(f" • Confidence: {result['confidence']*100:.1f}%")
    print(f" • Status: awaiting_validation (CHECKPOINT 2)")
    print("="*80 + "\n")
    
    return result


# ═══════════════════════════════════════════════════════════
#  CHECKPOINT 2: OCR OUTPUT REVIEW (API ENDPOINT)
# ═══════════════════════════════════════════════════════════

def get_pending_validations(conn, limit: int = 10) -> List[Dict]:
    """
    Get pending validation queue items for human review
    
    Returns:
        List of validation records with OCR output
    """
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                v.validation_id,
                v.dataset_id,
                v.stage,
                v.status,
                v.validation_data,
                v.created_at,
                m.filename,
                m.file_type,
                m.storage_path
            FROM validation_queue v
            JOIN metadata_datasets m ON v.dataset_id = m.dataset_id
            WHERE v.status = 'pending_review'
            ORDER BY v.created_at ASC
            LIMIT %s
        """, (limit,))
        
        return cursor.fetchall()
    
    except psycopg2.Error as e:
        print(f"⚠️ Query failed: {e}")
        return []


def approve_validation(
    conn,
    validation_id: uuid.UUID,
    approved_by: Optional[int] = None,
    edits: Optional[Dict] = None
) -> bool:
    """
    Approve validation queue item (CHECKPOINT 2: User clicks APPROVE ✅)
    
    Args:
        conn: PostgreSQL connection
        validation_id: Validation record ID
        approved_by: User ID
        edits: Optional manual corrections to validation_data
    
    Returns:
        True if successful
    """
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Apply edits if provided
        if edits:
            cursor.execute("""
                UPDATE validation_queue
                SET validation_data = validation_data || %s::jsonb
                WHERE validation_id = %s
            """, (Json(edits), validation_id))
        
        # Update status to approved
        cursor.execute("""
            UPDATE validation_queue
            SET status = 'approved',
                reviewed_by = %s,
                reviewed_at = %s
            WHERE validation_id = %s
        """, (approved_by, datetime.now(), validation_id))
        
        # Get dataset_id to update metadata_datasets
        cursor.execute(
            "SELECT dataset_id FROM validation_queue WHERE validation_id = %s",
            (validation_id,)
        )
        dataset = cursor.fetchone()
        
        if dataset:
            cursor.execute("""
                UPDATE metadata_datasets
                SET status = 'approved',
                    processed_date = %s
                WHERE dataset_id = %s
            """, (datetime.now(), dataset['dataset_id']))
        
        # Log to audit_trail
        cursor.execute("""
            INSERT INTO audit_trail (
                trail_id,
                dataset_id,
                action,
                performed_by,
                timestamp,
                details
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            uuid.uuid4(),
            dataset['dataset_id'],
            'validation_approved',
            approved_by,
            datetime.now(),
            Json({'validation_id': str(validation_id), 'edits_applied': bool(edits)})
        ))
        
        conn.commit()
        print(f"   ✓ Validation approved (validation_id: {validation_id})")
        return True
    
    except psycopg2.Error as e:
        print(f"⚠️ Approval failed: {e}")
        conn.rollback()
        return False


def reject_validation(
    conn,
    validation_id: uuid.UUID,
    rejected_by: Optional[int] = None,
    reason: Optional[str] = None
) -> bool:
    """
    Reject validation queue item (CHECKPOINT 2: User clicks REJECT ❌)
    
    This triggers a re-run of OCR or moves to manual data entry
    """
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE validation_queue
            SET status = 'rejected',
                reviewed_by = %s,
                reviewed_at = %s,
                rejection_reason = %s
            WHERE validation_id = %s
        """, (rejected_by, datetime.now(), reason, validation_id))
        
        # Get dataset_id
        cursor.execute(
            "SELECT dataset_id FROM validation_queue WHERE validation_id = %s",
            (validation_id,)
        )
        dataset = cursor.fetchone()
        
        if dataset:
            cursor.execute("""
                UPDATE metadata_datasets
                SET status = 'needs_review'
                WHERE dataset_id = %s
            """, (dataset['dataset_id'],))
            
            # Log rejection
            cursor.execute("""
                INSERT INTO audit_trail (
                    trail_id,
                    dataset_id,
                    action,
                    performed_by,
                    timestamp,
                    details
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                uuid.uuid4(),
                dataset['dataset_id'],
                'validation_rejected',
                rejected_by,
                datetime.now(),
                Json({'validation_id': str(validation_id), 'reason': reason})
            ))
        
        conn.commit()
        print(f"   ✓ Validation rejected (validation_id: {validation_id})")
        print(f"      Reason: {reason}")
        return True
    
    except psycopg2.Error as e:
        print(f"⚠️ Rejection failed: {e}")
        conn.rollback()
        return False


# ═══════════════════════════════════════════════════════════
#  EXAMPLE USAGE
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║      Validation Queue Integration - Configuration Check           ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    print("📋 Configuration:")
    print(f"   • MinIO: {MINIO_ENDPOINT} (secure: {MINIO_SECURE})")
    print(f"   • Bucket Raw: {MINIO_BUCKET_RAW}")
    print(f"   • PostgreSQL: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
    print(f"   • User: {POSTGRES_USER}\n")
    
    # Test connections
    print("🔌 Testing connections...\n")
    
    # Test MinIO
    minio_client = get_minio_client()
    if minio_client:
        print("   ✅ MinIO: Connected")
        ensure_buckets_exist(minio_client)
    else:
        print("   ❌ MinIO: Not available (will use local filesystem)")
    
    # Test PostgreSQL
    db_conn = get_db_connection()
    if db_conn:
        print("   ✅ PostgreSQL: Connected")
        
        # Check required tables exist
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('metadata_datasets', 'validation_queue', 'audit_trail')
        """)
        tables = [row['table_name'] for row in cursor.fetchall()]
        
        for table in ['metadata_datasets', 'validation_queue', 'audit_trail']:
            if table in tables:
                print(f"      ✓ Table exists: {table}")
            else:
                print(f"      ❌ Table missing: {table}")
        
        db_conn.close()
    else:
        print("   ❌ PostgreSQL: Not available")
    
    print("\n" + "="*80)
    print(" Integration Ready!")
    print(" Use: from validation_queue_integration import process_and_store_document")
    print("="*80 + "\n")
