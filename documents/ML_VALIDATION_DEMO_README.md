# ML Validation Demo Scripts
## For TSD Documentation Screenshots

These scripts demonstrate the ML pipeline's data validation safeguards.

---

## 📁 Available Scripts

### 1. **test_ml_validation.py** - Detailed Validation Check
**Use this for:** Showing all individual validation checks

**Output includes:**
- ✅/❌/⚠️ status for each check
- MIN_SAMPLES check (shows if < 30 samples per class)
- LABEL_BALANCE check (class distribution)
- FEATURE_VARIANCE check
- TARGET_ENCODING check
- Detailed recommendations

**Best for:** USMA-102, USMA-103, USMA-106 screenshots

---

### 2. **demo_training_attempt.py** - Full Training Flow
**Use this for:** Showing the complete "Click Train → Validation → Block" flow

**Output includes:**
- [1/5] Initializing pipeline
- [2/5] Loading dataset
- [3/5] Running validation
- [4/5] Training decision
- [5/5] Either: Training starts OR Training blocked

**Best for:** Demonstrating ML training safeguards in action

---

## 🚀 How to Run

### Option 1: PowerShell (Recommended for Screenshots)

```powershell
# Navigate to project directory
cd C:\Users\Syarifah\usm-autoimmune-ml-platform

# Run validation check
python test_ml_validation.py

# OR run training attempt demo
python demo_training_attempt.py
```

### Option 2: Using your existing terminal
```powershell
# If FastAPI server is running, use a separate terminal window
# These scripts run independently of the server

python test_ml_validation.py
```

---

## 📸 Screenshot Tips

1. **Clear your terminal** before running:
   ```powershell
   cls
   ```

2. **Run the script**:
   ```powershell
   python demo_training_attempt.py
   ```

3. **Take screenshot** when output shows:
   - "⛔ TRAINING BLOCKED" header
   - List of failed validation checks
   - Recommendations

4. **For better visibility**, you can zoom terminal:
   - Press `Ctrl` + Mouse Wheel to zoom in
   - Or `Ctrl` + `+` to increase font size

---

## 🎯 Expected Output

### If data is sufficient (unlikely with test data):
```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ✓ TRAINING STARTED SUCCESSFULLY                           ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### If data is insufficient (expected):
```
╔══════════════════════════════════════════════════════════════════════════════╗
║                ⛔ TRAINING BLOCKED - DATA VALIDATION FAILED                   ║
╚══════════════════════════════════════════════════════════════════════════════╝

📋 SUMMARY:
   • Total records: 28
   • Validation checks run: 5
   • Checks passed: 3
   • Checks failed: 2
   • Training status: BLOCKED

❌ FAIL - MIN_SAMPLES
   Details: Insufficient samples. Need 30 per class, have 14
   💡 Recommendation: Collect at least 16 more labeled samples before training

❌ FAIL - LABEL_BALANCE
   Details: Class imbalance ratio: 4.5 (threshold: 10.0)
   💡 Recommendation: Balance dataset or use class_weight parameter

💡 WHY THIS MATTERS:
   Training a model on insufficient or poor-quality data would result in:
   • Overfitting and poor generalization
   • Unreliable predictions on new patients
   • Potential medical misdiagnosis
   • Wasted computational resources

✓ This validation system ensures safe, reliable ML model development
```

---

## 🔧 Customization

### Change minimum samples requirement:
Edit the script and change:
```python
result = validator.validate_for_ml_training(
    batch_id=batch_id,
    target_column='labels_disease_classification',
    min_samples_per_class=30  # ← Change this number
)
```

### Use a specific batch ID:
Replace the auto-detection with:
```python
batch_id = uuid.UUID('your-batch-id-here')
```

---

## 📋 TSD Sections This Covers

- **USMA-102**: ML Data Validation Service
- **USMA-103**: Target column encoding fixes
- **USMA-106**: Data quality pre-checks
- **3.4.4**: ML Data Validation screenshots

---

## ⚠️ Troubleshooting

### Error: "No datasets found"
- Make sure you have uploaded data through the frontend
- Check database has records in `flexible_dataset_wide` table

### Error: "Module not found"
- Make sure you're in the project root directory
- Activate virtual environment if using one

### Error: "Database connection failed"
- Check if PostgreSQL is running
- Check `.env` file has correct database credentials

---

## 📝 What This Demonstrates

These scripts prove that your ML pipeline has **professional-grade safeguards**:

1. ✅ Data is validated BEFORE training (not after)
2. ✅ Minimum sample requirements enforced (30 per class)
3. ✅ Class balance checked
4. ✅ Feature quality verified
5. ✅ Clear error messages with actionable recommendations
6. ✅ Training blocked if requirements not met

This prevents:
- ❌ Wasting GPU resources on bad data
- ❌ Training overfitted models
- ❌ Deploying unreliable medical AI
- ❌ Hours of debugging failed training runs
