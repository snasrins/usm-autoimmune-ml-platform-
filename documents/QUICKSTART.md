# 🚀 QUICK START GUIDE - Unstructured Pipeline on GPU
**Model**: Qwen3-VL-4B-Thinking (4B parameters, ~8-10GB VRAM)  
**Target**: PDF and TXT medical documents  
**No Docker** - Direct Python installation  
**Date**: March 24, 2026

---

## ⚡ 5-Minute Setup (Copy-Paste These Commands)

### On GPU Server (ssh shaggy@gpulab1)

```bash
# 1. Navigate to project
cd ~/usm-autoimmune-ml-platform  # adjust path if needed

# 2. Create virtual environment
python3 -m venv venv_qwen3
source venv_qwen3/bin/activate

# 3. Install dependencies (takes 5-10 min on first run)
pip install --upgrade pip
pip install -r requirements_qwen3vl.txt

# 4. Verify GPU is ready
python3 check_gpu_ready.py

# 5. Create test documents
python3 test_sample_documents.py

# 6. Run pipeline on test files
python3 standalone_unstructured_pipeline.py ./test_documents/*.txt
```

**Done!** Results will be in `./pipeline_output/`

---

## 📊 What to Expect

### First Run (Cold Start)
- **Time**: 10-15 minutes total
  - Model download: 5-10 min (downloads ~10GB Qwen3-VL-4B-Thinking)
  - Processing 3 test TXT files: ~30 seconds
- **VRAM**: ~8-10 GB allocated
- **Storage**: ~10-12 GB (model cache)

### Subsequent Runs (Warm Start)
- **Time**: ~10-20 seconds per page (OCR required)
- **VRAM**: Same ~8-10 GB (model stays loaded)
- **Storage**: Minimal (~few MB per document processed)

### Terminal Output Preview

```
================================================================================
🏥 USM AUTOIMMUNE - UNSTRUCTURED DATA PIPELINE
================================================================================
📅 Date: 2026-03-24 10:30:45
🎮 GPU: NVIDIA GeForce RTX 3090
================================================================================

📊 CHECKPOINT: INITIALIZATION
⏱️  Time Elapsed: 0.00s
================================================================================
🎮 GPU VRAM:
   Allocated: 0.00 MB (0.00 GB)
   Free:      24576.00 MB (24.00 GB)
   Usage:     0.0%

💾 STORAGE:
   Used:   45.23 GB
   Free:   954.77 GB
   Usage:  4.5%
================================================================================

🚀 Loading Qwen/Qwen3-VL-4B-Thinking...
   Step 1/2: Loading processor...
   Step 2/2: Loading model...
✅ Qwen3-VL-4B-Thinking loaded on cuda
   Model VRAM: 8192.00 MB (8.00 GB)

📊 CHECKPOINT: MODEL_LOADED
🎮 GPU VRAM:
   Allocated: 8192.00 MB (8.00 GB)
   Usage:     33.3%
   Free:      16384.00 MB (16.00 GB) - Plenty of headroom!

📄 Processing TXT: sample_clinical_note.txt
✅ TXT processed: 2456 characters
   Time: 0.15s

📄 Processing TXT: sample_lab_report.txt
✅ TXT processed: 3789 characters
   Time: 0.12s

📊 PROCESSING SUMMARY
================================================================================
Total files processed: 2
Success: 2
GPU VRAM used: 8245.50 MB (8.05 GB)
Storage consumed: 0.002 GB
================================================================================
```

---

## 🎯 Files You Need

All files are ready in your workspace:

| File | Purpose | Size |
|------|---------|------|
| `standalone_unstructured_pipeline.py` | Main pipeline script | ~15 KB |
| `requirements_qwen3vl.txt` | Dependencies | ~1 KB |
| `check_gpu_ready.py` | Pre-flight checks | ~5 KB |
| `test_sample_documents.py` | Generate test data | ~8 KB |
| `RUN_ON_GPU.md` | Detailed instructions | ~10 KB |
| `QUICKSTART.md` | This file | ~5 KB |

---

## 🎬 Step-by-Step Execution

### Step 1: Connect & Verify

```bash
# From Windows
ssh shaggy@<GPU_IP>

# Once connected
nvidia-smi  # Check GPU is free (should show ~1 MiB usage)
```

### Step 2: Setup Environment

```bash
cd ~/usm-autoimmune-ml-platform
python3 -m venv venv_qwen3
source venv_qwen3/bin/activate
pip install --upgrade pip
pip install -r requirements_qwen3vl.txt  # Takes 5-10 min
```

### Step 3: Verify Setup

```bash
python3 check_gpu_ready.py
# Answer 'n' to skip model download test (or 'y' to test now)
```

### Step 4: Create Test Data

```bash
python3 test_sample_documents.py
# Creates ./test_documents/ with 4 sample TXT files
```

### Step 5: Run Pipeline

```bash
# Process test files
python3 standalone_unstructured_pipeline.py ./test_documents/*.txt

# Watch in real-time (open separate terminal)
watch -n 1 nvidia-smi
```

### Step 6: Check Results

```bash
# View results
cat pipeline_output/results_*.json

# View resource usage
cat pipeline_output/resource_usage.log

# Check storage
du -sh ~/.cache/huggingface/  # Model cache (~10GB)
du -sh pipeline_output/         # Processing outputs (~few MB)
```

---

## 📈 Resource Monitoring Commands

### Monitor GPU VRAM (Real-Time)

```bash
# Option 1: nvidia-smi (refreshes every 1 second)
watch -n 1 nvidia-smi

# Option 2: Continuous output
while true; do clear; nvidia-smi; sleep 1; done

# Option 3: Just memory
nvidia-smi --query-gpu=memory.used,memory.total --format=csv -l 1
```

### Monitor Storage

```bash
# Disk usage
df -h

# Model cache size
du -sh ~/.cache/huggingface/

# Output directory size
du -sh pipeline_output/

# Watch storage in real-time
watch -n 5 "df -h | grep -E 'Filesystem|/$'"
```

### System Resources

```bash
# CPU and RAM
htop  # or top

# Everything at once (requires tmux)
tmux  # split panes and run nvidia-smi, htop, tail -f resource_usage.log
```

---

## ✅ Success Checklist

After running, verify:

- [ ] Model loaded successfully (see "✅ Qwen3-VL-4B-Thinking loaded on cuda")
- [ ] VRAM usage shown (should be ~8-10 GB, <50% of 24GB)
- [ ] All test files processed (3-4 TXT files)
- [ ] Results JSON created in `pipeline_output/`
- [ ] Resource log created with checkpoints
- [ ] Storage consumption logged
- [ ] No CUDA out-of-memory errors

**If all checked**: You're ready to process real medical documents!

---

## 🐛 Common Issues

### "CUDA not available"
```bash
# Check if NVIDIA drivers installed
nvidia-smi

# Check PyTorch installation
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### "Model download failed"
```bash
# Check internet
ping huggingface.co

# Set proxy if needed
export http_proxy=http://proxy:port
export https_proxy=http://proxy:port
```

### "Out of memory"
```bash
# Clear GPU cache
python3 -c "import torch; torch.cuda.empty_cache()"

# Check what's using GPU
nvidia-smi

# Kill other GPU processes if needed
kill <PID>
```

### "/tmp/ permission denied"
```bash
# Create user-specific temp directory
mkdir -p ~/tmp
# Edit standalone_unstructured_pipeline.py line 207:
# Change: temp_path = f"/tmp/page_{page_num}_{int(time.time())}.png"
# To:     temp_path = f"~/tmp/page_{page_num}_{int(time.time())}.png"
```

---

## 🔄 Transfer Files to GPU Server

### Option 1: WinSCP (GUI)

1. Open WinSCP
2. Connect to: `shaggy@<GPU_IP>`
3. Navigate to: `/home/shaggy/usm-autoimmune-ml-platform/`
4. Upload files:
   - `standalone_unstructured_pipeline.py`
   - `requirements_qwen3vl.txt`
   - `check_gpu_ready.py`
   - `test_sample_documents.py`
   - `RUN_ON_GPU.md`
   - `QUICKSTART.md`

### Option 2: SCP (Command Line)

```powershell
# From Windows PowerShell
cd C:\Users\Syarifah\usm-autoimmune-ml-platform

scp standalone_unstructured_pipeline.py shaggy@<GPU_IP>:~/usm-autoimmune-ml-platform/
scp requirements_qwen3vl.txt shaggy@<GPU_IP>:~/usm-autoimmune-ml-platform/
scp check_gpu_ready.py shaggy@<GPU_IP>:~/usm-autoimmune-ml-platform/
scp test_sample_documents.py shaggy@<GPU_IP>:~/usm-autoimmune-ml-platform/
scp RUN_ON_GPU.md shaggy@<GPU_IP>:~/usm-autoimmune-ml-platform/
scp QUICKSTART.md shaggy@<GPU_IP>:~/usm-autoimmune-ml-platform/
```

### Option 3: Git (if repository exists)

```bash
# On Windows: commit and push
git add standalone_unstructured_pipeline.py requirements_qwen3vl.txt check_gpu_ready.py test_sample_documents.py
git commit -m "Add standalone Qwen3-VL-4B pipeline with VRAM monitoring"
git push

# On GPU server: pull
git pull origin main
```

---

## 📞 Need Help?

**Refer to**:
- Detailed instructions: [RUN_ON_GPU.md](RUN_ON_GPU.md)
- Troubleshooting: See section above
- Model documentation: https://huggingface.co/Qwen/Qwen3-VL-4B-Thinking

**Contact**:
- Data Engineer: Syarifah Fajriyah
- For GPU issues: IT Admin

---

## 🎯 Next Steps (After Successful Test)

1. **Document results**:
   - Note VRAM consumption (should be ~8-10 GB)
   - Note processing speed (seconds per page)
   - Save resource_usage.log for review

2. **Test with real data**:
   - Process actual patient PDFs
   - Verify medical entity extraction accuracy
   - Check confidence scores

3. **Deploy to main GPU** (172.24.175.24 when stable):
   - Transfer working code
   - Build FastAPI endpoints
   - Integrate with PostgreSQL

4. **Architecture revision**:
   - Update diagrams with Qwen3-VL-4B-Thinking specs
   - Document resource requirements
   - Plan scaling (batch processing, queue system)

5. **Draw.io schema**:
   - Visualize Snowflake schema
   - Show unstructured data flow
   - Highlight fact_disease_specific_data table

6. **Snapshot implementation**:
   - Database backup strategy
   - Model versioning
   - Pipeline state checkpoints

---

**Ready to start!** 🚀
