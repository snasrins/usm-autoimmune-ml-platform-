# 🎯 Frontend-Backend Integration - Complete Wiring Summary

**Date:** April 22, 2026  
**Status:** ✅ Ready to implement  
**Estimated Time:** 2-3 days for full integration

---

## 📦 **WHAT I'VE CREATED FOR YOU**

### **1. Complete API Wrapper**
**File:** `frontend/src/services/api-complete.js`

All backend endpoints wrapped and ready to use:
- ✅ **unstructuredPipelineAPI** - PDF/Image → Qwen OCR → Tabular
- ✅ **structuredPipelineAPI** - CSV/Excel → Preview → Edit
- ✅ **preprocessingAPI** - Data quality, missing values, outliers, normalization
- ✅ **labelingAPI** - Assign labels, bulk operations, statistics
- ✅ **mlPreparationAPI** - Validate, prepare dataset for training
- ✅ **edaAPI** - Statistical analysis, correlations, distributions
- ✅ **trainingAPI** - Train models, poll status, compare results
- ✅ **scorecardAPI** - Generate scorecard, bin tables, patient scores, CSV export
- ✅ **explainabilityAPI** - SHAP values, LLM explanations
- ✅ **batchPredictionAPI** - Batch predictions, export results

### **2. Complete Pipeline Documentation**
**File:** `frontend/COMPLETE_PIPELINE_INTEGRATION.md`

Full end-to-end workflow from upload to scorecard with:
- Visual flow diagrams
- API call sequences
- State management guidance
- Session storage keys

### **3. Implementation Steps Guide**
**File:** `frontend/INTEGRATION_IMPLEMENTATION_STEPS.md`

Exact code changes for each page:
- Data Ingestion (unstructured + structured)
- Data Preparation (preview + preprocessing)
- Label Assignment
- Training Jobs (with polling)
- Model Comparison
- Clinical Scorecard

---

## 🔄 **THE TWO PIPELINES**

### **Pipeline A: Unstructured (PDF/Images)**
```
Upload PDF/Image 
    ↓ (Qwen OCR)
Review OCR Text
    ↓ (Convert)
Tabular Preview
    ↓ (same as Pipeline B from here)
```

### **Pipeline B: Structured (CSV/Excel)**
```
Upload CSV/Excel
    ↓ (Direct Preview)
```

### **Shared Pipeline (Both Merge Here)**
```
Preview & Edit Data
    ↓
Data Quality Check
    ↓
Apply Preprocessing
    ↓
Save to Database (→ batch_id)
    ↓
Label Assignment
    ↓
ML Validation
    ↓
(Optional) EDA
    ↓
Dataset Preparation
    ↓
Model Training (11 algorithms)
    ↓
Model Comparison
    ↓
Clinical Scorecard Generation
    ↓
🎉 COMPLETE!
```

---

## 🎯 **HOW TO IMPLEMENT**

### **Quick Start (30 minutes)**

1. **Copy API wrapper:**
```bash
# File already created: frontend/src/services/api-complete.js
# No action needed - it's ready!
```

2. **Update one page as proof of concept:**
Start with **ClinicalScorecardPage.jsx** (smallest change, biggest impact):

```javascript
// Add import
import { scorecardAPI } from '../services/api-complete';

// Replace mock data with real API call
const handleGenerateScorecard = async () => {
  try {
    const result = await scorecardAPI.generateScorecard(modelId, {
      binningMethod: 'rolling_mean',
      numBins: 4,
      useYouden: true
    });
    
    setScorecardId(result.scorecard_id);
    // ... rest of the code
  } catch (error) {
    console.error('Scorecard generation failed:', error);
  }
};
```

3. **Test it:**
```bash
cd frontend
npm run dev

# Navigate to Clinical Scorecard page
# Try generating a scorecard
# Check browser console for API calls
```

---

### **Full Implementation (2-3 days)**

**Day 1 Morning: Data Ingestion & Preparation**
- [ ] Update `DataIngestionPage.jsx` (2 hours)
  - Structured upload → uses `structuredPipelineAPI.uploadForPreview()`
  - Unstructured upload → uses `unstructuredPipelineAPI.uploadForOCR()`
  - Convert OCR → uses `unstructuredPipelineAPI.convertToTabular()`
- [ ] Update `DataPreparationPage.jsx` (2 hours)
  - Load preview → uses `structuredPipelineAPI.getPreview()`
  - Edit cells → uses `structuredPipelineAPI.editCell()`
  - Preprocessing → uses `preprocessingAPI.handleMissingValues()`, etc.
  - Save → uses `preprocessingAPI.savePreprocessed()`

**Day 1 Afternoon: Labeling**
- [ ] Update `LabelAssignmentPage.jsx` (3 hours)
  - Load unlabeled → uses `labelingAPI.getUnlabeledRecords()`
  - Assign labels → uses `labelingAPI.assignLabel()`
  - Bulk/batch → uses `labelingAPI.bulkAssignLabels()`
  - Validation → uses `mlPreparationAPI.validateForML()`

**Day 2 Morning: ML Training**
- [ ] Update `TrainingJobsPage.jsx` (3 hours)
  - Prepare dataset → uses `mlPreparationAPI.prepareDataset()`
  - Train models → uses `trainingAPI.trainBaseModel()` for each
  - Poll status → uses `trainingAPI.getJobStatus()` every 3s
  - Store results → collect model IDs

**Day 2 Afternoon: Model Comparison & Scorecard**
- [ ] Update `ModelComparisonPage.jsx` (2 hours)
  - Load comparison → uses `trainingAPI.compareModels()`
  - Select best model
- [ ] Update `ClinicalScorecardPage.jsx` (2 hours)
  - Generate → uses `scorecardAPI.generateScorecard()`
  - Load tables → uses `scorecardAPI.getBinScoreTables()`
  - Calculate scores → uses `scorecardAPI.calculatePatientScore()`
  - Export CSV → uses `scorecardAPI.exportScorecardCSV()`

**Day 3: Testing & Polish**
- [ ] End-to-end testing (3 hours)
- [ ] Error handling (2 hours)
- [ ] Loading states (1 hour)
- [ ] UI polish (2 hours)

---

## ✅ **VALIDATION CHECKLIST**

After each step, verify in **sessionStorage**:

```javascript
// After Data Ingestion:
sessionStorage.getItem('preview_session_id')  // Should be UUID

// After Data Preparation Save:
sessionStorage.getItem('current_batch_id')     // Should be UUID

// After Dataset Preparation:
sessionStorage.getItem('dataset_id')           // Should be string

// After Training:
sessionStorage.getItem('trained_model_ids')    // Should be JSON array

// After Comparison:
sessionStorage.getItem('best_model_id')        // Should be string

// After Scorecard:
sessionStorage.getItem('scorecard_id')         // Should be string
```

---

## 🔧 **COMMON ISSUES & SOLUTIONS**

### **Issue 1: CORS Errors**
**Solution:** Check `vite.config.js` proxy configuration:
```javascript
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://100.106.132.15:8001',
        changeOrigin: true,
        secure: false
      }
    }
  }
});
```

### **Issue 2: 401 Unauthorized**
**Solution:** Check token in localStorage:
```javascript
console.log('Token:', localStorage.getItem('access_token'));

// If missing, login first
navigate('/login');
```

### **Issue 3: API Returns 500**
**Solution:** Check backend logs:
```bash
docker logs usm-autoimmune-api --tail 50
```

### **Issue 4: Session ID Not Found**
**Solution:** Verify session storage:
```javascript
// Debug in browser console
console.log('Session ID:', sessionStorage.getItem('preview_session_id'));

// If missing, start from Data Ingestion
window.location.href = '/data-ingestion';
```

### **Issue 5: Polling Not Working**
**Solution:** Check interval cleanup:
```javascript
useEffect(() => {
  const interval = setInterval(pollStatus, 3000);
  return () => clearInterval(interval);  // MUST CLEANUP!
}, [jobId]);
```

---

## 📊 **API ENDPOINT MAPPING**

Quick reference for which API to use where:

| Page | Primary APIs Used |
|------|-------------------|
| **DataIngestionPage** | `structuredPipelineAPI`, `unstructuredPipelineAPI` |
| **DataPreparationPage** | `structuredPipelineAPI`, `preprocessingAPI` |
| **LabelAssignmentPage** | `labelingAPI`, `mlPreparationAPI` |
| **EDAExplorerPage** | `edaAPI` |
| **TrainingJobsPage** | `mlPreparationAPI`, `trainingAPI` |
| **ModelComparisonPage** | `trainingAPI` |
| **ClinicalScorecardPage** | `scorecardAPI` |
| **ModelExplainabilityPage** | `explainabilityAPI` |
| **BatchPredictionPage** | `batchPredictionAPI` |

---

## 🚀 **TESTING WORKFLOW**

### **End-to-End Test:**

1. **Upload CSV:**
   - Go to Data Ingestion
   - Upload `111_patients_wide.csv`
   - Should navigate to Data Preparation

2. **Preprocess:**
   - Should see preview loaded
   - Apply missing value imputation
   - Apply winsorization
   - Save to database
   - Should navigate to Label Assignment

3. **Label:**
   - Should load unlabeled records
   - Assign labels to some records
   - Run validation
   - Should pass with "can_proceed: true"
   - Navigate to Training

4. **Train:**
   - Prepare dataset
   - Select XGBoost, Logistic Regression
   - Start training
   - Watch progress bars update
   - Wait for completion

5. **Compare:**
   - Should show side-by-side metrics
   - Select best model
   - Navigate to Scorecard

6. **Generate Scorecard:**
   - Click generate
   - Should show bin tables
   - Should show risk stratification
   - Try patient calculator
   - Export CSV

---

## 💡 **PRO TIPS**

1. **Start Small:** Wire one page at a time, test thoroughly
2. **Use Browser DevTools:** Network tab shows API calls
3. **Check sessionStorage:** Verify IDs stored correctly
4. **Add Console Logs:** Debug state transitions
5. **Error Handling:** Wrap ALL API calls in try-catch
6. **Loading States:** Show spinners during async operations
7. **Polling Cleanup:** Always clear intervals on unmount

---

## 📞 **SUPPORT**

If you get stuck:

1. **Check the guides:**
   - `COMPLETE_PIPELINE_INTEGRATION.md` - Full workflow
   - `INTEGRATION_IMPLEMENTATION_STEPS.md` - Code examples

2. **Debug steps:**
   - Check browser console for errors
   - Check Network tab for failed API calls
   - Check sessionStorage for missing IDs
   - Check backend logs for server errors

3. **Common fixes:**
   - Clear sessionStorage and start fresh
   - Restart backend container
   - Hard refresh browser (Ctrl+Shift+R)
   - Check CORS configuration

---

## 🎉 **SUCCESS CRITERIA**

You know it's working when:

✅ Upload CSV → navigates to preview  
✅ Preview shows real data from backend  
✅ Preprocessing applies and refreshes data  
✅ Save creates batch_id  
✅ Labeling loads unlabeled records  
✅ Validation passes  
✅ Training starts and polls status  
✅ Progress bars update in real-time  
✅ Model comparison shows real metrics  
✅ Scorecard generates bin tables  
✅ CSV export downloads real file  

---

**🚀 You're ready to wire everything! Start with the proof of concept (ClinicalScorecardPage), then follow the 3-day plan!**

**All the code is in:**
- `frontend/src/services/api-complete.js` (API wrapper)
- `frontend/INTEGRATION_IMPLEMENTATION_STEPS.md` (Code examples)
- `frontend/COMPLETE_PIPELINE_INTEGRATION.md` (Pipeline flow)

**Good luck! 🎯**
