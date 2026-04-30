# End-to-End Quick Validation Test
## USM Autoimmune ML Platform - Critical Path Testing
**Date:** April 27, 2026  
**Duration:** 30-45 minutes  
**Purpose:** Validate all core features work end-to-end

---

## 🎯 Test Objective

Verify the **complete ML workflow** from login → data upload → quality check → training → prediction → explainability in one continuous flow.

---

## ✅ Pre-Test Checklist

```bash
# 1. Check all services running
docker ps | grep -E "postgres|minio|fastapi"

# 2. Check backend health
curl http://100.106.132.15:8001/health
# Expected: {"status":"healthy"...}

# 3. Get admin JWT token
curl -X POST "http://100.106.132.15:8001/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"s.nasrin","password":"testjwt"}' | jq -r '.access_token'

# Save token for later:
export TOKEN="<paste_token_here>"
```

**Verify:** All services healthy, token obtained ✅

---

## 🔐 STEP 1: Security Features (5 mins)

### 1.1 Test JWT Authentication
```bash
# Try accessing protected endpoint without token (should fail)
curl http://100.106.132.15:8001/api/v1/admin/stats

# Expected: {"detail":"Not authenticated"}
```
✅ Pass ❌ Fail

### 1.2 Test with JWT Token
```bash
# Access with token (should work)
curl -H "Authorization: Bearer $TOKEN" \
  http://100.106.132.15:8001/api/v1/admin/stats

# Expected: {"users":{"total":9,...},"patients":{"total":63,...}}
```
✅ Pass ❌ Fail

### 1.3 Test Rate Limiting
```bash
# Make 15 rapid requests to login (limit: 10/min)
for i in {1..15}; do 
  curl -s -o /dev/null -w "%{http_code}\n" \
    http://100.106.132.15:8001/api/v1/auth/login
done | sort | uniq -c

# Expected: Some 405 (wrong method) + some 429 (rate limited)
```
✅ Pass ❌ Fail

### 1.4 Test HTTPS
```bash
# Access via HTTPS
curl -k https://100.106.132.15/health

# Expected: Returns healthy status over TLS
```
✅ Pass ❌ Fail

**Security Tests Complete:** ____/4 passed

---

## 📊 STEP 2: Data Upload (5 mins)

### 2.1 Check Existing Patients
```bash
# Verify data exists
curl -H "Authorization: Bearer $TOKEN" \
  "http://100.106.132.15:8001/api/v1/patients?limit=5" | jq '.total'

# Expected: 63 (or your total patient count)
```
Total patients: ______  
✅ Pass ❌ Fail

### 2.2 View Patient Details
```bash
# Get first patient
curl -H "Authorization: Bearer $TOKEN" \
  "http://100.106.132.15:8001/api/v1/patients?limit=1" | jq '.patients[0]'

# Expected: Shows patient_id, name_anonymous, created_at, etc.
```
✅ Pass ❌ Fail

**Data Upload Tests Complete:** ____/2 passed

---

## 🔍 STEP 3: Data Quality (3 mins)

### 3.1 Check Data Quality Endpoint
```bash
# Get quality summary for structured_data_pivot table
curl -H "Authorization: Bearer $TOKEN" \
  "http://100.106.132.15:8001/api/v1/data-quality/summary?table_name=structured_data_pivot" \
  | jq '.completeness_score'

# Expected: Returns completeness score (e.g., 0.95 = 95%)
```
Completeness score: ______%  
✅ Pass ❌ Fail

### 3.2 Check for Missing Values
```bash
# Check missing value report
curl -H "Authorization: Bearer $TOKEN" \
  "http://100.106.132.15:8001/api/v1/data-quality/missing-values?table_name=structured_data_pivot" \
  | jq '.missing_columns | length'

# Expected: Returns number of columns with missing values
```
Columns with missing data: ______  
✅ Pass ❌ Fail

**Data Quality Tests Complete:** ____/2 passed

---

## 🤖 STEP 4: ML Training (10 mins)

### 4.1 Prepare Dataset with Feature Engineering
```bash
curl -X POST "http://100.106.132.15:8001/api/v1/ml/prepare-dataset" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_table": "structured_data_pivot",
    "target_column": "labels_disease_severity",
    "test_size": 0.35,
    "apply_feature_engineering": true,
    "batch_id": "e2e_test_batch"
  }' | jq '.job_id'

# Expected: Returns job_id like "dataset_prep_abc123..."
# SAVE THIS JOB ID!
```
Dataset Job ID: ______________________  
✅ Pass ❌ Fail

### 4.2 Check Dataset Preparation Status
```bash
# Replace <job_id> with actual job ID from 4.1
curl -H "Authorization: Bearer $TOKEN" \
  "http://100.106.132.15:8001/api/v1/ml/jobs/<job_id>/status" \
  | jq '.status'

# Expected: "completed" (may need to wait 10-30 seconds)
# If "running", wait and check again
```
Status: ______________________  
✅ Pass ❌ Fail

### 4.3 Train Base Model (XGBoost)
```bash
# Use dataset_job_id from 4.1
curl -X POST "http://100.106.132.15:8001/api/v1/ml/train/base-model" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "algorithm": "xgboost",
    "dataset_id": "<dataset_job_id>",
    "target_column": "labels_disease_severity",
    "hyperparameter_tuning": true,
    "batch_id": "e2e_test_batch"
  }' | jq '.job_id'

# Expected: Returns training_job_id like "xgboost_train_abc123..."
# ⏳ This takes 2-5 minutes - grab coffee!
```
Training Job ID: ______________________  
✅ Pass ❌ Fail

### 4.4 Monitor Training Progress
```bash
# Check every 30 seconds
curl -H "Authorization: Bearer $TOKEN" \
  "http://100.106.132.15:8001/api/v1/ml/jobs/<training_job_id>/status" \
  | jq '{status: .status, progress: .progress}'

# Expected: 
# - "running" (first few minutes)
# - "completed" (after 2-5 minutes)
```
Final status: ______________________  
Training accuracy: ______%  
✅ Pass ❌ Fail

### 4.5 View Training Results
```bash
# Get full job details
curl -H "Authorization: Bearer $TOKEN" \
  "http://100.106.132.15:8001/api/v1/ml/jobs/<training_job_id>" \
  | jq '{
    status: .status,
    algorithm: .algorithm,
    metrics: .result.test_metrics,
    model_path: .result.model_path
  }'

# Expected: Shows accuracy, precision, recall, F1, model saved to MinIO
```
Test Accuracy: ______%  
Model saved: ✅ Yes ❌ No  
✅ Pass ❌ Fail

**ML Training Tests Complete:** ____/5 passed

---

## 🎯 STEP 5: Predictions (5 mins)

### 5.1 Make Single Prediction
```bash
# Use the trained model from 4.5
curl -X POST "http://100.106.132.15:8001/api/v1/ml/predict" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model_version": "<training_job_id>",
    "patient_data": {
      "lab_results_CRP": 1.5,
      "lab_results_ESR": 45,
      "lab_results_C3": 85,
      "lab_results_C4": 12,
      "lab_results_PLT": 230,
      "lab_results_WBC": 4.5,
      "lab_results_HGB": 12.0
    }
  }' | jq '{prediction: .prediction, confidence: .confidence}'

# Expected: Returns prediction class and confidence score
```
Prediction: ______________________  
Confidence: ______%  
✅ Pass ❌ Fail

### 5.2 Check Prediction History
```bash
# View recent predictions
curl -H "Authorization: Bearer $TOKEN" \
  "http://100.106.132.15:8001/api/v1/ml/predictions/history?limit=1" \
  | jq '.predictions[0]'

# Expected: Shows the prediction we just made (5.1)
```
✅ Pass ❌ Fail

**Prediction Tests Complete:** ____/2 passed

---

## 🧠 STEP 6: Explainability (SHAP + Gemma) (5 mins)

### 6.1 Generate SHAP Explanation
```bash
# Generate SHAP for the prediction from 5.1
curl -X POST "http://100.106.132.15:8001/api/v1/explainability/shap" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model_version": "<training_job_id>",
    "patient_data": {
      "lab_results_CRP": 1.5,
      "lab_results_ESR": 45,
      "lab_results_C3": 85,
      "lab_results_C4": 12,
      "lab_results_PLT": 230,
      "lab_results_WBC": 4.5,
      "lab_results_HGB": 12.0
    }
  }' | jq '{
    base_value: .base_value,
    prediction: .prediction_value,
    top_features: .feature_contributions[:3]
  }'

# Expected: Shows SHAP values, top contributing features
```
Base value: ______  
Top feature: ______________________  
✅ Pass ❌ Fail

### 6.2 Generate Gemma AI Explanation
```bash
# Get natural language explanation
curl -X POST "http://100.106.132.15:8001/api/v1/explainability/gemma-explain" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "shap_values": {
      "lab_results_CRP": 0.18,
      "lab_results_ESR": 0.12,
      "cytopenia": 0.08
    },
    "prediction": "moderate_risk",
    "confidence": 0.75
  }' | jq -r '.explanation' | head -n 10

# Expected: Natural language clinical explanation
# ⏳ Takes 5-10 seconds (Gemma AI generating text)
```
Explanation generated: ✅ Yes ❌ No  
✅ Pass ❌ Fail

**Explainability Tests Complete:** ____/2 passed

---

## 📈 STEP 7: Admin Features (3 mins)

### 7.1 View Platform Stats
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://100.106.132.15:8001/api/v1/admin/stats | jq '.'

# Expected: Shows user count, patient count, training jobs, etc.
```
Total users: ______  
Total patients: ______  
✅ Pass ❌ Fail

### 7.2 View Training Job History
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://100.106.132.15:8001/api/v1/ml/jobs?limit=5" \
  | jq '.jobs | length'

# Expected: Shows recent training jobs (at least 1 from this test)
```
Jobs found: ______  
✅ Pass ❌ Fail

### 7.3 Check Audit Logs
```bash
# Check if audit logging is working
docker exec -e PGPASSWORD=Mtai2026! usm-autoimmune-postgres \
  psql -U usm_db_admin -d usm_autoimmune_registry \
  -c "SELECT COUNT(*) FROM audit_logs WHERE username='s.nasrin' AND timestamp > NOW() - INTERVAL '10 minutes';"

# Expected: Shows count > 0 (all our API calls logged)
```
Audit log entries: ______  
✅ Pass ❌ Fail

**Admin Tests Complete:** ____/3 passed

---

## 🎨 STEP 8: UI Testing (5 mins)

### 8.1 Login to Frontend
1. Open browser: `http://100.106.132.15:5173`
2. Login: `s.nasrin` / `testjwt`
3. Verify: Dashboard loads, shows user badge "Admin"

✅ Pass ❌ Fail

### 8.2 Navigate All Pages
Check each page loads without errors:
- [ ] Dashboard (shows stats cards)
- [ ] Data Catalog (shows 63 patients)
- [ ] Data Quality (shows quality metrics)
- [ ] Training Jobs (shows our XGBoost job)
- [ ] Predictions (shows prediction history)
- [ ] Explainability (shows SHAP/Gemma tabs)
- [ ] Model Comparison (shows model rankings)
- [ ] Admin Panel (admin only)

Pages working: ____/8  
✅ Pass ❌ Fail

### 8.3 Test Prediction UI
1. Go to Predictions page
2. Select model: XGBoost (from Step 4)
3. Enter patient data (same as Step 5.1)
4. Click "Make Prediction"
5. Verify: Shows prediction result + confidence

✅ Pass ❌ Fail

**UI Tests Complete:** ____/3 passed

---

## 📊 TEST SUMMARY

| Category | Tests Passed | Total Tests | Pass Rate |
|----------|-------------|------------|-----------|
| **Security** | ____/4 | 4 | ____% |
| **Data Upload** | ____/2 | 2 | ____% |
| **Data Quality** | ____/2 | 2 | ____% |
| **ML Training** | ____/5 | 5 | ____% |
| **Predictions** | ____/2 | 2 | ____% |
| **Explainability** | ____/2 | 2 | ____% |
| **Admin** | ____/3 | 3 | ____% |
| **UI** | ____/3 | 3 | ____% |
| **TOTAL** | ____/23 | 23 | ____% |

---

## ✅ CRITICAL PATH VALIDATION

**End-to-End Flow Verified:**
- [ ] Login with JWT authentication
- [ ] Data exists and is accessible
- [ ] Data quality checks working
- [ ] Feature engineering applied correctly
- [ ] Model training completes successfully
- [ ] Predictions generated with confidence scores
- [ ] SHAP explanations show feature importance
- [ ] Gemma AI generates clinical explanations
- [ ] Audit logs capture all actions
- [ ] UI displays all features correctly
- [ ] HTTPS/TLS encryption active
- [ ] Rate limiting prevents abuse

**Overall Status:**  
✅ **PLATFORM READY FOR PRODUCTION**  
⚠️ **MINOR ISSUES FOUND** (document below)  
❌ **CRITICAL ISSUES FOUND** (document below)

---

## 🐛 ISSUES FOUND

### Critical Issues
*None expected - document if found*

| Issue # | Description | Steps to Reproduce | Severity |
|---------|-------------|-------------------|----------|
|         |             |                   |          |

### Minor Issues
*Document any non-blocking issues*

| Issue # | Description | Workaround | Priority |
|---------|-------------|-----------|----------|
|         |             |           |          |

---

## 📝 NOTES & OBSERVATIONS

**Performance:**
- Dataset preparation time: ______ seconds
- Model training time: ______ minutes
- Prediction latency: ______ ms
- SHAP generation time: ______ seconds
- Gemma explanation time: ______ seconds

**Observations:**
- 
- 
- 

---

## ✍️ SIGN-OFF

**Tester Name:** ______________________  
**Date:** April 27, 2026  
**Time:** ______________________  
**Duration:** ______ minutes  

**Overall Assessment:**  
☐ **PASS** - All critical features working, platform production-ready  
☐ **PASS WITH MINOR ISSUES** - Core features work, minor improvements needed  
☐ **FAIL** - Critical issues found, requires fixes before deployment

**Comments:**
_________________________________________________________________________
_________________________________________________________________________
_________________________________________________________________________

---

**Next Steps:**
1. ✅ If PASS: Deploy to production, prepare TSD presentation
2. ⚠️ If PASS WITH ISSUES: Document issues, create fix tickets
3. ❌ If FAIL: Debug issues, retest after fixes
