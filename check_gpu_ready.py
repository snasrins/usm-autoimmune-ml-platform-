#!/usr/bin/env python3
"""
Quick GPU Check - Verify CUDA and model availability
Run this BEFORE running the full pipeline to catch issues early
"""

import sys

print("="*80)
print(" GPU ENVIRONMENT CHECK")
print("="*80)

# Check 1: PyTorch
print("\n 1. Checking PyTorch...")
try:
    import torch
    print(f"    PyTorch version: {torch.__version__}")
    print(f"    CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"    CUDA version: {torch.version.cuda}")
        print(f"    GPU device: {torch.cuda.get_device_name(0)}")
        
        # Check VRAM
        total_vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"    Total VRAM: {total_vram:.2f} GB")
        
        allocated_vram = torch.cuda.memory_allocated(0) / (1024**3)
        print(f"    Currently allocated: {allocated_vram:.2f} GB")
        print(f"    Available VRAM: {total_vram - allocated_vram:.2f} GB")
    else:
        print("    CUDA not available - will run on CPU (VERY SLOW!)")
        
except ImportError as e:
    print(f"    PyTorch not installed: {e}")
    sys.exit(1)

# Check 2: Transformers
print("\n 2. Checking Transformers...")
try:
    import transformers
    print(f"    Transformers version: {transformers.__version__}")
except ImportError:
    print("    Transformers not installed")
    print("      Install: pip install transformers")
    sys.exit(1)

# Check 3: PDF libraries
print("\n 3. Checking PDF libraries...")
try:
    import pdfplumber
    print("     pdfplumber available")
except ImportError:
    print("     pdfplumber not available")
    print("      Install: pip install pdfplumber")

try:
    import fitz
    print("     PyMuPDF (fitz) available")
except ImportError:
    print("     PyMuPDF not available")
    print("      Install: pip install PyMuPDF")

try:
    from pdf2image import convert_from_path
    print("     pdf2image available")
except ImportError:
    print("    pdf2image not available")
    print("      Install: pip install pdf2image")
    print("      Also need system package: sudo apt-get install poppler-utils")

# Check 4: Image processing
print("\n 4. Checking Image libraries...")
try:
    from PIL import Image
    print("    Pillow (PIL) available")
except ImportError:
    print("   Pillow not installed")
    print("      Install: pip install Pillow")

# Check 5: Monitoring
print("\n 5. Checking Monitoring libraries...")
try:
    import psutil
    print("    psutil available")
except ImportError:
    print("      psutil not available (needed for storage monitoring)")
    print("      Install: pip install psutil")

# Check 6: Test model download (optional - takes time)
print("\n 6. Checking Qwen3-VL-2B-Instruct availability...")
test_download = input("   Test download Qwen3-VL-2B-Instruct? (y/n): ").lower()

if test_download == 'y':
    print("   Attempting to load processor (this may take a few minutes)...")
    try:
        from transformers import AutoProcessor
        processor = AutoProcessor.from_pretrained(
            "Qwen/Qwen3-VL-2B-Instruct",
            trust_remote_code=True
        )
        print("   ✅ Qwen3-VL-2B-Instruct processor loaded successfully!")
        print("   ✅ Model is available and cached")
    except Exception as e:
        print(f"    Failed to load model: {e}")
        print("   Check internet connection to HuggingFace")
else:
    print("   ⏭️ Skipped model download test")

# Summary
print("\n" + "="*80)
print(" SUMMARY")
print("="*80)

all_good = True

if not torch.cuda.is_available():
    print(" WARNING: CUDA not available - pipeline will be VERY SLOW on CPU")
    all_good = False

try:
    import pdfplumber, fitz
    from pdf2image import convert_from_path
except ImportError:
    print(" WARNING: Some PDF libraries missing - PDF processing may fail")
    all_good = False

if all_good:
    print(" ALL CHECKS PASSED!")
    print("   You're ready to run the pipeline:")
    print("   python3 standalone_unstructured_pipeline.py <file1.pdf> <file2.txt> ...")
else:
    print(" Some issues detected - review above")
    print("   Install missing dependencies from requirements_qwen3vl.txt")

print("="*80)
