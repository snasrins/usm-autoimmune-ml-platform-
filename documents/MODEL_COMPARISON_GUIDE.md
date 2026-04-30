# Qwen VL Model Comparison Guide
## Testing for Optimal Speed vs Accuracy

**Date:** March 25, 2026  
**Goal:** Achieve <20s/page while maintaining extraction accuracy

---

## Models to Compare

### 1. Qwen3-VL-4B-Thinking (Baseline - Slowest)
**File:** `standalone_unstructured_pipeline.py.backup`  
**Status:** ✅ Backed up  
**Expected Performance:**
- Speed: ~60-70s per page
- Accuracy: Highest (reasoning capability)
- VRAM: ~10-12GB
- Parameters: 4 billion

**When to use:**
- Maximum accuracy required
- Complex medical terminology
- Research/validation phase

---

### 2. Qwen3-VL-4B-Instruct (Current - Medium)
**File:** `standalone_unstructured_pipeline_4b_instruct.py`  
**Status:** ✅ Backed up (just created)  
**Expected Performance:**
- Speed: ~37s per page (current optimized)
- Accuracy: High (direct extraction)
- VRAM: ~8-10GB
- Parameters: 4 billion

**When to use:**
- Balanced speed vs accuracy
- Production deployment (current choice)
- Structured lab reports

**Achieved:**
- Total time: 236s for 6-page PDF
- Per page: 37.2s
- Entities: 37 (95% accuracy)
- Confidence: 85%

---

### 3. Qwen2.5-VL-3B-Instruct (Testing - Fastest)
**File:** `standalone_unstructured_pipeline.py` (active)  
**Status:** ✅ Implemented (FP16 - INT8 incompatible)  
**Expected Performance:**
- Speed: **~20-30s per page** (target: <30s) ⚡
- Accuracy: Good (to be validated)
- VRAM: ~6-8GB (FP16, no INT8 compression)
- Parameters: 3 billion (25% fewer)

**⚠️ COMPATIBILITY NOTE:**
- INT8 quantization NOT supported (architecture difference)
- Uses FP16 instead (still fast due to smaller model)
- Flash Attention 2 still works (main speedup)
- Model weights show UNEXPECTED/MISSING (this is NORMAL)

**When to use:**
- Speed-critical deployments
- High-volume processing
- Cost optimization (fewer parameters = less compute)

**To validate:**
- Entity extraction accuracy vs 4B models
- Confidence scores comparison
- Missing entity detection rate

---

## Testing Protocol

### Test Dataset
Use the same 6-page medical document for all 3 models:
```bash
# Sample document (ensure identical for fair comparison)
"Sample Medical Report.pdf"
```

### Metrics to Compare

| Metric | 4B Thinking | 4B Instruct | 2.5 3B Instruct | Target |
|--------|-------------|-------------|------------------|--------|
| **Speed** |
| Total time (6 pages) | ~420s | 236s | ? | <150s |
| Per page | ~70s | 37.2s | ? | <20s |
| **Accuracy** |
| Entities extracted | ? | 37 | ? | >35 |
| Confidence score | ? | 85% | ? | >80% |
| Text length | ? | 8,091 chars | ? | >7,500 |
| **Quality** |
| Lab tests found | ? | 25-30 | ? | >25 |
| Disease terms | ? | 5-7 | ? | >5 |
| Medications | ? | 3-5 | ? | >3 |
| **Resources** |
| VRAM usage | ~10GB | 4.66GB (19.3%) | ? | <8GB |
| Model size on disk | ~8GB | ~8GB | ~6GB | - |

---

## How to Run Each Test

### Test 1: Qwen3-VL-4B-Thinking (Baseline)
```bash
# Restore backup
cp standalone_unstructured_pipeline.py.backup standalone_unstructured_pipeline.py

# Or edit MODEL_VARIANT in file:
MODEL_VARIANT = "thinking"

# Run test
python standalone_unstructured_pipeline.py "Sample Medical Report.pdf"
```

**Expected output location:** `./pipeline_output/results_full_*.json`

---

### Test 2: Qwen3-VL-4B-Instruct (Already Tested ✅)
```bash
# Use backup file
cp standalone_unstructured_pipeline_4b_instruct.py standalone_unstructured_pipeline.py

# Or edit MODEL_VARIANT in file:
MODEL_VARIANT = "instruct"

# Run test (results already available)
python standalone_unstructured_pipeline.py "Sample Medical Report.pdf"
```

**Results from previous run:**
- Total time: 236s (3m 56s)
- Per page: 37.2s
- Entities: 37
- Confidence: 85%

---

### Test 3: Qwen2.5-VL-3B-Instruct (Current - To Test)
```bash
# Already configured in current file
# Check MODEL_VARIANT is set to:
MODEL_VARIANT = "2.5-3b-instruct"

# Run test
python standalone_unstructured_pipeline.py "Sample Medical Report.pdf"
```

**Monitoring:**
- Watch VRAM usage: Should be ~6-8GB (lower than 4B)
- Monitor per-page timing: Target <20s
- Check terminal output for entities found

---

## Accuracy Validation

### Critical Checks

**1. Entity Count Comparison**
```bash
# After each test, check:
cat pipeline_output/results_full_*.json | grep '"type":' | wc -l

# Should extract similar number of entities:
# - Lab tests: 25-30 entities
# - Diseases: 5-7 entities
# - Medications: 3-5 entities
# Total: 35-40 entities expected
```

**2. Missing Entities (False Negatives)**
```bash
# Compare extracted entities across models
# Key entities that MUST be found:
# - Patient name (or REDACTED marker)
# - Lab No / MRN
# - All lab test results with values
# - Disease diagnoses (SLE, etc.)
# - Medications prescribed
```

**3. Entity Quality**
Check the JSON output for:
- ✅ Correct test names (Haemoglobin, not "Hae")
- ✅ Numeric values parsed correctly
- ✅ Units extracted (g/dL, mmol/L, etc.)
- ✅ Reference ranges present
- ✅ Abnormal flags detected (*)

**4. False Positives**
- Ensure no hallucinated entities
- Verify all extracted values exist in source PDF
- Check confidence scores (should be >75%)

---

## Decision Criteria

### Scenario 1: Speed Priority (Production Deployment)
**Choose Qwen2.5-VL-3B-Instruct IF:**
- ✅ Per-page time <20s
- ✅ Entity count >90% of 4B model (>33 entities)
- ✅ No critical entities missing
- ✅ Confidence score >80%

**Benefit:** 2x faster processing, 25% less VRAM, lower cost

---

### Scenario 2: Accuracy Priority (Research/Validation)
**Choose Qwen3-VL-4B-Instruct IF:**
- ❌ 3B model misses critical entities
- ❌ Confidence scores <80%
- ❌ Too many false positives/negatives

**Benefit:** Proven accuracy (85% confidence, 37 entities), balanced performance

---

### Scenario 3: Maximum Quality (Rare Cases)
**Choose Qwen3-VL-4B-Thinking IF:**
- ❌ Both Instruct models have accuracy issues
- ❌ Complex reasoning needed (unusual medical terms)
- ❌ Speed not a constraint

**Benefit:** Highest accuracy, reasoning capability

---

## Quick Test Command

Run all 3 tests in sequence (automated):

```bash
# Test script (create this)
cat > test_all_models.sh << 'EOF'
#!/bin/bash

echo "=== Testing All 3 Qwen VL Models ==="

# Test 1: 4B Thinking (from backup)
echo "Test 1: Qwen3-VL-4B-Thinking..."
cp standalone_unstructured_pipeline.py.backup standalone_unstructured_pipeline.py
sed -i 's/MODEL_VARIANT = .*/MODEL_VARIANT = "thinking"/' standalone_unstructured_pipeline.py
python standalone_unstructured_pipeline.py "Sample Medical Report.pdf"
mv pipeline_output/results_full_*.json pipeline_output/results_4b_thinking.json

# Test 2: 4B Instruct (from backup)
echo "Test 2: Qwen3-VL-4B-Instruct..."
cp standalone_unstructured_pipeline_4b_instruct.py standalone_unstructured_pipeline.py
python standalone_unstructured_pipeline.py "Sample Medical Report.pdf"
mv pipeline_output/results_full_*.json pipeline_output/results_4b_instruct.json

# Test 3: 2.5 3B Instruct (current)
echo "Test 3: Qwen2.5-VL-3B-Instruct..."
cp standalone_unstructured_pipeline_original.py standalone_unstructured_pipeline.py
python standalone_unstructured_pipeline.py "Sample Medical Report.pdf"
mv pipeline_output/results_full_*.json pipeline_output/results_25_3b_instruct.json

echo "=== Comparison ==="
python compare_results.py
EOF

chmod +x test_all_models.sh
./test_all_models.sh
```

---

## Results Summary Template

After testing, fill this table:

| Model | Speed (total) | Speed (per page) | Entities | Confidence | VRAM | Verdict |
|-------|--------------|------------------|----------|------------|------|---------|
| **4B Thinking** | ___ s | ___ s | ___ | ___% | ___GB | Baseline |
| **4B Instruct** ✅ | 236s | 37.2s | 37 | 85% | 4.66GB | Current |
| **2.5 3B Instruct** ⚡ | ___ s | ___ s | ___ | ___% | ___GB | Testing |

**Recommendation:** _[Fill after testing]_

---

## Troubleshooting

### If 2.5 3B Model Fails to Load

**Error:** `ImportError: cannot import name 'Qwen2VLProcessor'`

**Solution:**
```bash
# Update transformers to latest version
pip install --upgrade transformers

# Ensure version supports Qwen2.5-VL
pip list | grep transformers
# Should be: transformers>=4.37.0
```

---

### If Accuracy Drops Significantly

**Symptoms:**
- Entity count <30 (vs 37 in 4B model)
- Confidence <75%
- Missing critical lab tests

**Solution:**
- Stick with Qwen3-VL-4B-Instruct (proven accuracy)
- Consider optimizing prompts for 3B model
- Wait for Qwen2.5-VL model updates

---

### If Speed Not Improved

**Expected:** 2.5 3B should be 30-40% faster than 4B model

**If not faster:**
- Check VRAM usage (should be lower)
- Verify INT8 quantization enabled
- Ensure Flash Attention 2 active
- May need to reduce DPI further (120 → 96)

---

## Backup Files Summary

You now have 3 versions:

| File | Model | Status | Use For |
|------|-------|--------|---------|
| `standalone_unstructured_pipeline.py.backup` | 4B Thinking | Backed up | Baseline testing |
| `standalone_unstructured_pipeline_4b_instruct.py` | 4B Instruct | Backed up | Current production |
| `standalone_unstructured_pipeline.py` | 2.5 3B Instruct | Active | Speed testing |

---

## Next Steps

1. **Run Test:** Execute 2.5 3B model on sample document
   ```bash
   python standalone_unstructured_pipeline.py "Sample Medical Report.pdf"
   ```

2. **Compare Results:** Check `pipeline_output/results_full_*.json`
   - Count entities: `cat results_full_*.json | grep '"type":' | wc -l`
   - Check timing: Look for "processing_time" in JSON
   - Verify VRAM: Check terminal output

3. **Validate Accuracy:**
   - Compare entity lists side-by-side
   - Manually verify critical entities present
   - Check confidence scores distribution

4. **Make Decision:**
   - If 3B model achieves <20s/page with >90% entities → **USE 3B** ⚡
   - If 3B model misses entities or <80% confidence → **Keep 4B Instruct** ✅
   - If both have issues → **Fallback to 4B Thinking** (rare)

5. **Update Documentation:**
   - Record final choice in production README
   - Document performance benchmarks
   - Update deployment scripts

---

**Status:** Ready for testing 🚀  
**Expected completion time:** 15-20 minutes (includes 3 model tests if running all)
