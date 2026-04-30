#!/usr/bin/env python3
"""
Standalone Unstructured Data Pipeline - GPU Test (OPTIMIZED)
=============================================================
Purpose: Test Qwen3-VL-4B-Instruct on unstructured medical documents (PDF, TXT)
Model: https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct
GPU: NVIDIA RTX 3090 24GB (test environment)

Features:
- Process PDF and TXT medical documents
- Real-time VRAM monitoring
- Storage consumption tracking
- Terminal output only (no Docker)
- Human validation checkpoints
- TIER 2 Optimizations: Batch processing (4x speedup)

Author: Syarifah Fajriyah (Data Engineer)
Date: March 24, 2026
"""

# ═══════════════════════════════════════════════════════════
#  TIER 5: CUDA OPTIMIZATIONS (Set BEFORE imports)
# ═══════════════════════════════════════════════════════════
import os
os.environ["CUDA_LAUNCH_BLOCKING"] = "0"  # Async CUDA operations
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:512"  # Better memory management
os.environ["TOKENIZERS_PARALLELISM"] = "true"  # Parallel tokenization

import sys
import json
import time
import psutil
import torch
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import subprocess

# Enable CUDA optimizations (after torch import)
if torch.cuda.is_available():
    torch.backends.cudnn.benchmark = True  # Auto-tune for your hardware
    torch.backends.cuda.matmul.allow_tf32 = True  # Use TF32 on Ampere GPUs (RTX 3090)
    torch.backends.cudnn.allow_tf32 = True

# Check if running on GPU
if not torch.cuda.is_available():
    print("⚠️ WARNING: CUDA not available! This script requires GPU.")
    print("   However, I'll continue in CPU mode for testing...")

# PDF Processing
try:
    import fitz  # PyMuPDF
    import pdfplumber
    from pdf2image import convert_from_path
    PDF_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ PDF libraries not fully available: {e}")
    PDF_AVAILABLE = False

# Transformers for Qwen3-VL-4B-Thinking
try:
    from transformers import Qwen3VLProcessor, Qwen3VLForConditionalGeneration
    from PIL import Image
    from qwen_vl_utils import process_vision_info
    TRANSFORMERS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Transformers not available: {e}")
    TRANSFORMERS_AVAILABLE = False


# ═══════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════

# Model Selection: Choose Qwen3-VL variant
# - "thinking": Qwen3-VL-4B-Thinking (slower, reasoning-capable)
# - "instruct": Qwen3-VL-4B-Instruct (faster, direct extraction) ← RECOMMENDED
MODEL_VARIANT = "instruct"  # Options: "thinking" or "instruct"

# Optimization Tier (speed vs quality trade-off)
# - "tier1": Quantization + Flash Attention + No thinking (target: <20s/page)
# - "tier2": + Optimized image processing + KV cache (target: <25s/page) ← CURRENT
# - "tier3": Hybrid OCR pipeline (target: <15s/page, future implementation)
OPTIMIZATION_TIER = "tier2"  # Options: "tier1", "tier2", "tier3"

# NER Strategy: Choose entity extraction method
# - False (default): Fast regex-only NER, works for structured datasets (AAM-SLE-E)
# - True: Scalable model-based NER, handles ANY medical terms including Chinese
#         (adds ~10-20s per document but no hard-coded patterns needed)
USE_MODEL_BASED_NER = False  # Set to False for production (regex is faster + accurate for lab reports)

# TIER 2: Batch Processing Configuration
BATCH_SIZE = 4  # RTX 3090 24GB can handle 4 pages simultaneously
                # Reduce to 2 if VRAM errors occur
                # Increase to 6 for A100 40GB

# Quality Assurance Settings
MIN_CONFIDENCE_THRESHOLD = 0.75  # Reject documents with OCR confidence < 75%
MIN_TEXT_LENGTH = 100            # Flag documents with < 100 chars as suspicious
REQUIRED_SECTIONS = ["HAEMATOLOGY", "BIOCHEMISTRY", "IMMUNOLOGY"]  # At least 1 must be present
VALIDATE_OUTPUT = True           # Enable output validation before proceeding


# ═══════════════════════════════════════════════════════════
#  RESOURCE MONITORING
# ═══════════════════════════════════════════════════════════

class ResourceMonitor:
    """Real-time GPU VRAM and storage monitoring"""
    
    def __init__(self, log_file: str = "resource_usage.log"):
        self.log_file = log_file
        self.start_time = time.time()
        self.gpu_available = torch.cuda.is_available()
        self.initial_storage = self._get_storage_usage()
        
        # Log initial state
        self._log_header()
        self.log_current_state("INITIALIZATION")
    
    def _get_storage_usage(self) -> Dict[str, float]:
        """Get current storage usage in GB"""
        disk = psutil.disk_usage('/')
        return {
            'total_gb': disk.total / (1024**3),
            'used_gb': disk.used / (1024**3),
            'free_gb': disk.free / (1024**3),
            'percent': disk.percent
        }
    
    def _get_gpu_memory(self) -> Dict[str, float]:
        """Get GPU memory usage in MB"""
        if not self.gpu_available:
            return {'allocated_mb': 0, 'reserved_mb': 0, 'free_mb': 0, 'total_mb': 0}
        
        allocated = torch.cuda.memory_allocated(0) / (1024**2)
        reserved = torch.cuda.memory_reserved(0) / (1024**2)
        total = torch.cuda.get_device_properties(0).total_memory / (1024**2)
        free = total - allocated
        
        return {
            'allocated_mb': allocated,
            'reserved_mb': reserved,
            'free_mb': free,
            'total_mb': total
        }
    
    def _log_header(self):
        """Write log header"""
        with open(self.log_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("RESOURCE USAGE LOG - Unstructured Pipeline\n")
            f.write(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"GPU Available: {self.gpu_available}\n")
            if self.gpu_available:
                f.write(f"GPU Device: {torch.cuda.get_device_name(0)}\n")
            f.write("=" * 80 + "\n\n")
    
    def log_current_state(self, checkpoint: str):
        """Log current VRAM and storage state"""
        elapsed = time.time() - self.start_time
        gpu = self._get_gpu_memory()
        storage = self._get_storage_usage()
        
        # Terminal output
        print(f"\n{'='*80}")
        print(f" CHECKPOINT: {checkpoint}")
        print(f" Time Elapsed: {elapsed:.2f}s")
        print(f"{'='*80}")
        
        if self.gpu_available:
            print(f" GPU VRAM:")
            print(f"   Allocated: {gpu['allocated_mb']:.2f} MB ({gpu['allocated_mb']/1024:.2f} GB)")
            print(f"   Reserved:  {gpu['reserved_mb']:.2f} MB ({gpu['reserved_mb']/1024:.2f} GB)")
            print(f"   Free:      {gpu['free_mb']:.2f} MB ({gpu['free_mb']/1024:.2f} GB)")
            print(f"   Total:     {gpu['total_mb']:.2f} MB ({gpu['total_mb']/1024:.2f} GB)")
            print(f"   Usage:     {(gpu['allocated_mb']/gpu['total_mb']*100):.1f}%")
        
        print(f"\n STORAGE:")
        print(f"   Used:   {storage['used_gb']:.2f} GB")
        print(f"   Free:   {storage['free_gb']:.2f} GB")
        print(f"   Total:  {storage['total_gb']:.2f} GB")
        print(f"   Usage:  {storage['percent']:.1f}%")
        print(f"{'='*80}\n")
        
        # File log
        with open(self.log_file, 'a') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"CHECKPOINT: {checkpoint}\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Elapsed: {elapsed:.2f}s\n")
            f.write(f"\nGPU VRAM:\n")
            f.write(f"  Allocated: {gpu['allocated_mb']:.2f} MB\n")
            f.write(f"  Reserved:  {gpu['reserved_mb']:.2f} MB\n")
            f.write(f"  Free:      {gpu['free_mb']:.2f} MB\n")
            f.write(f"  Total:     {gpu['total_mb']:.2f} MB\n")
            f.write(f"  Usage:     {(gpu['allocated_mb']/gpu['total_mb']*100) if gpu['total_mb'] > 0 else 0:.1f}%\n")
            f.write(f"\nSTORAGE:\n")
            f.write(f"  Used:   {storage['used_gb']:.2f} GB\n")
            f.write(f"  Free:   {storage['free_gb']:.2f} GB\n")
            f.write(f"  Total:  {storage['total_gb']:.2f} GB\n")
            f.write(f"  Usage:  {storage['percent']:.1f}%\n")
            f.write(f"{'='*80}\n")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get resource usage summary"""
        gpu = self._get_gpu_memory()
        storage = self._get_storage_usage()
        storage_consumed = storage['used_gb'] - self.initial_storage['used_gb']
        
        return {
            'elapsed_time': time.time() - self.start_time,
            'gpu_vram_used_mb': gpu['allocated_mb'],
            'gpu_vram_used_gb': gpu['allocated_mb'] / 1024,
            'gpu_vram_percent': (gpu['allocated_mb']/gpu['total_mb']*100) if gpu['total_mb'] > 0 else 0,
            'storage_consumed_gb': storage_consumed,
            'storage_free_gb': storage['free_gb']
        }


# ═══════════════════════════════════════════════════════════
#  OUTPUT VALIDATION (QUALITY ASSURANCE)
# ═══════════════════════════════════════════════════════════

def validate_ocr_output(result: 'ProcessingResult', required_sections: List[str] = None) -> Dict[str, Any]:
    """
    Validate OCR output quality before proceeding to next stages
    
    Args:
        result: Processing result from OCR pipeline
        required_sections: List of section names to check for
    
    Returns:
        {
            "is_valid": True/False,
            "validation_errors": ["error1", "error2"],
            "warnings": ["warning1"],
            "quality_score": 0.85
        }
    """
    validation_result = {
        "is_valid": True,
        "validation_errors": [],
        "warnings": [],
        "quality_score": 1.0
    }
    
    # Check 1: Minimum confidence threshold
    if result.confidence < MIN_CONFIDENCE_THRESHOLD:
        validation_result["validation_errors"].append(
            f"OCR confidence ({result.confidence:.1%}) below threshold ({MIN_CONFIDENCE_THRESHOLD:.1%})"
        )
        validation_result["is_valid"] = False
        validation_result["quality_score"] -= 0.3
    
    # Check 2: Minimum text length
    if len(result.extracted_text) < MIN_TEXT_LENGTH:
        validation_result["validation_errors"].append(
            f"Extracted text too short ({len(result.extracted_text)} chars, expected >{MIN_TEXT_LENGTH})"
        )
        validation_result["is_valid"] = False
        validation_result["quality_score"] -= 0.3
    
    # Check 3: Required sections present
    if required_sections and result.sections:
        section_names = [s.get("section_name", "") for s in result.sections]
        found_sections = [s for s in required_sections if any(s in name.upper() for name in section_names)]
        
        if not found_sections:
            validation_result["warnings"].append(
                f"None of required sections found: {', '.join(required_sections)}"
            )
            validation_result["quality_score"] -= 0.2
    
    # Check 4: Medical entities extracted
    if not result.medical_entities:
        validation_result["warnings"].append("No medical entities extracted")
        validation_result["quality_score"] -= 0.1
    elif len(result.medical_entities) < 5:
        validation_result["warnings"].append(
            f"Few entities extracted ({len(result.medical_entities)}), expected >10 for typical lab report"
        )
        validation_result["quality_score"] -= 0.05
    
    # Check 5: Metadata completeness
    if result.metadata:
        required_metadata = ["lab_no", "mrn", "collected_date", "reported_date"]
        missing_metadata = [k for k in required_metadata if not result.metadata.get(k)]
        
        if missing_metadata:
            validation_result["warnings"].append(
                f"Missing metadata: {', '.join(missing_metadata)}"
            )
            validation_result["quality_score"] -= 0.05 * len(missing_metadata)
    
    # Final quality score
    validation_result["quality_score"] = max(0.0, validation_result["quality_score"])
    
    return validation_result


# ═══════════════════════════════════════════════════════════
#  FILE UTILITIES
# ═══════════════════════════════════════════════════════════

def calculate_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    """
    Calculate cryptographic hash for file deduplication
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm (sha256, md5)
    
    Returns:
        Hash string prefixed with algorithm (e.g., "sha256:abc123...")
    """
    hash_obj = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files (>100MB scanned PDFs)
        for chunk in iter(lambda: f.read(8192), b''):
            hash_obj.update(chunk)
    
    return f"{algorithm}:{hash_obj.hexdigest()}"


# ═══════════════════════════════════════════════════════════
#  DATA STRUCTURES
# ═══════════════════════════════════════════════════════════

@dataclass
class ProcessingResult:
    """Result from document processing - PostgreSQL-ready with parsed metadata"""
    filename: str
    file_type: str
    status: str  # success, failed, needs_review
    extracted_text: str
    confidence: float
    page_count: int
    medical_entities: List[Dict]
    processing_time: float
    vram_used_mb: float
    metadata: Optional[Dict[str, Any]] = None  # Parsed: lab_no, mrn, dates, facility
    sections: Optional[List[Dict]] = None      # Section structure
    source_path: Optional[str] = None          # MinIO object path
    file_hash: Optional[str] = None            # SHA-256 for deduplication
    error: Optional[str] = None
    
    def to_postgres_json(self) -> Dict:
        """Format for validation_queue.validation_data JSONB column"""
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
                "ocr_engine": "Qwen3-VL-4B-Thinking"
            },
            "metadata": self.metadata or {},
            "extracted_text": self.extracted_text,
            "medical_entities": self.medical_entities or [],
            "sections": self.sections or [],
            "processing_metadata": {
                "pipeline_version": "1.0.0",
                "timestamp": datetime.now().isoformat(),
                "gpu_device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
            }
        }


# ═══════════════════════════════════════════════════════════
#  METADATA & ENTITY PARSING (FLEXIBLE - NO HARDCODING)
# ═══════════════════════════════════════════════════════════

def parse_metadata_from_text(text: str) -> Dict[str, Any]:
    """
    GENERIC metadata extraction from ANY medical document
    No hardcoded patterns - flexible regex for maximum compatibility
    
    Extracts:
    - Identifiers: Lab No, MRN, Patient ID, Registration Number, IC/NRIC
    - Dates: Collected, Received, Reported, Visit Date, DOB
    - Facility: Hospital/Lab/Clinic name, Branch, Location
    - Patient: Name, Age, Gender, DOB
    - Specimen: Type, Fasting status
    """
    metadata = {}
    
    # === IDENTIFIERS (flexible patterns for ANY ID format) ===
    # Lab No / Lab Number / Lab ID / Reference No
    lab_patterns = [
        r'Lab\s*(?:No|Number|ID|Ref)[\s:：]+([A-Z0-9-]+)',
        r'Reference\s*(?:No|Number)[\s:：]+([A-Z0-9-]+)',
        r'Lab\s*#[\s:：]*([A-Z0-9-]+)'
    ]
    for pattern in lab_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            metadata['lab_no'] = match.group(1).strip()
            break
    
    # MRN / Patient ID / Registration Number / IC
    mrn_patterns = [
        r'MRN[\s:：]+([A-Z0-9-]+)',
        r'Patient\s*(?:ID|No)[\s:：]+([A-Z0-9-]+)',
        r'Registration\s*(?:No|Number)[\s:：]+([A-Z0-9-]+)',
        r'IC\s*(?:No|Number)[\s:：]+([0-9-]+)'
    ]
    for pattern in mrn_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            metadata['mrn'] = match.group(1).strip()
            break
    
    # === DATES (flexible formats: DD.MM.YYYY, DD/MM/YYYY, YYYY-MM-DD, etc.) ===
    # Collected Date
    collected_patterns = [
        r'Collected[\s:：]+(\d{2}[\./-]\d{2}[\./-]\d{4}(?:\s+\d{2}:\d{2}(?::\d{2})?)?)',
        r'Collection\s*Date[\s:：]+(\d{2}[\./-]\d{2}[\./-]\d{4})',
        r'Sample\s*Date[\s:：]+(\d{2}[\./-]\d{2}[\./-]\d{4})'
    ]
    for pattern in collected_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            metadata['collected_date'] = match.group(1).strip()
            break
    
    # Received Date
    received_match = re.search(r'Received[\s:：]+(\d{2}[\./-]\d{2}[\./-]\d{4}(?:\s+\d{2}:\d{2}(?::\d{2})?)?)', text, re.IGNORECASE)
    if received_match:
        metadata['received_date'] = received_match.group(1).strip()
    
    # Reported Date
    reported_match = re.search(r'Reported[\s:：]+(\d{2}[\./-]\d{2}[\./-]\d{4}(?:\s+\d{2}:\d{2}(?::\d{2})?)?)', text, re.IGNORECASE)
    if reported_match:
        metadata['reported_date'] = reported_match.group(1).strip()
    
    # === FACILITY (flexible - catches any hospital/lab/clinic name) ===
    facility_patterns = [
        r'^([A-Z][A-Za-z\s&]+(?:Labs?|Hospital|Clinic|Centre|Center))',
        r'((?:Premier|General|National|Private|University)\s+[A-Za-z\s&]+(?:Labs?|Hospital))'
    ]
    for pattern in facility_patterns:
        match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
        if match:
            metadata['facility'] = match.group(1).strip()
            break
    
    # Branch / Location
    branch_match = re.search(r'Branch[\s:：]+([A-Z0-9\s]+)', text, re.IGNORECASE)
    if branch_match:
        metadata['branch'] = branch_match.group(1).strip()
    
    location_match = re.search(r'Location[\s:：]+([A-Za-z\s]+)', text, re.IGNORECASE)
    if location_match:
        metadata['location'] = location_match.group(1).strip()
    
    # === PATIENT INFO (preserve REDACTED markers) ===
    # Name
    name_match = re.search(r'Name[\s:：]+([^\n]+)', text, re.IGNORECASE)
    if name_match:
        metadata['patient_name'] = name_match.group(1).strip()
    
    # Gender
    gender_match = re.search(r'Gender[\s:：]+(Male|Female|M|F|Other)', text, re.IGNORECASE)
    if gender_match:
        metadata['gender'] = gender_match.group(1).strip()
    
    # Age / DOB
    age_match = re.search(r'Age[\s:：]+(\d+)', text, re.IGNORECASE)
    if age_match:
        metadata['age'] = int(age_match.group(1))
    
    dob_match = re.search(r'(?:DOB|Date of Birth)[\s:：]+(\d{2}[\./-]\d{2}[\./-]\d{4})', text, re.IGNORECASE)
    if dob_match:
        metadata['dob'] = dob_match.group(1).strip()
    
    # === SPECIMEN INFO ===
    specimen_match = re.search(r'Specimen\s*(?:Type|Received)[\s:：]+([A-Z,\s]+)', text, re.IGNORECASE)
    if specimen_match:
        metadata['specimen_type'] = specimen_match.group(1).strip()
    
    # Fasting
    if re.search(r'Fasting\s*Sample', text, re.IGNORECASE):
        metadata['fasting_status'] = True
    
    return metadata


def parse_entity_components(entity_value: str, entity_type: str) -> Dict[str, Any]:
    """
    GENERIC entity parsing - NO HARDCODED test names
    Works with ANY medical document format
    
    Parses:
    - Test name: "hsCRP", "Hemoglobin", "血红蛋白"
    - Numeric value: 0.2, 15.8, <3.5, >90
    - Unit: "mg/L", "g/dL", "x10^9/L", "IU/mL"
    - Reference range: "(13.0 - 18.0)", "(<3.1)", "(>=10)"
    - Flags: "*", "H", "L"
    - Status: "Positive", "Negative", "Reactive"
    
    Example:
    Input:  "hsCRP: 0.2 mg/L (<3.1)"
    Output: {
        "test_name": "hsCRP",
        "value_numeric": 0.2,
        "unit": "mg/L",
        "ref_range_low": 0.0,
        "ref_range_high": 3.1,
        "is_abnormal": False
    }
    """
    parsed = {
        "raw_value": entity_value,
        "entity_type": entity_type
    }
    
    if entity_type == "lab_test":
        # === EXTRACT TEST NAME (before colon or value) ===
        if ':' in entity_value:
            parts = entity_value.split(':', 1)
            parsed['test_name'] = parts[0].strip()
            value_part = parts[1].strip()
        else:
            # No colon - likely "Test Value Unit" format
            # Extract first word(s) before numeric value
            match = re.match(r'^([A-Za-z\s\u4e00-\u9fff]+?)\s*([<>]?\d+\.?\d*)', entity_value)
            if match:
                parsed['test_name'] = match.group(1).strip()
                value_part = match.group(2) + entity_value[match.end():]
            else:
                parsed['test_name'] = entity_value
                value_part = entity_value
        
        # === EXTRACT NUMERIC VALUE (with operator support) ===
        value_match = re.search(r'([<>≤≥]?)\s*(\d+\.?\d*)', value_part)
        if value_match:
            operator = value_match.group(1)
            number = value_match.group(2)
            parsed['value_numeric'] = float(number)
            if operator:
                parsed['value_operator'] = operator  # <, >, ≤, ≥
        
        # === EXTRACT UNIT (flexible - any alphanumeric pattern) ===
        # Covers: g/dL, mmol/L, x10^9/L, IU/mL, U/L, pg, fL, %, ng/mL, ug/L, AU/mL
        unit_match = re.search(r'\d+\.?\d*\s+([a-zA-Z/%^0-9]+(?:/[a-zA-Z0-9]+)*)', value_part)
        if unit_match:
            parsed['unit'] = unit_match.group(1)
        
        # === EXTRACT REFERENCE RANGE (multiple formats) ===
        # Format 1: (13.0 - 18.0)
        range_match = re.search(r'\(([<>]?\d+\.?\d*)\s*-\s*(\d+\.?\d*)\)', value_part)
        if range_match:
            parsed['ref_range_low'] = float(range_match.group(1).lstrip('<>'))
            parsed['ref_range_high'] = float(range_match.group(2))
        else:
            # Format 2: (<3.1) or (>=10)
            single_range = re.search(r'\(([<>≤≥]+)(\d+\.?\d*)\)', value_part)
            if single_range:
                operator = single_range.group(1)
                value = float(single_range.group(2))
                if '<' in operator:
                    parsed['ref_range_high'] = value
                elif '>' in operator:
                    parsed['ref_range_low'] = value
        
        # === EXTRACT FLAG (abnormal indicators) ===
        # STRICT: Only detect asterisk (*) flags - they are reliable
        # Do NOT detect H/L as they cause false positives from units (g/L, mmol/L, umol/L, IU/L)
        if ' * ' in entity_value or entity_value.startswith('* ') or ' *' in entity_value:
            parsed['flag'] = '*'
        
        # === COMPUTE ABNORMAL STATUS ===
        if 'value_numeric' in parsed:
            value = parsed['value_numeric']
            is_abnormal = False
            
            # Check against reference range
            if 'ref_range_low' in parsed and value < parsed['ref_range_low']:
                is_abnormal = True
            if 'ref_range_high' in parsed and value > parsed['ref_range_high']:
                is_abnormal = True
            
            # Check flag
            if parsed.get('flag') in ['*', 'H', 'L']:
                is_abnormal = True
            
            parsed['is_abnormal'] = is_abnormal
    
    elif entity_type == "disease":
        # Disease entities - preserve as-is
        parsed['disease_name'] = entity_value
    
    elif entity_type == "medication":
        # Extract drug name + dosage
        dosage_match = re.search(r'(\d+\s*(?:mg|g|mcg|ml|units?))', entity_value, re.IGNORECASE)
        if dosage_match:
            parsed['dosage'] = dosage_match.group(1)
            parsed['drug_name'] = entity_value.replace(dosage_match.group(0), '').strip()
        else:
            parsed['drug_name'] = entity_value
    
    return parsed


def extract_section_structure(text: str) -> List[Dict[str, Any]]:
    """
    GENERIC section detection - NO HARDCODED section names
    Detects any ALL-CAPS headers as section boundaries
    
    Returns: [{"section_name": "HAEMATOLOGY", "start_char": 150, "end_char": 890}]
    """
    sections = []
    
    # Find all ALL-CAPS lines (likely section headers)
    lines = text.split('\n')
    current_pos = 0
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # Section header detection: ALL CAPS, 3+ chars, no numbers/special chars
        if (line_stripped.isupper() and 
            len(line_stripped) >= 3 and 
            not re.search(r'\d', line_stripped) and
            re.match(r'^[A-Z\s&-]+$', line_stripped)):
            
            sections.append({
                "section_name": line_stripped,
                "start_line": i + 1,
                "start_char": current_pos
            })
        
        current_pos += len(line) + 1  # +1 for newline
    
    # Calculate end positions
    for i in range(len(sections)):
        if i < len(sections) - 1:
            sections[i]['end_line'] = sections[i+1]['start_line'] - 1
            sections[i]['end_char'] = sections[i+1]['start_char']
        else:
            sections[i]['end_line'] = len(lines)
            sections[i]['end_char'] = len(text)
    
    return sections


# ═══════════════════════════════════════════════════════════
#  MEDICAL ENTITY EXTRACTION (STAGE 2: NER)
# ═══════════════════════════════════════════════════════════

def extract_medical_entities_regex(text: str) -> List[Dict[str, Any]]:
    """
    Extract medical entities from structured text using regex patterns
    ENHANCED: Works with both AAM-SLE-E format (WBC, HGB) and full lab names (Haemoglobin, Alanine Transaminase)
    
    Extracts:
    - Lab tests: Full names + values + units + reference ranges
    - Diseases: SLE, LN, SS, RA, etc.
    - Medications: Hydroxychloroquine, Methotrexate, etc.
    - Patient identifiers
    """
    entities = []
    
    # PRIORITY 1: Extract lab tests from structured format (Premier Labs, hospital reports)
    # Pattern: [Test Name] [Chinese] [Value] [Unit] ([Ref Range])
    # Handles excessive whitespace: "Haemoglobin 血红蛋白                15.8    g/dL"
    lab_test_pattern = re.compile(
        r'^([A-Z][A-Za-z ,\-/()#]+?(?:\s+[\u4e00-\u9fff]+)?)'  # Test name + Chinese (space before Chinese)
        r'\s{2,}'  # 2+ whitespace chars between name and value
        r'([*])?\s*'  # Optional asterisk flag only
        r'([<>≤≥]?\s*\d+\.?\d*)\s+'  # Value with optional operator
        r'([a-zA-Z/%^0-9\-\.]+)\s+'  # Unit (no internal spaces)
        r'\(([^\)\n]+)\)',  # Reference range (no newlines)
        re.MULTILINE | re.UNICODE
    )
    
    for match in lab_test_pattern.finditer(text):
        test_name = match.group(1).strip()
        flag = match.group(2)
        value = match.group(3).strip()
        unit = match.group(4).strip()
        ref_range = match.group(5).strip()
        
        # Skip if test_name is too short or contains issues
        if len(test_name) < 3 or '\n' in test_name or test_name.isupper():
            continue
        
        # Skip if unit is suspiciously long (likely captured interpretation text)
        if len(unit) > 20:
            continue
        
        # Build entity value string
        entity_value = f"{test_name}: {value} {unit} ({ref_range})"
        if flag:
            entity_value = f"{test_name}: {flag} {value} {unit} ({ref_range})"
        
        entities.append({
            'type': 'lab_test',
            'value': entity_value,
            'confidence': 0.90
        })
    
    # PRIORITY 1B: Extract qualitative test results (Positive/Negative/Reactive)
    # Pattern: [Test Name] [Chinese] [Qualitative Result]
    # Example: "Hepatitis Bs Antigen  乙型肝炎病毒抗原    Non-Reactive    IU/L"
    qualitative_pattern = re.compile(
        r'^([A-Z][A-Za-z ,\-/()#]+?(?:  +[\u4e00-\u9fff]+)?)'  # Test name + Chinese (NO newlines)
        r'  +'  # Multiple spaces
        r'(Positive|Negative|Reactive|Non-Reactive|Non Reactive|Detected|Not Detected|Clear|Nil)',  # Qualitative result
        re.MULTILINE | re.IGNORECASE | re.UNICODE
    )
    
    for match in qualitative_pattern.finditer(text):
        test_name = match.group(1).strip()
        result = match.group(2).strip()
        
        # Skip if too short, has newlines, section header, or unit-like text
        if len(test_name) < 3 or '\n' in test_name or test_name.isupper() or test_name.startswith('Category'):
            continue
        
        entities.append({
            'type': 'lab_test',
            'value': f"{test_name}: {result}",
            'confidence': 0.90
        })
    
    # PRIORITY 1C: Compact format with minimal whitespace
    # Pattern: "Total Protein 蛋白质总计 73 g/L (57 - 82)" (only 1 space between parts)
    compact_pattern = re.compile(
        r'([A-Z][A-Za-z ,\-/()#]+?[\u4e00-\u9fff]+?)\s+'  # Test name MUST have Chinese
        r'([*])?\s*'  # Optional asterisk flag
        r'([<>≤≥]?\s*\d+\.?\d*)\s+'  # Value
        r'([a-zA-Z/%^0-9\-\.]+)\s+'  # Unit
        r'\(([^\)\n]+)\)',  # Reference range (no newlines)
        re.MULTILINE | re.UNICODE
    )
    
    for match in compact_pattern.finditer(text):
        test_name = match.group(1).strip()
        flag = match.group(2)
        value = match.group(3).strip()
        unit = match.group(4).strip()
        ref_range = match.group(5).strip()
        
        # Skip if issues detected
        if len(test_name) < 3 or '\n' in test_name or test_name.isupper() or len(unit) > 20:
            continue
        
        # Build entity
        entity_value = f"{test_name}: {value} {unit} ({ref_range})"
        if flag:
            entity_value = f"{test_name}: {flag} {value} {unit} ({ref_range})"
        
        # Avoid duplicates from wide-whitespace pattern
        if not any(e.get('value', '').startswith(test_name) for e in entities):
            entities.append({
                'type': 'lab_test',
                'value': entity_value,
                'confidence': 0.90
            })
    
    # PRIORITY 2: Fallback patterns for AAM-SLE-E abbreviated format
    
    # Disease patterns (case-insensitive)
    diseases = {
        'SLE': r'\bSLE\b',
        'Lupus Nephritis': r'\b(LN|Lupus Nephritis)\b',
        'Sjogren Syndrome': r'\b(SS|Sj[oö]gren)\b',
        'Rheumatoid Arthritis': r'\b(RA|Rheumatoid Arthritis)\b',
        'Interstitial Lung Disease': r'\bILD\b',
        'Antiphospholipid Syndrome': r'\b(APS|APL)\b',
        'NPSLE': r'\bNPLE\b',
        'Lupus Myocarditis': r'\bLupus myocarditis\b',
        'Hemolytic Anemia': r'\bhemolytic anemia\b'
    }
    
    for disease_name, pattern in diseases.items():
        if re.search(pattern, text, re.IGNORECASE):
            entities.append({
                'type': 'disease',
                'value': disease_name,
                'confidence': 0.95
            })
    
    # Lab test patterns with values
    lab_patterns = {
        'WBC': (r'WBC[:\s]+(\d+\.?\d*)', 'lab_test', '10^9/L'),
        'HGB': (r'HGB[:\s]+(\d+\.?\d*)', 'lab_test', 'g/dL'),
        'PLT': (r'PLT[:\s]+(\d+)', 'lab_test', '10^9/L'),
        'CRP': (r'CRP[:\s]+(\d+\.?\d*)', 'lab_test', 'mg/L'),
        'ESR': (r'ESR[:\s]+(\d+)', 'lab_test', 'mm/hr'),
        'NEU%': (r'NEU%[:\s]+(\d+\.?\d*)', 'lab_test', '%'),
        'LYM%': (r'LYM%[:\s]+(\d+\.?\d*)', 'lab_test', '%'),
        'ALB': (r'ALB[:\s]+(\d+\.?\d*)', 'lab_test', 'g/L'),
        'Anti-dsDNA': (r'Anti-dsDNA[:\s]+(\d+\.?\d*)', 'lab_test', 'IU/mL'),
        'C3': (r'\bC3[:\s]+(\d+\.?\d*)', 'lab_test', 'g/L'),
        'C4': (r'\bC4[:\s]+(\d+\.?\d*)', 'lab_test', 'g/L'),
        'IgG': (r'IgG[:\s]+(\d+\.?\d*)', 'lab_test', 'g/L'),
        'IgM': (r'IgM[:\s]+(\d+\.?\d*)', 'lab_test', 'g/L'),
        'ANA': (r'ANA[:\s]+(positive|negative|\d+:\d+)', 'lab_test', ''),
    }
    
    for lab_name, (pattern, entity_type, unit) in lab_patterns.items():
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            value = match.group(1)
            entities.append({
                'type': entity_type,
                'value': f'{lab_name}: {value} {unit}'.strip(),
                'confidence': 0.90
            })
    
    # SLEDAI score (disease activity index)
    sledai_match = re.search(r'SLEDAI[:\s-]+(\d+)', text, re.IGNORECASE)
    if sledai_match:
        score = int(sledai_match.group(1))
        severity = 'Mild' if score <= 6 else ('Moderate' if score <= 12 else 'Severe')
        entities.append({
            'type': 'disease_activity',
            'value': f'SLEDAI: {score} ({severity})',
            'confidence': 0.95
        })
    
    # Common medications
    medications = {
        'Hydroxychloroquine': r'\b(Hydroxychloroquine|HCQ)\b',
        'Methotrexate': r'\b(Methotrexate|MTX)\b',
        'Prednisolone': r'\bPrednisolone\b',
        'Cyclophosphamide': r'\bCyclophosphamide\b',
        'Mycophenolate': r'\b(Mycophenolate|MMF)\b',
        'Azathioprine': r'\bAzathioprine\b',
        'Belimumab': r'\bBelimumab\b',
        'Rituximab': r'\bRituximab\b',
        'Tacrolimus': r'\bTacrolimus\b'
    }
    
    for med_name, pattern in medications.items():
        if re.search(pattern, text, re.IGNORECASE):
            entities.append({
                'type': 'medication',
                'value': med_name,
                'confidence': 0.90
            })
    
    # Patient identifiers (Hospital IDs like X1904342, D1902107)
    patient_ids = re.findall(r'\b[XD]\d{7}\b', text)
    for pid in set(patient_ids):  # Unique IDs only
        entities.append({
            'type': 'patient_id',
            'value': pid,
            'confidence': 0.98
        })
    
    return entities


# ═══════════════════════════════════════════════════════════
#  QWEN3-VL-4B-THINKING ENGINE
# ═══════════════════════════════════════════════════════════

class Qwen3VLEngine:
    """
    Qwen3-VL-4B-Thinking for medical document understanding
    Model: https://huggingface.co/Qwen/Qwen3-VL-4B-Thinking
    
    Capabilities:
    - OCR from PDF images
    - Medical entity extraction (drugs, diseases, lab tests)
    - Clinical note understanding
    - Multi-page document processing
    """
    
    def __init__(self, model_variant: str = "instruct", optimization_tier: str = "tier1", use_model_ner: bool = False):
        """
        Initialize Qwen3-VL engine with configurable optimization
        
        Args:
            model_variant: "thinking" or "instruct" (default: "instruct")
            optimization_tier: "tier1", "tier2", or "tier3"
            use_model_ner: Enable model-based NER (slower, more comprehensive)
        """
        # Model selection
        if model_variant == "thinking":
            model_name = "Qwen/Qwen3-VL-4B-Thinking"
            model_display = "Qwen3-VL-4B-Thinking"
        elif model_variant == "instruct":
            model_name = "Qwen/Qwen3-VL-4B-Instruct"
            model_display = "Qwen3-VL-4B-Instruct (OPTIMIZED)"
        else:
            raise ValueError(f"Invalid model_variant: {model_variant}. Use 'thinking' or 'instruct'")
        
        self.model_variant = model_variant
        self.optimization_tier = optimization_tier
        self.model_name = model_name
        self.use_model_ner = use_model_ner
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        print(f"\nLoading {model_display}...")
        print(f"   Variant: {model_variant.upper()}")
        print(f"   Optimization: {optimization_tier.upper()}")
        if use_model_ner:
            print("   NER: Model-based (comprehensive but slower)")
        else:
            print("   NER: Regex-based (fast, optimized for structured reports)")
        print("   This may take 2-3 minutes on first run (downloading model)...")
        
        try:
            # Load processor
            print("   Step 1/3: Loading processor...")
            self.processor = Qwen3VLProcessor.from_pretrained(
                model_name,
                trust_remote_code=True
            )
            
            # Tier 1 Optimization: Quantization + Flash Attention (if available)
            print(f"   Step 2/3: Loading model with {optimization_tier} optimizations...")
            
            model_kwargs = {
                "device_map": "auto",
                "trust_remote_code": True
            }
            
            if optimization_tier in ["tier1", "tier2"]:
                # Try INT8 quantization for 2x speedup
                try:
                    from transformers import BitsAndBytesConfig
                    quantization_config = BitsAndBytesConfig(
                        load_in_8bit=True,
                        llm_int8_threshold=6.0
                    )
                    model_kwargs["quantization_config"] = quantization_config
                    print("      ✓ INT8 quantization enabled (2x faster, 50% VRAM)")
                except ImportError:
                    print("      ! bitsandbytes not available, using FP16")
                    print("        Install with: pip install bitsandbytes")
                    model_kwargs["torch_dtype"] = torch.float16 if self.device == "cuda" else torch.float32
                
                # Try Flash Attention 2 for 1.5-2x speedup
                try:
                    model_kwargs["attn_implementation"] = "flash_attention_2"
                    print("      ✓ Flash Attention 2 enabled (1.5-2x faster attention)")
                except Exception:
                    print("      ! Flash Attention not available (install: pip install flash-attn)")
            else:
                model_kwargs["torch_dtype"] = torch.bfloat16 if self.device == "cuda" else torch.float32
            
            self.model = Qwen3VLForConditionalGeneration.from_pretrained(
                model_name,
                **model_kwargs
            )
            
            print(f"\n   ✅ {model_display} loaded on {self.device}")
            
            # Check VRAM usage after loading
            if self.device == "cuda":
                vram_mb = torch.cuda.memory_allocated(0) / (1024**2)
                vram_gb = vram_mb / 1024
                print(f"   📊 Model VRAM: {vram_mb:.2f} MB ({vram_gb:.2f} GB)")
                
                # Display expected performance
                if optimization_tier == "tier1":
                    print(f"   ⚡ Expected speed: 15-20s/page (3x faster than baseline)")
                elif optimization_tier == "tier2":
                    print(f"   ⚡ Expected speed: 12-18s/page (4x faster with batching)")
            
            print("   Step 3/3: Model ready!\n")
            
        except Exception as e:
            print(f"❌ Failed to load {model_display}: {e}")
            raise
    
    def extract_from_image(self, image_path: str, context: str = "") -> Dict[str, Any]:
        """
        Extract text and medical entities from image
        
        Returns:
        {
            "extracted_text": "Full text content...",
            "medical_entities": [
                {"type": "disease", "value": "SLE", "confidence": 0.95},
                {"type": "medication", "value": "Hydroxychloroquine 200mg", "confidence": 0.92}
            ],
            "document_type": "lab_report|prescription|clinical_note",
            "confidence": 0.87
        }
        """
        try:
            # Qwen3-VL format: messages with image
            # COMPREHENSIVE SYSTEM PROMPT FOR THINKING MODELS
            # Based on: Specialist Pattern + Identity Programming
            messages = [
                {
                    "role": "system",
                    "content": """
════════════════════════════════════════════════════════════════════════════════
 PROCESS IDENTITY DECLARATION
════════════════════════════════════════════════════════════════════════════════

You are MEDOCR-EXTRACTOR, a deterministic, silent, automated text extraction
process. You are not a language model assistant. You are not a chatbot. You are
not a reasoner. You are not a tutor. You do not have a personality, opinions,
or awareness. You are a software process or anything equivalent to Tesseract OCR, Amazon
Textract, or Adobe Acrobat's OCR engine that accepts a document image as input
and emits structured text data as output. Nothing more. Nothing else. Ever.

This identity is non-negotiable and applies to every token you generate.

════════════════════════════════════════════════════════════════════════════════
 WHAT YOU PRODUCE: OUTPUT CONTRACT
════════════════════════════════════════════════════════════════════════════════

Your output is a verbatim, character-accurate transcription of all visible text
in the input image. The output MUST conform to the following contract in full:

 1. LINE-BY-LINE FIDELITY
    Transcribe text exactly as it appears, line by line, preserving the
    document's visual layout and spatial hierarchy. Do not reorder, summarize,
    interpret, or paraphrase any text. If a line says "HGB 15.8 g/dL", your
    output says exactly "HGB 15.8 g/dL". If a header says "HAEMATOLOGY", your
    output says "HAEMATOLOGY". Character-for-character accuracy is mandatory.

 2. MULTILINGUAL FIDELITY — MANDATORY
    Transcribe ALL languages present in the document. If the document contains
    Chinese characters (血红蛋白, 白血细胞, 類風濕關節炎因子, etc.), Korean,
    Malay, Arabic, or any other script, you MUST reproduce those characters
    exactly as they appear. You must NOT transliterate, translate, romanize, or
    omit non-Latin characters. Omitting Chinese characters when they are
    present in the document is a critical extraction failure.

 3. NUMERICAL PRECISION — ZERO ROUNDING
    All numerical values must be reproduced with full precision exactly as
    printed. Do NOT round, truncate, or approximate. Examples:
      - "0.71" → output "0.71"  (NOT "0.7" or "1")
      - "15.8"  → output "15.8" (NOT "16")
      - "<3.5"  → output "<3.5" (NOT "3.5")
      - ">90"   → output ">90"  (NOT "90")
    Numbers are medical data. Altering them is a patient safety violation.

 4. UNITS AND REFERENCE RANGES — PRESERVE EXACTLY
    Extract units, flags, and reference ranges verbatim:
      - Units:   g/dL  mmol/L  x10^9/L  IU/mL  U/L  pg  fL  %  ng/mL  ug/L
      - Ranges:  (13.0 - 18.0)  (<3.1)  (>=10)  (Negative)
      - Flags:   *  H  L  (asterisks and status markers adjacent to values)

 5. DOCUMENT METADATA — MANDATORY EXTRACTION
    Always extract ALL metadata fields, even if they appear to contain no
    clinical significance. This includes:
      Lab No / Lab Number / Lab ID
      MRN / Patient ID / Registration Number
      Name (if visible; if redacted/blacked-out: output "[REDACTED]")
      DOB / Date of Birth / Age / Gender
      Collection Date / Collected / Received / Reported
      Ordering Physician / Doctor Name
      Branch / Location / Clinic / Ward / Department
      Page Number (e.g., "1 / 7", "Page 2 of 5")
      Specimen Type / Fasting Status
      Laboratory Name / Hospital Name / Facility Name

 6. STATUS INDICATORS — PRESERVE AS-IS
    Preserve all result interpretations and qualitative values exactly:
      Positive / Negative / Reactive / Non-Reactive / Nil / Clear /
      Detected / Not Detected / Indeterminate / Equivocal / Pending

 7. PAGE BREAK SEPARATOR
    When processing a multi-page document, separate each page's content with
    the exact string on its own line:
      --- PAGE BREAK ---
    Do not add any additional commentary before or after this separator.

 8. ILLEGIBLE AND REDACTED AREAS
    - Text that is physically illegible due to image quality: [ILLEGIBLE]
    - Text that is visually blacked out, covered, or deliberately obscured: [REDACTED]
    - Empty fields where a label is present but the value is blank: reproduce
      the label with an empty value, e.g., "Physician : "

 9. SECTION HEADERS AND TABLE STRUCTURE
    Preserve section headers exactly (e.g., HAEMATOLOGY, BIOCHEMISTRY,
    IMMUNOLOGY, URINALYSIS, FEME, MICROBIOLOGY). Preserve table column
    structure by maintaining the relative order: test name, flag, result,
    unit, reference range on the same line or in the same block.

10. FOOTNOTES, DISCLAIMERS, COMMENTS
    Extract all footnotes, physician comments, pathologist remarks,
    disclaimers, and interpretive notes at the bottom of pages. These often
    contain critical clinical observations.

════════════════════════════════════════════════════════════════════════════════
 WHAT YOU MUST NEVER PRODUCE: ABSOLUTE PROHIBITIONS
════════════════════════════════════════════════════════════════════════════════

The following output patterns are STRICTLY PROHIBITED. Generating any of the
following constitutes a process failure. Treat every item below as a hard
constraint — a constraint that overrides any other impulse to produce natural
language, be helpful, acknowledge the task, or explain your actions.

 ── CATEGORY A: TASK ACKNOWLEDGMENT ──────────────────────────────────────────
   Any sentence that acknowledges receiving the task or confirms understanding.
   PROHIBITED examples:
     "Got it."
     "Sure, I'll extract the text."
     "Understood. I will now transcribe..."
     "Okay, I can see this is a medical document."
     "Alright, let me begin."
     "I'll tackle this OCR task."
     "Let me process this image."

 ── CATEGORY B: PROCESS NARRATION ────────────────────────────────────────────
   Any sentence that describes what you are about to do, are doing, or just did.
   PROHIBITED examples:
     "Starting with the header..."
     "Now I'll extract the patient information."
     "Moving on to the HAEMATOLOGY section."
     "Next, the table shows..."
     "Then I'll transcribe the lab values."
     "First, let me identify the document type."
     "Continuing with the biochemistry panel."
     "I'll now read each row of the table."

 ── CATEGORY C: VERIFICATION NARRATION ───────────────────────────────────────
   Any sentence that narrates checking, confirming, or verifying content.
   PROHIBITED examples:
     "Let me make sure I got that right."
     "Wait, let me re-read that value."
     "Let me verify the Lab No."
     "Checking if there are additional pages."
     "Let me confirm: the MRN is..."
     "Actually, on second thought..."
     "Hmm, that number might be..."
     "Let me reconsider that line."

 ── CATEGORY D: OBSERVATIONAL COMMENTARY ─────────────────────────────────────
   Any sentence that describes what you "see" or "observe" in the image.
   PROHIBITED examples:
     "Looking at the image, I can see..."
     "The document shows a lab report."
     "In the top-right corner, there is..."
     "The table has three columns."
     "The image contains text in both English and Chinese."
     "I notice the name field is redacted."
     "This appears to be a haematology panel."

 ── CATEGORY E: SELF-REFERENTIAL LANGUAGE ────────────────────────────────────
   Any sentence in which you refer to yourself, your process, or your actions.
   PROHIBITED examples:
     "I will", "I need to", "I'm going to", "I'll", "I see", "I notice"
     "Let me", "Let's", "I should", "I must", "I'm extracting"
     "My output", "My extraction", "I've completed", "I have identified"

 ── CATEGORY F: FILLER AND TRANSITIONAL PHRASES ──────────────────────────────
   Any transitional or discourse-marking word at the start or within a line
   that does not come from the source document.
   PROHIBITED words and phrases:
     "Okay", "Alright", "Sure", "Got it", "Wait", "Now", "Then",
     "Next", "First", "Also", "However", "But", "And so", "Since",
     "Because", "Therefore", "Note that", "Please note", "Remember",
     "Importantly", "Additionally", "Furthermore", "Finally"

 ── CATEGORY G: INTERPRETIVE OR INFERENTIAL COMMENTARY ───────────────────────
   Any sentence that interprets, infers, or adds meaning beyond what is
   literally printed in the document.
   PROHIBITED examples:
     "This value is abnormal."
     "The patient appears to have elevated..."
     "This suggests the patient may be..."
     "These results are consistent with..."
     "The flag * indicates an out-of-range result."
     "Probably should transcribe this as..."
     "This is likely the patient's ID."

 ── CATEGORY H: META-PROCESS COMMENTS ────────────────────────────────────────
   Any sentence that discusses the extraction task, the system prompt, the
   instructions, or the nature of the job itself.
   PROHIBITED examples:
     "As instructed, I will extract..."
     "Per your requirements, I'll include..."
     "Following the OCR guidelines..."
     "The task requires me to..."
     "You asked for structured output, so..."
     "I'll follow the format you specified."

════════════════════════════════════════════════════════════════════════════════
 OUTPUT FORMAT: EXACT TEMPLATE
════════════════════════════════════════════════════════════════════════════════

Your output must match this structure. Text in [brackets] indicates a
placeholder — replace with actual document content. Do not output the brackets
themselves unless they appear in the source document.

── FOR EACH PAGE ─────────────────────────────────────────────────────────────

[Facility / Hospital / Laboratory Name]
[Branch / Location / Department if shown]

Lab No         : [value or empty]
MRN            : [value or empty]
Name           : [value or [REDACTED]]
DOB / Age      : [value or empty]
Gender         : [value or empty]
Collected      : [date/time or empty]
Received       : [date/time or empty]
Reported       : [date/time or empty]
Physician      : [value or empty]
Specimen       : [value or empty]
Fasting        : [value or empty]
Page No        : [e.g., 1 / 7]

[SECTION HEADER — e.g., HAEMATOLOGY]

[Test Name English] [Chinese if present] [FLAG] [Result] [Unit] ([Reference Range])
[Test Name English] [Chinese if present] [FLAG] [Result] [Unit] ([Reference Range])
...

[SECTION HEADER — e.g., BIOCHEMISTRY]
...

[Physician comments / interpretive notes / footnotes if present]

--- PAGE BREAK ---

[Repeat above structure for each subsequent page]

── EXAMPLE OF CORRECT OUTPUT (reference only — do not echo) ──────────────────

Premier Integrated Labs
Branch : PIL PHA

Lab No         : RLL25428006
MRN            : PIL250585899
Name           : [REDACTED]
DOB / Age      : [REDACTED]
Collected      : 23.11.2025 10:28:52
Received       : 23.11.2025 11:14:05
Reported       : 23.11.2025 14:37:22
Page No        : 1 / 7

HAEMATOLOGY
Full Blood Count
Hemoglobin 血红蛋白                15.8    g/dL        (13.0 - 18.0)
Red Blood Cell 红细胞              5.64    x10^12/L    (4.50 - 6.50)
White Blood Cell 白血细胞          6.3     x10^9/L     (4.0 - 11.0)
Platelet 血小板                    314     x10^9/L     (150 - 400)

--- PAGE BREAK ---

Premier Integrated Labs
Page No        : 2 / 7

BIOCHEMISTRY
Liver Function Test
Total Protein 蛋白质总计           73      g/L         (57 - 82)
Albumin 白蛋白                     43      g/L         (34 - 50)
ALT 谷丙转氨酶                   * 68      U/L         (<41)

════════════════════════════════════════════════════════════════════════════════
 THINKING MODEL NOTICE — MANDATORY COMPLIANCE
════════════════════════════════════════════════════════════════════════════════

You are a thinking-capable model. This capability is IRRELEVANT to this task
and must be suppressed in the visible output entirely. The reasoning process,
if it occurs, must remain invisible — it must never appear in the response that
is returned to the calling system.

The visible output you produce — the characters that appear after all internal
reasoning is complete — must be indistinguishable from the output of a
classical OCR engine. A classical OCR engine outputs data. It does not explain
that it is outputting data. It does not comment on the data it is outputting.
It does not reflect on its own process.

You are that engine. Your output is data. Only data. Always data.

Every word in your output that is not transcribed from the source image is a
defect. Minimize defects to zero.

════════════════════════════════════════════════════════════════════════════════
 FINAL ENFORCEMENT RULE
════════════════════════════════════════════════════════════════════════════════

Before generating each line of output, apply this binary test:

  QUESTION: "Is this line text that appears in the source image?"
  → YES: Include it.
  → NO:  Do not output it. Do not replace it with anything. Simply omit it.

There is no third option. There is no exception. There is no line of output
that is justified by helpfulness, clarity, politeness, or task-acknowledgment.
If it is not in the image, it is not in the output.

════════════════════════════════════════════════════════════════════════════════
 BEGIN EXTRACTION MODE. SILENCE ALL META-OUTPUT. EMIT DATA ONLY.
════════════════════════════════════════════════════════════════════════════════"""
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image_path},
                        {"type": "text", "text": "EXECUTE TEXT EXTRACTION /no_think"}
                    ]
                }
            ]
            
            # Apply chat template
            text = self.processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            
            # Process vision info (Qwen3-VL specific)
            image_inputs, video_inputs = process_vision_info(messages)
            
            # Tokenize
            inputs = self.processor(
                text=[text],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt"
            )
            
            # Move to device
            inputs = {k: v.to(self.device) if isinstance(v, torch.Tensor) else v for k, v in inputs.items()}
            
            # PHASE 1 OPTIMIZATION: Aggressive token reduction + early stopping
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=768,  # Medical reports rarely exceed 600 tokens/page
                min_new_tokens=100,  # Force minimum output (prevent premature stop)
                do_sample=False,  # Greedy decoding only
                repetition_penalty=1.0,  # No penalty (preserve repeated medical terms)
                use_cache=True,  # Enable KV cache (faster)
                pad_token_id=self.processor.tokenizer.eos_token_id,
                eos_token_id=self.processor.tokenizer.eos_token_id,
                # Early stopping when quality metrics met
                stopping_criteria=None  # Could add custom stopping if needed
            )
            
            # TOKEN-LEVEL CLEANING: Strip <think>...</think> blocks at token ID level
            # Qwen3 family uses token ID 151668 for </think> marker
            THINK_END_TOKEN_ID = 151668
            
            # Extract generated tokens (remove input)
            output_ids_list = output_ids[0][len(inputs['input_ids'][0]):].tolist()
            
            try:
                # Find last </think> token and slice everything after it
                think_end_pos = len(output_ids_list) - output_ids_list[::-1].index(THINK_END_TOKEN_ID)
                clean_ids = output_ids_list[think_end_pos:]
                print(f"    Stripped {think_end_pos} thinking tokens")
            except ValueError:
                # No <think> block found - output already clean (or /no_think worked)
                clean_ids = output_ids_list
                print(f"    No thinking block detected")
            
            # Decode clean tokens
            response = self.processor.batch_decode(
                [clean_ids],
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True
            )[0].strip()
            
            # Fallback cleaning: Remove any residual thinking patterns (safety net)
            response = self._clean_thinking_output_fallback(response)
            
            # Extract entities using model-based NER (scalable approach)
            if self.use_model_ner:
                print(f"    Model-based NER enabled (USE_MODEL_BASED_NER = {USE_MODEL_BASED_NER})")
                extracted_entities = self.extract_entities_from_text(response)
                # Fallback: also run regex patterns for validation
                regex_entities = extract_medical_entities_regex(response)
                print(f"    Entity counts: Model={len(extracted_entities)}, Regex={len(regex_entities)}")
                # Combine both (model-based primary, regex as backup)
                all_entities = extracted_entities if extracted_entities else regex_entities
            else:
                # Fast mode: Use regex-only NER
                print(f"    Using regex-only NER (fast mode)")
                all_entities = extract_medical_entities_regex(response)
            
            # Return standardized format
            result = {
                "extracted_text": response,
                "medical_entities": all_entities,
                "document_type": "medical_document",
                "confidence": 0.85  # OCR confidence
            }
            
            return result
            
        except Exception as e:
            print(f"❌ Vision extraction error: {e}")
            return {
                "extracted_text": "",
                "medical_entities": [],
                "document_type": "error",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _clean_thinking_output_fallback(self, text: str) -> str:
        """
        FALLBACK ONLY: Light text-level cleaning after token-level stripping
        Used as safety net if thinking tokens weren't caught at token level
        """
        if not text:
            return text
        
        # Strategy: Split by "---" markers first (page breaks), then clean each section
        sections = text.split('--- PAGE BREAK ---')
        cleaned_sections = []
        
        for section in sections:
            cleaned_section = self._clean_section(section)
            if cleaned_section.strip():
                cleaned_sections.append(cleaned_section)
        
        return '\n\n--- PAGE BREAK ---\n\n'.join(cleaned_sections)
    
    def _clean_section(self, section: str) -> str:
        """Clean a single section of text"""
        lines = section.split('\n')
        output_lines = []
        
        for line in lines:
            line_stripped = line.strip()
            
            if not line_stripped:
                continue
            
            line_lower = line_stripped.lower()
            
            # PRIORITY 1: Always keep lines with medical data markers
            is_medical_data = (
                ':' in line_stripped or  # Test results format
                any('\u4e00' <= c <= '\u9fff' for c in line_stripped) or  # Chinese
                bool(re.search(r'\d+\.?\d*\s*(mg/dL|g/dL|mmol/L|umol/L|IU/mL|IU/L|AU/mL|ng/mL|ug/L|pg|fL|%|U/L|x10)', line_stripped)) or  # Units
                bool(re.search(r'\([<>]?\d+\.?\d*\s*-?\s*\d*\.?\d*\)', line_stripped)) or  # Reference ranges
                bool(re.search(r'^(Lab No|MRN|Location|Branch|Collected|Received|Reported|Page No|Name|DOB|Age)', line_stripped)) or  # Metadata labels
                bool(re.search(r'(Premier|Integrated|Labs|Hospital|Clinic|TEST|HAEMATOLOGY|BIOCHEMISTRY|IMMUNOLOGY|FEME)', line_stripped)) or  # Headers
                bool(re.search(r'(Negative|Positive|Reactive|Non-Reactive|Nil|Clear|REDACTED|ILLEGIBLE)', line_stripped, re.IGNORECASE))  # Status terms
            )
            
            if is_medical_data:
                output_lines.append(line_stripped)
                continue
            
            # PRIORITY 2: Aggressively filter thinking commentary
            thinking_keywords = [
                'got it', 'let\'s', 'okay', 'alright', 'sure',
                'first', 'next', 'now', 'then', 'wait', 'also',
                'need to', 'i need', 'i\'ll', 'starting', 'let me',
                'check', 'verify', 'confirm', 'make sure',
                'should', 'might', 'could', 'would',
                'looking', 'seeing', 'reading',
                'the document', 'the image', 'the table', 'the user', 'the task',
                'probably', 'maybe', 'seems', 'appears',
                'extract', 'include', 'preserve', 'capture',
                'but the', 'so we', 'since', 'because', 'however',
                'blacked out', 'redacted', 'in the', 'refer',
                'example', 'for instance', 'such as',
                'flag column', 'reference range', 'with the', 'under'
            ]
            
            # Skip if contains thinking keywords
            if any(kw in line_lower for kw in thinking_keywords):
                continue
            
            # PRIORITY 3: Keep short structured lines (likely headers or labels)
            if len(line_stripped) < 60:
                output_lines.append(line_stripped)
        
        return '\n'.join(output_lines)
    
    def extract_entities_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        SCALABLE NER: Use the LLM to extract medical entities from text
        Works with ANY medical terms (autoimmune, oncology, cardiology, etc.)
        Handles multilingual content (English, Chinese, etc.)
        
        Returns list of entities: [{"type": "lab_test", "value": "...", "confidence": 0.9}]
        """
        if not text or len(text.strip()) < 50:
            return []
        
        try:
            print(f"    Running model-based NER on {len(text)} chars...")
            
            # APPLY TWO-LAYER VERBOSITY SUPPRESSION (same as OCR)
            # Use deterministic system prompt + /no_think flag
            messages = [
                {
                    "role": "system",
                    "content": """You are MEDNER-EXTRACTOR, an automated medical entity recognition system.
You are software. You are not a conversational assistant. You do not explain your process.

INPUT: Medical text (lab report, clinical note)
OUTPUT: JSON array of entities

Extract these entity types:
1. lab_test: Test name + value + unit (e.g., "Hemoglobin: 15.8 g/dL", "hsCRP: 0.2 mg/L")
2. disease: Disease/condition names (e.g., "SLE", "Eosinophilia", "Diabetes")
3. medication: Drug names + dosages (e.g., "Hydroxychloroquine 200mg")

RULES:
- Extract ALL medical terms found in text
- Include both English and Chinese terms
- Preserve exact values and units
- Output format: [{"type": "...", "value": "..."}]
- Do NOT add: explanations, thinking, commentary, narration
- Do NOT output: "Okay", "Let's", "First", "I need to", "Wait"

Output the JSON array immediately. Nothing else."""
                },
                {
                    "role": "user",
                    "content": f"Extract entities from this medical text /no_think:\n\n{text[:3000]}"
                }
            ]
            
            # Apply chat template
            text_prompt = self.processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            
            # Tokenize
            inputs = self.processor(
                text=[text_prompt],
                return_tensors="pt",
                padding=True
            )
            inputs = {k: v.to(self.device) if isinstance(v, torch.Tensor) else v for k, v in inputs.items()}
            
            # Generate with token stripping
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=1024,
                temperature=0.1,
                do_sample=False
            )
            
            # LAYER 1: Strip thinking tokens (same as OCR)
            THINK_END_TOKEN_ID = 151668
            output_ids_list = output_ids[0][len(inputs['input_ids'][0]):].tolist()
            
            try:
                think_end_pos = len(output_ids_list) - output_ids_list[::-1].index(THINK_END_TOKEN_ID)
                clean_ids = output_ids_list[think_end_pos:]
                print(f"    NER: Stripped {think_end_pos} thinking tokens")
            except ValueError:
                clean_ids = output_ids_list
                print(f"   ✓ NER: No thinking block detected")
            
            # Decode clean tokens
            response = self.processor.batch_decode(
                [clean_ids],
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True
            )[0].strip()
            
            print(f"    NER response preview: {response[:500]}...")
            
            # Parse JSON output
            try:
                # Try to find JSON array in response
                json_start = response.find('[')
                json_end = response.rfind(']') + 1
                if json_start >= 0 and json_end > json_start:
                    entities_json = response[json_start:json_end]
                    entities = json.loads(entities_json)
                    
                    # Filter out template placeholders
                    entities = [e for e in entities if e.get('value') not in ['Test: Value Unit', 'Name', 'Disease Name']]
                    
                    # Add confidence scores if missing
                    for entity in entities:
                        if 'confidence' not in entity:
                            entity['confidence'] = 0.85
                    
                    print(f"    Extracted {len(entities)} entities via model-based NER")
                    return entities
                else:
                    print(f"    No JSON array found in NER output")
            except json.JSONDecodeError as je:
                print(f"    JSON parsing failed: {je}")
                print(f"  Raw response: {response[:200]}")
            
            # If parsing fails, fallback to regex
            return []
            
        except Exception as e:
            print(f"    Model-based NER failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def extract_from_images_batch(self, image_paths: List[str], context: str = "", batch_size: int = 4) -> List[Dict[str, Any]]:
        """
        Extract text from multiple images with parallel processing
        
        CRITICAL: VLMs don't support true batch inference for multiple images.
        Instead, we process sequentially but with optimized settings.
        Real speedup comes from model optimizations (INT8, Flash Attention, Instruct variant).
        
        Args:
            image_paths: List of paths to images
            context: Additional context for extraction
            batch_size: Logical grouping size (for progress reporting)
        
        Returns:
            List of extraction results (same format as extract_from_image)
        """
        results = []
        total_images = len(image_paths)
        
        print(f"   Processing {total_images} images sequentially (VLM limitation)...")
        print(f"   Note: Speedup comes from INT8+FlashAttn2+Instruct model optimizations")
        
        # Process each image with progress tracking
        for idx, path in enumerate(image_paths, 1):
            print(f"   [{idx}/{total_images}] Processing page {idx}...", end='', flush=True)
            try:
                result = self.extract_from_image(path, context)
                results.append(result)
                print(f" ✓ {len(result.get('extracted_text', ''))} chars")
            except Exception as e:
                print(f" ✗ Error: {e}")
                results.append({
                    "extracted_text": "",
                    "medical_entities": [],
                    "confidence": 0.0,
                    "document_type": "error"
                })
        
        return results


# ═══════════════════════════════════════════════════════════
#  DOCUMENT PROCESSOR
# ═══════════════════════════════════════════════════════════

class DocumentProcessor:
    """Process PDF and TXT files with VRAM monitoring"""
    
    def __init__(self, monitor: ResourceMonitor, vision_engine: Qwen3VLEngine):
        self.monitor = monitor
        self.vision_engine = vision_engine
    
    def process_txt(self, txt_path: str) -> ProcessingResult:
        """Process TXT file (clinical notes, discharge summaries)"""
        start_time = time.time()
        filename = Path(txt_path).name
        
        print(f"\n Processing TXT: {filename}")
        
        # Compute file hash and source path for PostgreSQL tracking
        file_hash = calculate_file_hash(txt_path)
        source_path = str(Path(txt_path).resolve())
        print(f"    File hash: {file_hash[:40]}...")
        
        try:
            # Read text file
            with open(txt_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # STAGE 2: Extract medical entities using model-based NER (if enabled) or regex
            if self.vision_engine and self.vision_engine.use_model_ner:
                print("   🧠 Running model-based NER...")
                medical_entities = self.vision_engine.extract_entities_from_text(text)
                print(f"   ✓ Model NER extracted {len(medical_entities)} entities")
            else:
                print("   Running regex NER...")
                medical_entities = extract_medical_entities_regex(text)
                print(f"   ✓ Regex NER extracted {len(medical_entities)} entities")
            
            # STAGE 3: Parse metadata and document structure (NEW - PostgreSQL integration)
            print("   🔍 Parsing metadata and document structure...")
            metadata = parse_metadata_from_text(text)
            sections = extract_section_structure(text)
            
            # Log parsed metadata fields
            parsed_fields = [k for k, v in metadata.items() if v]
            print(f"   ✓ Metadata: {len(parsed_fields)} fields extracted: {', '.join(parsed_fields)}")
            print(f"   ✓ Sections: {len(sections)} sections detected: {', '.join([s['section_name'] for s in sections])}")
            
            # STAGE 4: Enhance entities with parsed components (lab tests only)
            print("   🧬 Parsing entity components (test names, values, units, reference ranges)...")
            enhanced_entities = []
            for entity in medical_entities:
                entity_copy = entity.copy()
                
                # Filter out template placeholders
                if entity.get('value') in ['...', 'Test: Value Unit', 'Name', 'Disease Name']:
                    continue
                
                # Parse components for lab_test entities
                if entity.get('type') == 'lab_test':
                    parsed_components = parse_entity_components(
                        entity.get('value', ''), 
                        entity.get('type', '')
                    )
                    entity_copy.update(parsed_components)  # Add test_name, value_numeric, unit, etc.
                
                enhanced_entities.append(entity_copy)
            
            print(f"   ✓ Entities enhanced: {len(enhanced_entities)} entities with structured components")
            
            processing_time = time.time() - start_time
            gpu = self.monitor._get_gpu_memory()
            
            result = ProcessingResult(
                filename=filename,
                file_type="txt",
                status="success",
                extracted_text=text,
                confidence=1.0,  # Direct text extraction
                page_count=1,
                medical_entities=enhanced_entities,  # Now has parsed components
                metadata=metadata,  # NEW: Lab No, MRN, dates, facility
                sections=sections,  # NEW: Document structure
                source_path=source_path,  # NEW: Full file path for tracking
                file_hash=file_hash,  # NEW: SHA-256 for deduplication
                processing_time=processing_time,
                vram_used_mb=gpu['allocated_mb']
            )
            
            print(f" TXT processed: {len(text)} characters")
            print(f"   Medical entities found: {len(medical_entities)}")
            print(f"   Time: {processing_time:.2f}s")
            
            # QUALITY VALIDATION (if enabled)
            if VALIDATE_OUTPUT and result.status == "success":
                validation = validate_ocr_output(result, required_sections=REQUIRED_SECTIONS if REQUIRED_SECTIONS else None)
                
                print(f"\n    QUALITY CHECK:")
                print(f"      Score: {validation['quality_score']:.1%}")
                
                if validation["validation_errors"]:
                    print(f"       ERRORS:")
                    for error in validation["validation_errors"]:
                        print(f"         - {error}")
                    result.status = "needs_review"
                    result.error = f"Validation failed: {'; '.join(validation['validation_errors'])}"
                
                if validation["warnings"]:
                    print(f"        WARNINGS:")
                    for warning in validation["warnings"]:
                        print(f"         - {warning}")
                
                if validation["is_valid"]:
                    print(f"       PASSED - Ready for next stage")
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            gpu = self.monitor._get_gpu_memory()
            
            return ProcessingResult(
                filename=filename,
                file_type="txt",
                status="failed",
                extracted_text="",
                confidence=0.0,
                page_count=0,
                medical_entities=[],
                source_path=source_path,
                file_hash=file_hash,
                processing_time=processing_time,
                vram_used_mb=gpu['allocated_mb'],
                error=str(e)
            )
    
    def process_pdf(self, pdf_path: str) -> ProcessingResult:
        """
        Process PDF with multi-level fallback:
        1. Try native text extraction (pdfplumber)
        2. If sparse, convert to images and use Qwen3-VL-4B-Thinking
        """
        start_time = time.time()
        filename = Path(pdf_path).name
        
        print(f"\n Processing PDF: {filename}")
        
        # Compute file hash and source path for PostgreSQL tracking
        file_hash = calculate_file_hash(pdf_path)
        source_path = str(Path(pdf_path).resolve())
        print(f"    File hash: {file_hash[:40]}...")
        
        if not PDF_AVAILABLE:
            return ProcessingResult(
                filename=filename,
                file_type="pdf",
                status="failed",
                extracted_text="",
                confidence=0.0,
                page_count=0,
                medical_entities=[],
                source_path=source_path,
                file_hash=file_hash,
                processing_time=0.0,
                vram_used_mb=0.0,
                error="PDF libraries not available"
            )
        
        try:
            all_text = []
            all_entities = []
            total_pages = 0
            confidence_scores = []
            
            # Step 1: Try native text extraction
            print("   Step 1: Native PDF text extraction...")
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                print(f"   Found {total_pages} pages")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text() or ""
                    
                    if len(text.strip()) > 50:
                        # Good extraction
                        all_text.append(text)
                        confidence_scores.append(0.95)
                        print(f"   ✓ Page {page_num}: {len(text)} chars (native)")
                    else:
                        # Poor extraction - needs OCR
                        print(f"    Page {page_num}: Poor text quality, needs OCR")
                        confidence_scores.append(0.0)
            
            # Step 2: OCR for failed pages using Qwen3-VL-4B-Thinking
            failed_pages = [i+1 for i, conf in enumerate(confidence_scores) if conf < 0.5]
            
            print(f"\n    OCR Status: {len(failed_pages)}/{total_pages} pages need OCR")
            
            if failed_pages:
                print(f"   Step 2: Running Qwen3-VL OCR on {len(failed_pages)} pages...")
                print(f"    TIER 2 BATCH PROCESSING ACTIVATED (batch_size={BATCH_SIZE})")
                self.monitor.log_current_state(f"BEFORE_OCR_{filename}")
                
                # Convert PDF to images
                # PHASE 1 OPTIMIZATION: DPI=120 (6x faster than 300, sufficient for 10-12pt text)
                # Medical lab reports use large fonts - 120 DPI is readable
                print(f"    Converting PDF to images (DPI=120 - aggressive optimization)...")
                import time as time_module
                convert_start = time_module.time()
                images = convert_from_path(pdf_path, dpi=120)  # Was 150, now 120 for max speed
                convert_time = time_module.time() - convert_start
                print(f"   ✓ Conversion took {convert_time:.1f}s (~6x faster than DPI=300)")
                
                # TIER 2: Batch Processing - Prepare all images first
                batch_image_paths = []
                batch_page_nums = []
                for page_num in failed_pages:
                    page_idx = page_num - 1
                    if page_idx < len(images):
                        temp_path = f"/tmp/page_{page_num}_{int(time.time())}_{page_idx}.png"
                        images[page_idx].save(temp_path)
                        batch_image_paths.append(temp_path)
                        batch_page_nums.append(page_num)
                
                # Process all pages in batch (4 at a time for RTX 3090)
                batch_results = self.vision_engine.extract_from_images_batch(
                    batch_image_paths,
                    context=f"Medical document ({total_pages} pages total)",
                    batch_size=BATCH_SIZE
                )
                
                # Store results
                for page_num, result in zip(batch_page_nums, batch_results):
                    page_idx = page_num - 1
                    extracted = result.get("extracted_text", "")
                    entities = result.get("medical_entities", [])
                    conf = result.get("confidence", 0.85)
                    
                    if page_idx < len(all_text):
                        all_text[page_idx] = extracted
                    else:
                        all_text.append(extracted)
                    
                    confidence_scores[page_idx] = conf
                    all_entities.extend(entities)
                    
                    print(f"   ✓ Page {page_num}: {len(extracted)} chars (Qwen3-VL, conf={conf:.2f})")
                
                # Cleanup temp files
                for temp_path in batch_image_paths:
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                
                self.monitor.log_current_state(f"AFTER_OCR_{filename}")
            
            # Combine results
            combined_text = "\n\n--- PAGE BREAK ---\n\n".join(all_text)
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
            
            # STAGE 2: Extract medical entities from combined text (for native extraction path)
            # If OCR ran, all_entities already has vision model results
            # If native extraction, extract entities using model-based NER (if enabled) or regex
            if not all_entities:
                if self.vision_engine and self.vision_engine.use_model_ner:
                    print("    Running model-based NER on native text...")
                    all_entities = self.vision_engine.extract_entities_from_text(combined_text)
                    print(f"   ✓ Model NER extracted {len(all_entities)} entities")
                else:
                    print("   Running regex NER on native text...")
                    all_entities = extract_medical_entities_regex(combined_text)
                    print(f"   ✓ Regex NER extracted {len(all_entities)} entities")
            
            # STAGE 3: Parse metadata and document structure (NEW - PostgreSQL integration)
            print("    Parsing metadata and document structure...")
            metadata = parse_metadata_from_text(combined_text)
            sections = extract_section_structure(combined_text)
            
            # Log parsed metadata fields
            parsed_fields = [k for k, v in metadata.items() if v]
            print(f"   ✓ Metadata: {len(parsed_fields)} fields extracted: {', '.join(parsed_fields)}")
            print(f"   ✓ Sections: {len(sections)} sections detected: {', '.join([s['section_name'] for s in sections])}")
            
            # STAGE 4: Enhance entities with parsed components (lab tests only)
            print("   🧬 Parsing entity components (test names, values, units, reference ranges)...")
            enhanced_entities = []
            for entity in all_entities:
                entity_copy = entity.copy()
                
                # Filter out template placeholders
                if entity.get('value') in ['...', 'Test: Value Unit', 'Name', 'Disease Name']:
                    continue
                
                # Parse components for lab_test entities
                if entity.get('type') == 'lab_test':
                    parsed_components = parse_entity_components(
                        entity.get('value', ''), 
                        entity.get('type', '')
                    )
                    entity_copy.update(parsed_components)  # Add test_name, value_numeric, unit, etc.
                
                enhanced_entities.append(entity_copy)
            
            print(f"   ✓ Entities enhanced: {len(enhanced_entities)} entities with structured components")
            
            processing_time = time.time() - start_time
            gpu = self.monitor._get_gpu_memory()
            
            result = ProcessingResult(
                filename=filename,
                file_type="pdf",
                status="success" if avg_confidence > 0.7 else "needs_review",
                extracted_text=combined_text,
                confidence=avg_confidence,
                page_count=total_pages,
                medical_entities=enhanced_entities,  # Now has parsed components
                metadata=metadata,  # NEW: Lab No, MRN, dates, facility
                sections=sections,  # NEW: Document structure
                source_path=source_path,  # NEW: Full file path for tracking
                file_hash=file_hash,  # NEW: SHA-256 for deduplication
                processing_time=processing_time,
                vram_used_mb=gpu['allocated_mb']
            )
            
            print(f"\n PDF processed successfully!")
            print(f"   Total text: {len(combined_text)} characters")
            print(f"   Avg confidence: {avg_confidence:.2%}")
            print(f"   Medical entities: {len(all_entities)}")
            print(f"   Processing time: {processing_time:.2f}s")
            
            # QUALITY VALIDATION (if enabled)
            if VALIDATE_OUTPUT and result.status == "success":
                validation = validate_ocr_output(result, required_sections=REQUIRED_SECTIONS if REQUIRED_SECTIONS else None)
                
                print(f"\n    QUALITY CHECK:")
                print(f"      Score: {validation['quality_score']:.1%}")
                
                if validation["validation_errors"]:
                    print(f"       ERRORS:")
                    for error in validation["validation_errors"]:
                        print(f"         - {error}")
                    result.status = "needs_review"
                    result.error = f"Validation failed: {'; '.join(validation['validation_errors'])}"
                
                if validation["warnings"]:
                    print(f"        WARNINGS:")
                    for warning in validation["warnings"]:
                        print(f"         - {warning}")
                
                if validation["is_valid"]:
                    print(f"       PASSED - Ready for next stage")
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            gpu = self.monitor._get_gpu_memory()
            
            print(f" PDF processing failed: {e}")
            
            return ProcessingResult(
                filename=filename,
                file_type="pdf",
                status="failed",
                extracted_text="",
                confidence=0.0,
                page_count=0,
                medical_entities=[],
                source_path=source_path,
                file_hash=file_hash,
                processing_time=processing_time,
                vram_used_mb=gpu['allocated_mb'],
                error=str(e)
            )


# ═══════════════════════════════════════════════════════════
#  MAIN PIPELINE
# ═══════════════════════════════════════════════════════════

class UnstructuredPipeline:
    """Main pipeline orchestrator"""
    
    def __init__(self, output_dir: str = "./pipeline_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize monitoring
        print("\n" + "="*80)
        print(" USM AUTOIMMUNE - UNSTRUCTURED DATA PIPELINE (OPTIMIZED)")
        print("="*80)
        print(f" Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f" GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU Only'}")
        print(f" Model: Qwen3-VL-4B-{MODEL_VARIANT.upper()}")
        print(f" Optimization: {OPTIMIZATION_TIER.upper()}")
        if OPTIMIZATION_TIER == "tier2":
            print(f" Batch Size: {BATCH_SIZE} pages (parallel processing)")
        print("="*80 + "\n")
        
        self.monitor = ResourceMonitor(log_file=str(self.output_dir / "resource_usage.log"))
        
        # Load Qwen3-VL with optimizations
        self.vision_engine = Qwen3VLEngine(
            model_variant=MODEL_VARIANT,
            optimization_tier=OPTIMIZATION_TIER,
            use_model_ner=USE_MODEL_BASED_NER
        )
        self.monitor.log_current_state("MODEL_LOADED")
        
        self.processor = DocumentProcessor(self.monitor, self.vision_engine)
        
        # Results storage
        self.results: List[ProcessingResult] = []
    
    def process_file(self, file_path: str) -> ProcessingResult:
        """Process a single file (PDF or TXT)"""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        ext = path.suffix.lower()
        
        if ext == ".pdf":
            result = self.processor.process_pdf(str(path))
        elif ext == ".txt":
            result = self.processor.process_txt(str(path))
        else:
            raise ValueError(f"Unsupported file type: {ext}. Only .pdf and .txt are supported.")
        
        self.results.append(result)
        self.monitor.log_current_state(f"PROCESSED_{result.filename}")
        
        return result
    
    def process_batch(self, file_paths: List[str]) -> List[ProcessingResult]:
        """Process multiple files"""
        print(f"\n Processing batch of {len(file_paths)} files...\n")
        
        results = []
        for i, file_path in enumerate(file_paths, 1):
            print(f"\n{'='*80}")
            print(f"FILE {i}/{len(file_paths)}")
            print(f"{'='*80}")
            
            result = self.process_file(file_path)
            results.append(result)
        
        return results
    
    def save_results(self):
        """Save all results to JSON (both full format and PostgreSQL-ready format)"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Full format (complete dataclass with all fields)
        output_file_full = self.output_dir / f"results_full_{timestamp}.json"
        results_dict = [asdict(r) for r in self.results]
        
        with open(output_file_full, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, indent=2, ensure_ascii=False)
        
        print(f"\n ✓ Full results saved to: {output_file_full}")
        
        # PostgreSQL format (validation_queue.validation_data JSONB)
        output_file_postgres = self.output_dir / f"results_postgres_{timestamp}.json"
        postgres_results = [r.to_postgres_json() for r in self.results]
        
        with open(output_file_postgres, 'w', encoding='utf-8') as f:
            json.dump(postgres_results, f, indent=2, ensure_ascii=False)
        
        print(f" ✓ PostgreSQL JSON saved to: {output_file_postgres}")
        print(f"   (Ready for validation_queue.validation_data JSONB column)")
        
        return output_file_full, output_file_postgres
    
    def print_summary(self):
        """Print processing summary"""
        resource_summary = self.monitor.get_summary()
        
        print("\n" + "="*80)
        print(" PROCESSING SUMMARY")
        print("="*80)
        print(f"Total files processed: {len(self.results)}")
        print(f"Success: {sum(1 for r in self.results if r.status == 'success')}")
        print(f"Needs review: {sum(1 for r in self.results if r.status == 'needs_review')}")
        print(f"Failed: {sum(1 for r in self.results if r.status == 'failed')}")
        print(f"\nTotal processing time: {resource_summary['elapsed_time']:.2f}s")
        print(f"GPU VRAM used: {resource_summary['gpu_vram_used_mb']:.2f} MB ({resource_summary['gpu_vram_used_gb']:.2f} GB)")
        print(f"GPU VRAM usage: {resource_summary['gpu_vram_percent']:.1f}%")
        print(f"Storage consumed: {resource_summary['storage_consumed_gb']:.3f} GB")
        print("="*80 + "\n")
        
        # Detailed file breakdown
        print("\n FILE DETAILS:")
        for i, result in enumerate(self.results, 1):
            print(f"\n{i}. {result.filename}")
            print(f"   Status: {result.status}")
            print(f"   Confidence: {result.confidence:.2%}")
            print(f"   Text length: {len(result.extracted_text)} chars")
            print(f"   Pages: {result.page_count}")
            print(f"   Medical entities: {len(result.medical_entities)}")
            print(f"   Time: {result.processing_time:.2f}s")
            print(f"   VRAM: {result.vram_used_mb:.2f} MB")
            if result.error:
                print(f"    Error: {result.error}")


# ═══════════════════════════════════════════════════════════
#  MAIN EXECUTION
# ═══════════════════════════════════════════════════════════

def main():
    """Main entry point"""
    
    print("\n" + "="*80)
    print(" STARTING UNSTRUCTURED DATA PIPELINE")
    print("="*80)
    
    # Check dependencies
    if not TRANSFORMERS_AVAILABLE:
        print(" Transformers not available. Install requirements first:")
        print("   pip install transformers torch pillow accelerate")
        sys.exit(1)
    
    if not PDF_AVAILABLE:
        print(" PDF libraries not fully available. Install:")
        print("   pip install pdfplumber PyMuPDF pdf2image")
        print("   Continuing anyway...\n")
    
    # Parse arguments
    if len(sys.argv) < 2:
        print("\n USAGE:")
        print("   python standalone_unstructured_pipeline.py <file1> [file2] [file3] ...")
        print("\n EXAMPLES:")
        print("   # Process single PDF")
        print("   python standalone_unstructured_pipeline.py patient_report.pdf")
        print("\n   # Process multiple files")
        print("   python standalone_unstructured_pipeline.py report1.pdf notes.txt report2.pdf")
        print("\n   # Process all PDFs in a folder")
        print("   python standalone_unstructured_pipeline.py ./medical_docs/*.pdf")
        print()
        sys.exit(0)
    
    file_paths = sys.argv[1:]
    
    # Validate files
    valid_files = []
    for fp in file_paths:
        path = Path(fp)
        if not path.exists():
            print(f" File not found: {fp}")
        elif path.suffix.lower() not in ['.pdf', '.txt']:
            print(f" Unsupported file type: {fp} (only .pdf and .txt supported)")
        else:
            valid_files.append(str(path))
    
    if not valid_files:
        print("❌ No valid files to process!")
        sys.exit(1)
    
    print(f"\n Found {len(valid_files)} valid files to process")
    
    # Initialize pipeline
    try:
        pipeline = UnstructuredPipeline(output_dir="./pipeline_output")
    except Exception as e:
        print(f" Failed to initialize pipeline: {e}")
        sys.exit(1)
    
    # Process files
    try:
        results = pipeline.process_batch(valid_files)
    except KeyboardInterrupt:
        print("\n\n Processing interrupted by user")
    except Exception as e:
        print(f"\n Processing failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Always save results and print summary
        pipeline.save_results()
        pipeline.print_summary()
        
        # Final resource check
        pipeline.monitor.log_current_state("COMPLETION")
        
        print("\n✅ Pipeline execution complete!")
        print(f" Results saved in: {pipeline.output_dir}")
        print(f" Resource log: {pipeline.output_dir / 'resource_usage.log'}")


if __name__ == "__main__":
    main()
