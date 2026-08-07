"""
Unstructured Data Pipeline Service - Production Implementation
=================================================================
Flow: Upload → MinIO [usm-raw] → OCR [Qwen3-VL-2B-Instruct] → NER → Preview → Validation Queue

Features:
- PDF/TXT/Image processing
- MinIO object storage
- GPU-accelerated OCR with Qwen3-VL-2B-Instruct
- Medical entity extraction (NER)
- Quality validation
- PostgreSQL integration

Author: Syarifah Fajriyah
Date: April 3, 2026
"""

import os
import re
import json
import time
import hashlib
import traceback
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict

# MinIO
from minio import Minio
from minio.error import S3Error

# Database
from sqlalchemy.orm import Session
from sqlalchemy import text

# ML/OCR
import torch
from transformers import Qwen3VLProcessor, Qwen3VLForConditionalGeneration
from PIL import Image

# PDF Processing
try:
    import fitz  # PyMuPDF
    from pdf2image import convert_from_bytes
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# Enhanced NER (ported from tested standalone pipeline)
from app.services.enhanced_ner import (
    extract_medical_entities_comprehensive,
    parse_metadata_from_text,
    extract_section_structure,
    parse_table_structure_from_text  # NEW: Stage 2 structure parser
)


# ═══════════════════════════════════════════════════════════
#  DATA STRUCTURES
# ═══════════════════════════════════════════════════════════

@dataclass
class ProcessingResult:
    """OCR + NER result structure"""
    filename: str
    file_type: str
    status: str  # success, failed, needs_review
    extracted_text: str
    confidence: float
    page_count: int
    medical_entities: List[Dict]
    processing_time: float
    vram_used_mb: float
    metadata: Optional[Dict[str, Any]] = None
    sections: Optional[List[Dict]] = None
    structured_tests: Optional[List[Dict]] = None  # NEW: Table structure preservation
    source_path: Optional[str] = None
    file_hash: Optional[str] = None
    ocr_engine: Optional[str] = None
    error: Optional[str] = None
    
    def to_postgres_json(self) -> Dict:
        """Format for validation_queue.validation_data JSONB"""
        return {
            "document": {
                "filename": self.filename,
                "file_type": self.file_type,
                "source_path": self.source_path,
                "file_hash": self.file_hash,
                "page_count": self.page_count,
                "confidence_score": self.confidence,
                "status": self.status,
                "processing_time_s": self.processing_time,
                "vram_used_mb": self.vram_used_mb,
                "ocr_engine": self.ocr_engine or "Qwen3-VL-2B-Instruct"
            },
            "metadata": self.metadata or {},
            "extracted_text": self.extracted_text,
            "medical_entities": self.medical_entities or [],
            "structured_tests": self.structured_tests or [],  # NEW: Include table structure
            "sections": self.sections or [],
            "processing_metadata": {
                "pipeline_version": "2.0.0",
                "timestamp": datetime.now().isoformat(),
                "gpu_device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
            }
        }


# ═══════════════════════════════════════════════════════════
#  MINIO CLIENT
# ═══════════════════════════════════════════════════════════

class MinIOClient:
    """MinIO object storage client"""
    
    def __init__(self):
        self.endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
        
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure
        )
        
        self.bucket_name = "usm-raw"
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Create bucket if not exists"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                print(f"✅ Created MinIO bucket: {self.bucket_name}")
        except S3Error as e:
            print(f"⚠️ MinIO bucket error: {e}")
    
    def upload_file(self, file_data: bytes, file_name: str, content_type: str = "application/octet-stream") -> str:
        """Upload file to MinIO, returns object path"""
        date_path = datetime.now().strftime("%Y/%m/%d")
        object_name = f"{date_path}/{file_name}"
        
        try:
            self.client.put_object(
                self.bucket_name,
                object_name,
                data=BytesIO(file_data),
                length=len(file_data),
                content_type=content_type
            )
            return f"{self.bucket_name}/{object_name}"
        except S3Error as e:
            raise Exception(f"MinIO upload failed: {e}")
    
    def get_file(self, object_path: str) -> bytes:
        """Retrieve file from MinIO"""
        # object_path format: "usm-raw/2026/04/03/file.pdf"
        parts = object_path.split('/', 1)
        bucket = parts[0]
        object_name = parts[1] if len(parts) > 1 else object_path
        
        try:
            response = self.client.get_object(bucket, object_name)
            return response.read()
        except S3Error as e:
            raise Exception(f"MinIO download failed: {e}")


# ═══════════════════════════════════════════════════════════
#  QWEN3-VL-2B-INSTRUCT ENGINE
# ═══════════════════════════════════════════════════════════

class Qwen3VLEngine:
    """Qwen3-VL-2B-Instruct for medical OCR"""
    
    def __init__(self):
        self.model_name = "Qwen/Qwen3-VL-2B-Instruct"
        self.model_display_name = "Qwen3-VL-2B-Instruct"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        print(f"\nLoading {self.model_display_name}...")
        print(f"   Device: {self.device}")
        
        try:
            # Load processor
            self.processor = Qwen3VLProcessor.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                cache_dir=os.getenv("HF_CACHE_DIR", "./models/cache")
            )
            
            # Load model with INT8 quantization for speed
            from transformers import BitsAndBytesConfig
            
            quantization_config = BitsAndBytesConfig(
                load_in_8bit=True,
                bnb_8bit_compute_dtype=torch.float16
            )
            
            self.model = Qwen3VLForConditionalGeneration.from_pretrained(
                self.model_name,
                device_map="auto",
                trust_remote_code=True,
                quantization_config=quantization_config,
                cache_dir=os.getenv("HF_CACHE_DIR", "./models/cache")
            )
            
            # Set to eval mode for inference (disables dropout, etc.)
            self.model.eval()
            
            print(f"   ✅ Model loaded on {self.device}")
            print(f"   ⚡ Optimizations: INT8 quantization, eval mode, reduced tokens")
            print(f"   🎯 Target: ~20s/page (down from ~37s baseline)\\n")
            
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            raise
    
    def extract_from_image(self, image_path: str) -> Dict[str, Any]:
        """Extract text from image using Qwen3-VL-2B"""
        try:
            with torch.no_grad():  # Disable gradient computation for inference (faster)
                messages = [
                    {
                        "role": "system",
                        "content": "You are a medical document OCR system. Extract ALL text from the image exactly as it appears, line by line. Include Chinese characters if present. Output only the extracted text."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "image", "image": image_path},
                            {"type": "text", "text": "Extract all text from this medical document."}
                        ]
                    }
                ]
                
                # Process — limit max_pixels so the vision encoder handles fewer patches.
                # 256*28*28 ≈ 200k pixels caps the image resolution fed to the model.
                # The Qwen3-VL processor rescales internally; this alone can halve
                # the number of visual tokens and cut inference time by ~30-40%.
                text_prompt = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                inputs = self.processor(
                    text=[text_prompt],
                    images=[Image.open(image_path)],
                    return_tensors="pt",
                    padding=True,
                    max_pixels=256 * 28 * 28,  # ~200k px cap (Qwen3-VL default is 1280*28*28)
                )
                
                # Move to device
                inputs_on_device = {k: v.to(self.device) if isinstance(v, torch.Tensor) else v for k, v in inputs.items()}
                
                # Generate (OPTIMIZED for ~20s/page target)
                output_ids = self.model.generate(
                    **inputs_on_device,
                    max_new_tokens=400,  # CBC report text ≈ 150-300 tokens/page
                    min_new_tokens=30,   # Prevent premature stopping
                    do_sample=False,     # Greedy decoding (fastest)
                    use_cache=True,      # Enable KV cache
                    num_beams=1,         # No beam search (faster)
                    pad_token_id=self.processor.tokenizer.eos_token_id
                )
                
                # Decode ONLY the newly generated tokens (exclude the input prompt)
                # Without this slice, batch_decode returns the full conversation including
                # the system/user prompt, which breaks all downstream NER patterns.
                input_len = inputs_on_device["input_ids"].shape[1]
                new_tokens = output_ids[:, input_len:]
                
                # Decode
                response = self.processor.batch_decode(
                    new_tokens,
                    skip_special_tokens=True,
                    clean_up_tokenization_spaces=True
                )[0].strip()
                
                # Extract medical entities using comprehensive NER
                entities = extract_medical_entities_comprehensive(response)
                
                # Extract metadata
                metadata = parse_metadata_from_text(response)
                
                # Extract sections
                sections = extract_section_structure(response)
                
                return {
                    "extracted_text": response,
                    "medical_entities": entities,
                    "metadata": metadata,
                    "sections": sections,
                    "confidence": 0.85,
                    "entity_count": len(entities)
                }
            
        except Exception as e:
            print(f"❌ OCR error: {e}")
            return {
                "extracted_text": "",
                "medical_entities": [],
                "metadata": {},
                "sections": [],
                "confidence": 0.0,
                "entity_count": 0,
                "error": str(e)
            }
    
    def _extract_entities_regex(self, text: str) -> List[Dict[str, Any]]:
        """Use comprehensive NER from enhanced_ner module"""
        return extract_medical_entities_comprehensive(text)


# ═══════════════════════════════════════════════════════════
#  DOCUMENT PROCESSOR
# ═══════════════════════════════════════════════════════════

class DocumentProcessor:
    """Process PDF/TXT/Image files"""
    
    def __init__(self, vision_engine: Qwen3VLEngine):
        self.vision_engine = vision_engine
    
    def process_file(self, file_data: bytes, filename: str, file_type: str, source_path: str) -> ProcessingResult:
        """Process any file type"""
        start_time = time.time()
        file_hash = hashlib.sha256(file_data).hexdigest()
        
        print(f"\n Processing {file_type}: {filename}")
        
        try:
            if file_type == "pdf":
                return self._process_pdf(file_data, filename, source_path, file_hash, start_time)
            elif file_type == "txt":
                return self._process_txt(file_data, filename, source_path, file_hash, start_time)
            elif file_type in ["png", "jpg", "jpeg"]:
                return self._process_image(file_data, filename, source_path, file_hash, start_time)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
                
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            print(f"   ❌ Processing error: {error_msg}")
            traceback.print_exc()  # Print full traceback for debugging
            return ProcessingResult(
                filename=filename,
                file_type=file_type,
                status="failed",
                extracted_text="",
                confidence=0.0,
                page_count=0,
                medical_entities=[],
                source_path=source_path,
                file_hash=file_hash,
                ocr_engine="Qwen3-VL-2B-Instruct",
                processing_time=processing_time,
                vram_used_mb=0.0,
                error=error_msg
            )
    
    def _process_pdf(self, file_data: bytes, filename: str, source_path: str, file_hash: str, start_time: float) -> ProcessingResult:
        """Process PDF with OCR"""
        if not PDF_AVAILABLE:
            raise Exception("PDF libraries not available")
        
        # Convert PDF to images
        # DPI=120: A4 → ~992×1403px (vs 1654×2338px at default DPI=200).
        # 3.6× fewer pixels → ~2× faster vision token encoding without
        # losing readability on printed lab reports.
        images = convert_from_bytes(file_data, dpi=120)
        page_count = len(images)
        
        print(f"   Converting {page_count} pages to images...")
        
        # Save temp images and process with enhanced logging
        all_text = []
        all_entities = []
        all_metadata = {}
        all_sections = []
        temp_dir = Path("./temp_ocr")
        temp_dir.mkdir(exist_ok=True)
        
        for idx, image in enumerate(images, 1):
            temp_path = temp_dir / f"page_{idx}.png"
            image.save(temp_path)
            
            print(f"   OCR Page {idx}/{page_count}...", end='', flush=True)
            page_start = time.time()
            
            result = self.vision_engine.extract_from_image(str(temp_path))
            
            page_time = time.time() - page_start
            entity_count = len(result.get('medical_entities', []))
            
            print(f" ✓ ({page_time:.1f}s, {entity_count} entities)")
            
            all_text.append(result['extracted_text'])
            all_entities.extend(result.get('medical_entities', []))
            
            # Merge metadata (first page wins for most fields)
            if idx == 1:
                all_metadata = result.get('metadata', {})
            
            # Cleanup
            temp_path.unlink()
        
        combined_text = "\n\n--- PAGE BREAK ---\n\n".join(all_text)
        
        # STAGE 2: Parse table structure (NEW - preserves table layout)
        structured_data = parse_table_structure_from_text(combined_text)
        
        # Extract metadata and sections from combined text
        final_metadata = parse_metadata_from_text(combined_text)
        final_sections = extract_section_structure(combined_text)
        
        # Merge with page 1 metadata
        final_metadata.update(all_metadata)
        
        processing_time = time.time() - start_time
        
        return ProcessingResult(
            filename=filename,
            file_type="pdf",
            status="success",
            extracted_text=combined_text,
            confidence=0.85,
            page_count=page_count,
            medical_entities=all_entities,
            structured_tests=structured_data.get('tests', []),  # NEW: Structured test rows
            source_path=source_path,
            file_hash=file_hash,
            ocr_engine="Qwen3-VL-2B-Instruct",
            processing_time=processing_time,
            vram_used_mb=torch.cuda.memory_allocated(0) / (1024**2) if torch.cuda.is_available() else 0.0,
            metadata=final_metadata,
            sections=final_sections
        )
    
    def _process_txt(self, file_data: bytes, filename: str, source_path: str, file_hash: str, start_time: float) -> ProcessingResult:
        """Process text file with enhanced NER"""
        text = file_data.decode('utf-8')
        
        # STAGE 1: Extract entities using comprehensive NER (backward compatibility)
        entities = extract_medical_entities_comprehensive(text)
        
        # STAGE 2: Parse table structure (NEW - preserves table layout)
        structured_data = parse_table_structure_from_text(text)
        
        # Extract metadata and sections
        metadata = parse_metadata_from_text(text)
        sections = extract_section_structure(text)
        
        processing_time = time.time() - start_time
        
        return ProcessingResult(
            filename=filename,
            file_type="txt",
            status="success",
            extracted_text=text,
            confidence=1.0,
            page_count=1,
            medical_entities=entities,
            structured_tests=structured_data.get('tests', []),  # NEW: Structured test rows
            source_path=source_path,
            file_hash=file_hash,
            ocr_engine="Direct",
            processing_time=processing_time,
            vram_used_mb=0.0,
            metadata=metadata,
            sections=sections
        )
    
    def _process_image(self, file_data: bytes, filename: str, source_path: str, file_hash: str, start_time: float) -> ProcessingResult:
        """Process image file"""
        temp_dir = Path("./temp_ocr")
        temp_dir.mkdir(exist_ok=True)
        temp_path = temp_dir / filename
        
        with open(temp_path, 'wb') as f:
            f.write(file_data)
        
        # STAGE 1: OCR extraction
        result = self.vision_engine.extract_from_image(str(temp_path))
        temp_path.unlink()
        
        # STAGE 2: Parse table structure from extracted text
        extracted_text = result['extracted_text']
        structured_data = parse_table_structure_from_text(extracted_text)
        
        processing_time = time.time() - start_time
        
        return ProcessingResult(
            filename=filename,
            file_type="image",
            status="success",
            extracted_text=extracted_text,
            confidence=result['confidence'],
            page_count=1,
            medical_entities=result['medical_entities'],
            structured_tests=structured_data.get('tests', []),  # NEW: Structured test rows
            source_path=source_path,
            file_hash=file_hash,
            ocr_engine="Qwen3-VL-2B-Instruct",
            processing_time=processing_time,
            vram_used_mb=torch.cuda.memory_allocated(0) / (1024**2) if torch.cuda.is_available() else 0.0,
            metadata=result.get('metadata', {}),
            sections=result.get('sections', [])
        )


# ═══════════════════════════════════════════════════════════
#  MAIN SERVICE
# ═══════════════════════════════════════════════════════════

class UnstructuredPipelineService:
    """Main pipeline orchestrator"""
    
    def __init__(self, db: Session):
        self.db = db
        self.minio_client = MinIOClient()
        self.vision_engine = None  # Lazy load
        self.processor = None
    
    def _init_ml_engine(self):
        """Lazy load ML engine (heavy)"""
        if self.vision_engine is None:
            print("Initializing Qwen3-VL-2B-Instruct engine...")
            self.vision_engine = Qwen3VLEngine()
            self.processor = DocumentProcessor(self.vision_engine)
    
    def upload_and_process(self, file_data: bytes, filename: str, file_type: str, user_id: int) -> Dict:
        """
        Complete pipeline:
        1. Upload to MinIO [usm-raw]
        2. OCR with Qwen3-VL-2B-Instruct
        3. NER extraction
        4. Save to validation_queue
        """
        try:
            # Step 1: Upload to MinIO
            print(f"\n[1/4] Uploading to MinIO...")
            object_path = self.minio_client.upload_file(file_data, filename, content_type=f"application/{file_type}")
            print(f"   ✓ Saved to: {object_path}")
            
            # Step 2: Initialize ML engine
            print(f"\n[2/4] Initializing OCR engine...")
            self._init_ml_engine()
            
            # Step 3: Process file (OCR + NER)
            print(f"\n[3/4] Running OCR + NER...")
            result = self.processor.process_file(file_data, filename, file_type, object_path)
            
            print(f"\n   Status: {result.status}")
            print(f"   Extracted: {len(result.extracted_text)} characters")
            print(f"   Entities: {len(result.medical_entities)} found")
            if result.structured_tests:
                print(f"   Structured Tests: {len(result.structured_tests)} test rows (table preserved!)")
            print(f"   Time: {result.processing_time:.2f}s")
            if result.status == "failed" and hasattr(result, 'error'):
                print(f"   ❌ Error: {result.error}")
            
            # Step 4: Save to validation queue
            print(f"\n[4/4] Saving to validation queue...")
            validation_id = self._save_to_validation_queue(result, user_id)
            print(f"   ✓ Validation ID: {validation_id}")
            
            response = {
                "success": True,
                "validation_id": validation_id,
                "filename": filename,
                "minio_path": object_path,
                "extracted_text": result.extracted_text,
                "medical_entities": result.medical_entities,
                "structured_tests": result.structured_tests or [],  # NEW: Include structured table rows
                "metadata": result.metadata or {},  # NEW: Include metadata
                "status": result.status,
                "processing_time": result.processing_time,
                "page_count": result.page_count,
                "confidence": result.confidence
            }
            
            # Add error if processing failed
            if result.status == "failed" and hasattr(result, 'error'):
                response["error"] = result.error
            
            return response
            
        except Exception as e:
            print(f"\n❌ Pipeline failed: {e}")
            traceback.print_exc()
            raise
    
    def _save_to_validation_queue(self, result: ProcessingResult, user_id: int) -> int:
        """Save processing result to unstructured_document_processed table (100% flexible JSONB storage)"""
        try:
            validation_data = result.to_postgres_json()
            
            # Generate unique record_id (NO assumptions about document fields)
            import uuid
            record_id = str(uuid.uuid4())
            
            query = text("""
                INSERT INTO unstructured_document_processed (
                    extracted_record_id, document_filename, dataset_type, extracted_data, 
                    ocr_engine, processing_version, import_batch_id
                ) VALUES (
                    :extracted_record_id, :document_filename, :dataset_type, 
                    CAST(:extracted_data AS jsonb), :ocr_engine, :processing_version, :batch_id
                )
                RETURNING id
            """)
            
            result_proxy = self.db.execute(
                query,
                {
                    "extracted_record_id": record_id,  # Pure UUID, NO field assumptions
                    "document_filename": result.filename,
                    "dataset_type": result.file_type,  # Just 'pdf', 'txt', 'jpg'
                    "extracted_data": json.dumps(validation_data),  # Pure JSONB, NO structure enforced
                    "ocr_engine": "Qwen3-VL-2B-Instruct",
                    "processing_version": "2.0.0",
                    "batch_id": str(uuid.uuid4())
                }
            )
            validation_id = result_proxy.fetchone()[0]
            self.db.commit()
            
            return validation_id
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to save OCR result: {e}")
    
    def get_preview(self, validation_id: int) -> Dict:
        """Get preview of processed data"""
        try:
            query = text("""
                SELECT id, stage, status, validation_data, created_at
                FROM validation_queue
                WHERE id = :validation_id
            """)
            
            result = self.db.execute(query, {"validation_id": validation_id}).fetchone()
            
            if not result:
                raise Exception(f"Validation ID {validation_id} not found")
            
            return {
                "validation_id": result[0],
                "stage": result[1],
                "status": result[2],
                "data": result[3],
                "created_at": result[4].isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Failed to get preview: {e}")
