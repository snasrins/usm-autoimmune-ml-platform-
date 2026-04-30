# Running Unstructured Pipeline on GPU Server
**Model**: Qwen3-VL-4B-Thinking  
**GPU**: NVIDIA RTX 3090 24GB (shaggy@gpulab1)  
**Purpose**: Test unstructured PDF/TXT processing with VRAM monitoring  
**Date**: March 24, 2026

---

## 🎯 Goal Today (Priority Order)

1. **FIRST PRIORITY**: Run unstructured data PDF and TXT processing
   - PDF: Lab reports, clinical notes, discharge summaries
   - TXT: Clinical notes (no handwritten notes)
   - Monitor VRAM and storage consumption

2. Revise architecture (later)
3. Draw schema design on draw.io (later)
4. Snapshot implementation (later)

---

## 📋 Step-by-Step Setup

### Step 1: Connect to GPU Server

**From Windows (PowerShell/CMD):**
```powershell
# Test connection first
ping <GPU_SERVER_IP>

# Connect via SSH
ssh shaggy@<GPU_SERVER_IP>

# Or use PuTTY if preferred
```

### Step 2: Check GPU Status

```bash
# Verify GPU is available
nvidia-smi

# Expected output:
# - GPU: NVIDIA GeForce RTX 3090
# - Memory: ~1 MiB / 24576 MiB (should be mostly free)
# - CUDA Version: 12.8
```

### Step 3: Setup Python Environment

```bash
# Navigate to your workspace
cd ~/usm-autoimmune-ml-platform  # or wherever you want to work

# Create virtual environment (recommended)
python3 -m venv venv_qwen3
source venv_qwen3/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements_qwen3vl.txt

# This will download Qwen3-VL-4B-Thinking (~8-10GB model)
# Be patient - first run takes 5-10 minutes to download
```

**IMPORTANT**: On first run, the model will be downloaded from HuggingFace:
- Model size: ~8-10 GB
- Cache location: `~/.cache/huggingface/hub/`
- Download time: 5-10 minutes (depends on network)

### Step 4: Verify Installation

```bash
# Check PyTorch can see GPU
python3 -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}')"

# Expected output:
# CUDA Available: True
# GPU: NVIDIA GeForce RTX 3090
```

---

## 🚀 Running the Pipeline

### Process Single PDF

```bash
python3 standalone_unstructured_pipeline.py /path/to/patient_report.pdf
```

### Process Multiple Files

```bash
python3 standalone_unstructured_pipeline.py \
    patient1_report.pdf \
    patient2_notes.txt \
    lab_results.pdf
```

### Process All PDFs in a Directory

```bash
python3 standalone_unstructured_pipeline.py ./medical_docs/*.pdf
```

### Output You'll See

```
================================================================================
🏥 USM AUTOIMMUNE - UNSTRUCTURED DATA PIPELINE
================================================================================
📅 Date: 2026-03-24 10:30:00
🎮 GPU: NVIDIA GeForce RTX 3090
================================================================================

📊 CHECKPOINT: INITIALIZATION
⏱️  Time Elapsed: 0.00s
================================================================================
🎮 GPU VRAM:
   Allocated: 0.00 MB (0.00 GB)
   Reserved:  0.00 MB (0.00 GB)
   Free:      24576.00 MB (24.00 GB)
   Total:     24576.00 MB (24.00 GB)
   Usage:     0.0%

💾 STORAGE:
   Used:   45.23 GB
   Free:   954.77 GB
   Total:  1000.00 GB
   Usage:  4.5%
================================================================================

🚀 Loading Qwen/Qwen3-VL-4B-Thinking...
   This may take 2-3 minutes on first run (downloading model)...
   Step 1/2: Loading processor...
   Step 2/2: Loading model...
✅ Qwen3-VL-4B-Thinking loaded on cuda
   Model VRAM: 8192.00 MB (8.00 GB)

📊 CHECKPOINT: MODEL_LOADED
================================================================================
🎮 GPU VRAM:
   Allocated: 8192.00 MB (8.00 GB)
   Reserved:  8300.00 MB (8.11 GB)
   Free:      16276.00 MB (15.89 GB)
   Total:     24576.00 MB (24.00 GB)
   Usage:     33.3%
================================================================================

📑 Processing PDF: patient_report.pdf
   Step 1: Native PDF text extraction...
   Found 3 pages
   ✓ Page 1: 1234 chars (native)
   ✓ Page 2: 2345 chars (native)
   ⚠️ Page 3: Poor text quality, needs OCR

   Step 2: Running Qwen3-VL-4B-Thinking OCR on 1 pages...
   🔍 OCR Page 3...
   ✓ Page 3: 1890 chars (Qwen3-VL, conf=0.87)

✅ PDF processed successfully!
   Total text: 5469 characters
   Avg confidence: 92.33%
   Medical entities: 5
   Processing time: 15.45s

... (continues for each file)
```

---

## 📊 Monitoring Resource Usage

### Real-Time GPU Monitoring (Run in separate terminal)

```bash
# Watch GPU usage in real-time
watch -n 1 nvidia-smi

# OR for continuous output
while true; do clear; nvidia-smi; sleep 1; done
```

### Check Pipeline Resource Log

```bash
# View resource usage log
cat pipeline_output/resource_usage.log

# Monitor in real-time while pipeline runs
tail -f pipeline_output/resource_usage.log
```

### Check Storage Consumption

```bash
# Before running
df -h

# After running
df -h

# Check HuggingFace cache size
du -sh ~/.cache/huggingface/
```

---

## 📁 Output Files

After running, you'll find in `./pipeline_output/`:

1. **`results_YYYYMMDD_HHMMSS.json`** - Processing results for all files
   ```json
   [
     {
       "filename": "patient_report.pdf",
       "file_type": "pdf",
       "status": "success",
       "extracted_text": "PATIENT NAME: Ahmad...",
       "confidence": 0.923,
       "page_count": 3,
       "medical_entities": [
         {"type": "disease", "value": "SLE", "confidence": 0.95},
         {"type": "lab_test", "value": "Anti-dsDNA: 300 IU/ml", "confidence": 0.92}
       ],
       "processing_time": 15.45,
       "vram_used_mb": 8245.5
     }
   ]
   ```

2. **`resource_usage.log`** - Detailed VRAM and storage tracking at each checkpoint

---

## 🔧 Troubleshooting

### Issue: CUDA Out of Memory

```bash
# Clear GPU cache
python3 -c "import torch; torch.cuda.empty_cache()"

# Check what's using GPU
nvidia-smi
```

**Solution**: Qwen3-VL-4B-Thinking uses ~8-10GB VRAM. RTX 3090 has 24GB, so should be fine. If OOM occurs, check if other processes are using GPU.

### Issue: Model Download Fails

```bash
# Check internet connection
ping huggingface.co

# Manually download model
python3 -c "from transformers import AutoProcessor; AutoProcessor.from_pretrained('Qwen/Qwen3-VL-4B-Thinking', trust_remote_code=True)"
```

### Issue: PDF Libraries Missing

```bash
# Install system dependencies (Ubuntu)
sudo apt-get update
sudo apt-get install -y poppler-utils

# Then reinstall Python packages
pip install pdf2image pdfplumber PyMuPDF
```

### Issue: Permission Denied on /tmp/

```bash
# Change temp directory in script, or ensure /tmp is writable
chmod 777 /tmp
```

---

## 📈 Expected Resource Consumption

Based on Qwen3-VL-4B-Thinking specifications:

| Resource | Usage | Notes |
|----------|-------|-------|
| **GPU VRAM** | ~8-10 GB | Model loading + inference |
| **RAM** | ~4-6 GB | Image processing, text storage |
| **Storage** | ~10-12 GB | Model cache (~10GB) + outputs (~2GB for 1000 docs) |
| **Processing Speed** | ~10-20s/page | For OCR-required pages |

**Safe for RTX 3090 24GB**: Yes, leaves ~14-16GB VRAM free

---

## ✅ Success Criteria

1. **Model loads successfully** - See "✅ Qwen3-VL-4B-Thinking loaded on cuda"
2. **VRAM < 12 GB** - Should use ~8-10GB, well within 24GB limit
3. **PDF text extraction works** - See extracted text in terminal
4. **TXT processing works** - See text content parsed
5. **Medical entities detected** - See JSON entities in output
6. **Resource log created** - Check `pipeline_output/resource_usage.log`
7. **Results JSON saved** - Check `pipeline_output/results_*.json`

---

## 🔄 Next Steps (After Successful Test)

1. **If everything works on this GPU**:
   - Document exact VRAM and storage usage
   - Test with various PDF types (scanned vs native text)
   - Test with different page counts (1-page vs 50-page PDFs)

2. **Deploy to main GPU (172.24.175.24)** when stable:
   - Transfer code to main server
   - Install same dependencies
   - Build FastAPI endpoints around this processing logic
   - Integrate with MinIO and PostgreSQL

3. **Architecture revision**:
   - Update diagrams with Qwen3-VL-4B-Thinking
   - Document resource requirements
   - Plan scaling strategy

4. **Schema design** (draw.io):
   - Visual representation of Snowflake schema
   - Show unstructured data flow
   - Highlight fact_disease_specific_data table

5. **Snapshot implementation**:
   - Database snapshots for backups
   - Model versioning
   - Pipeline state checkpoints

---

## 📞 Support

For issues, contact:
- Data Engineer: Syarifah Fajriyah
- Supervisor: [SV Name]
- IT Admin: [For GPU server issues]
