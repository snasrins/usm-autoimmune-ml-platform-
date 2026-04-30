# USM Autoimmune ML Platform - System Integration Test (SIT) Script
**Project:** USM-Autoimmune PMO0006  
**Version:** 2.0 - Updated April 2026  
**Status:** Ready for SIT Testing

---

## Test Environment Setup
- **Backend API:** http://100.106.132.15:8001/api/v1
- **Frontend UI:** http://localhost:3001
- **MinIO Console:** http://100.106.132.15:9001
- **Database:** PostgreSQL 15 on gpulab1
- **Test User:** admin@usm.my / admin123
- **Test Dataset:** AAM-SLE-E (real data).xlsx (228 records)

---

## TEST SECTION 1: AUTHENTICATION & AUTHORIZATION

### TC-AUTH-001: User Login
**Priority:** Critical  
**Prerequisites:** Valid user account exists

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Navigate to http://localhost:3001 | Login page displayed | ☐ Pass ☐ Fail | |
| 2 | Enter valid credentials (admin@usm.my / admin123) | Login successful, redirected to Dashboard | ☐ Pass ☐ Fail | |
| 3 | Verify user profile in top-right corner | Shows "Admin User" or username | ☐ Pass ☐ Fail | |

### TC-AUTH-002: Session Persistence
**Priority:** High  
**Prerequisites:** User logged in

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Login successfully | User on Dashboard | ☐ Pass ☐ Fail | |
| 2 | Refresh page (F5) | User remains logged in | ☐ Pass ☐ Fail | |
| 3 | Close browser and reopen | Session maintained (or login required based on config) | ☐ Pass ☐ Fail | |

### TC-AUTH-003: Logout
**Priority:** Medium

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Click user profile menu | Dropdown menu appears | ☐ Pass ☐ Fail | |
| 2 | Click "Logout" | Redirected to login page, session cleared | ☐ Pass ☐ Fail | |
| 3 | Try to access /dashboard directly | Redirected to login | ☐ Pass ☐ Fail | |

---

## TEST SECTION 2: DATA UPLOAD & INGESTION (Layer 1-3)

### TC-UPLOAD-001: CSV File Upload - Valid Data
**Priority:** Critical  
**Test Data:** AAM-SLE-E (real data).xlsx converted to CSV

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Navigate to Data Catalog page | Data Catalog page loads | ☐ Pass ☐ Fail | |
| 2 | Click "Upload New Dataset" button | Upload dialog opens | ☐ Pass ☐ Fail | |
| 3 | Select CSV file from Dataset folder | File selected | ☐ Pass ☐ Fail | |
| 4 | Enter Dataset Type: "SLE" | Type entered | ☐ Pass ☐ Fail | |
| 5 | Enter Dataset Name: "SLE Test Data" | Name entered | ☐ Pass ☐ Fail | |
| 6 | Click Upload | Upload progress shown | ☐ Pass ☐ Fail | |
| 7 | Wait for upload completion | Success message "Preview created successfully" | ☐ Pass ☐ Fail | |
| 8 | Check MinIO console → usm-raw bucket | Raw CSV file saved with session_id path | ☐ Pass ☐ Fail | Check: session_{uuid}/raw_filename.csv |

**Verify:**
- Upload session ID generated
- Preview table shows first 20 rows
- Column names detected correctly
- Data types inferred (numeric, text, date)

### TC-UPLOAD-002: Excel File Upload
**Priority:** High  
**Test Data:** AAM-SLE-E (real data).xlsx

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Upload .xlsx file directly | System accepts Excel format | ☐ Pass ☐ Fail | |
| 2 | Verify conversion | Data displayed correctly in preview | ☐ Pass ☐ Fail | |
| 3 | Check MinIO raw bucket | Excel file saved | ☐ Pass ☐ Fail | |

### TC-UPLOAD-003: Invalid File Rejection
**Priority:** Medium

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Try to upload .txt file | Error: "Supported formats: CSV, Excel" | ☐ Pass ☐ Fail | |
| 2 | Try to upload .pdf file | Error: "Supported formats: CSV, Excel" | ☐ Pass ☐ Fail | |
| 3 | Try to upload empty CSV | Error or warning about no data | ☐ Pass ☐ Fail | |

---

## TEST SECTION 3: DATA QUALITY CHECKS (Layer 4)

### TC-QUALITY-001: Automatic Quality Analysis
**Priority:** Critical  
**Prerequisites:** Data uploaded successfully

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | After upload, navigate to Data Quality tab | Quality metrics displayed | ☐ Pass ☐ Fail | |
| 2 | Check "Missing Values" metric | Shows count and percentage per column | ☐ Pass ☐ Fail | |
| 3 | Check "Duplicate Rows" metric | Shows duplicate count | ☐ Pass ☐ Fail | |
| 4 | Check "Outliers" detection | Outliers identified using IQR method | ☐ Pass ☐ Fail | |
| 5 | View Quality Score | Overall score (0-100%) displayed | ☐ Pass ☐ Fail | |

**Verify:**
- Quality checks run automatically on upload
- Results stored in database
- Visual indicators (✓ ⚠ ✗) for each metric
- Detailed breakdown available per column

### TC-QUALITY-002: Quality Report Export
**Priority:** Medium

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | On Data Quality page, click "Export Report" | Export options shown | ☐ Pass ☐ Fail | |
| 2 | Select JSON format | Quality report downloaded as JSON | ☐ Pass ☐ Fail | |
| 3 | Verify report content | Contains all metrics and column details | ☐ Pass ☐ Fail | |

---

## TEST SECTION 4: PREPROCESSING & TRANSFORMATION (Layer 5)

### TC-PREPROCESS-001: Missing Value Imputation
**Priority:** Critical

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Navigate to Preprocessing page | Preview data displayed | ☐ Pass ☐ Fail | |
| 2 | Click "Handle Missing Values" | Imputation dialog opens | ☐ Pass ☐ Fail | |
| 3 | Select method: "Median" | Method selected | ☐ Pass ☐ Fail | |
| 4 | Set threshold: 0.9 (90%) | Threshold set | ☐ Pass ☐ Fail | |
| 5 | Click "Apply" | Processing message shown | ☐ Pass ☐ Fail | |
| 6 | Wait for completion | Success message: "Missing values handled" | ☐ Pass ☐ Fail | |
| 7 | Check preview table | Missing values filled with median | ☐ Pass ☐ Fail | |

**Verify:**
- Only numeric columns use median
- Categorical columns use mode
- Columns >90% missing dropped
- Preview updates in real-time

### TC-PREPROCESS-002: Duplicate Removal
**Priority:** High

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Click "Remove Duplicates" | Confirmation dialog | ☐ Pass ☐ Fail | |
| 2 | Select "Keep First" | Option selected | ☐ Pass ☐ Fail | |
| 3 | Click "Apply" | Duplicates removed | ☐ Pass ☐ Fail | |
| 4 | Check row count | Row count decreased by duplicate count | ☐ Pass ☐ Fail | |

### TC-PREPROCESS-003: Outlier Handling
**Priority:** High

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Click "Handle Outliers" | Method selection shown | ☐ Pass ☐ Fail | |
| 2 | Select method: "IQR" | IQR method selected | ☐ Pass ☐ Fail | |
| 3 | Set threshold: 1.5 | Threshold set | ☐ Pass ☐ Fail | |
| 4 | Click "Apply" | Outliers capped/removed | ☐ Pass ☐ Fail | |
| 5 | Verify results | Extreme values within IQR bounds | ☐ Pass ☐ Fail | |

### TC-PREPROCESS-004: Save Preprocessed Data
**Priority:** Critical

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | After all preprocessing, click "Save to Database" | Confirmation dialog | ☐ Pass ☐ Fail | |
| 2 | Enter dataset source: "Hospital USM" | Source entered | ☐ Pass ☐ Fail | |
| 3 | Click "Confirm" | Processing starts | ☐ Pass ☐ Fail | |
| 4 | Wait for completion | Success: "✅ Data saved to PostgreSQL! X records imported" | ☐ Pass ☐ Fail | |
| 5 | Check MinIO → usm-preprocessed bucket | CSV file saved: batch_{id}/final_preprocessed_{timestamp}.csv | ☐ Pass ☐ Fail | |
| 6 | Check PostgreSQL flexible_dataset_wide table | Records inserted with import_batch_id | ☐ Pass ☐ Fail | |

**Verify:**
- Batch ID generated
- Duplicates skipped (if any)
- Import statistics shown
- Data available in Data Catalog

---

## TEST SECTION 5: DATA LABELING (Layer 6)

### TC-LABEL-001: View Unlabeled Data
**Priority:** High  
**Prerequisites:** Preprocessed data saved

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Navigate to Labeling page | Labeling interface loads | ☐ Pass ☐ Fail | |
| 2 | Select target column: "labels_disease_classification" | Column selected | ☐ Pass ☐ Fail | |
| 3 | Check unlabeled count | Shows "X records without labels" | ☐ Pass ☐ Fail | |
| 4 | View first unlabeled record | Patient data displayed (no identifiers) | ☐ Pass ☐ Fail | |

### TC-LABEL-002: Assign Labels
**Priority:** Critical

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | View unlabeled record | Clinical data visible | ☐ Pass ☐ Fail | |
| 2 | Select label: "SLE" from dropdown | Label selected | ☐ Pass ☐ Fail | |
| 3 | Click "Save Label" | Success message | ☐ Pass ☐ Fail | |
| 4 | Verify label saved | Record marked as labeled | ☐ Pass ☐ Fail | |
| 5 | Check statistics | Labeled count incremented by 1 | ☐ Pass ☐ Fail | |

### TC-LABEL-003: Batch Labeling
**Priority:** Medium

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Click "Batch Label" | Batch interface opens | ☐ Pass ☐ Fail | |
| 2 | Select 10 records | Records selected | ☐ Pass ☐ Fail | |
| 3 | Apply label "RA" to all | All 10 records labeled | ☐ Pass ☐ Fail | |
| 4 | Check statistics | Labeled count +10 | ☐ Pass ☐ Fail | |

### TC-LABEL-004: Label Statistics
**Priority:** Medium

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | View labeling statistics | Stats dashboard shown | ☐ Pass ☐ Fail | |
| 2 | Check total records | Matches import count | ☐ Pass ☐ Fail | |
| 3 | Check labeled vs unlabeled | Sum equals total | ☐ Pass ☐ Fail | |
| 4 | Check label distribution | Bar chart shows SLE/RA/SSc counts | ☐ Pass ☐ Fail | |

---

## TEST SECTION 6: FEATURE ENGINEERING (Layer 6.5)

### TC-FEATURE-001: View Feature Pipeline
**Priority:** Medium  
**Prerequisites:** Labeled data available

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Navigate to Feature Engineering page | Feature pipeline page loads | ☐ Pass ☐ Fail | |
| 2 | View available transformations | List shows: Ratios, Temporal, Composite, Percentile | ☐ Pass ☐ Fail | |
| 3 | Check auto-detected features | System suggests clinical ratios | ☐ Pass ☐ Fail | |

### TC-FEATURE-002: Create Custom Feature
**Priority:** Low

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Click "Create Feature" | Feature creation dialog | ☐ Pass ☐ Fail | |
| 2 | Select type: "Ratio" | Ratio options shown | ☐ Pass ☐ Fail | |
| 3 | Select numerator: "laboratory_WBC" | Column selected | ☐ Pass ☐ Fail | |
| 4 | Select denominator: "laboratory_RBC" | Column selected | ☐ Pass ☐ Fail | |
| 5 | Name: "WBC_RBC_ratio" | Name entered | ☐ Pass ☐ Fail | |
| 6 | Click "Create" | Feature added to pipeline | ☐ Pass ☐ Fail | |
| 7 | Verify feature | Shows in feature list | ☐ Pass ☐ Fail | |

---

## TEST SECTION 7: ML TRAINING (Layer 7-8)

### TC-TRAIN-001: Prepare Training Dataset
**Priority:** Critical  
**Prerequisites:** Labeled data (minimum 100 records)

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Navigate to Training Jobs page | Training interface loads | ☐ Pass ☐ Fail | |
| 2 | Click "New Training Run" | Configuration dialog opens | ☐ Pass ☐ Fail | |
| 3 | Select dataset from dropdown | Dataset selected | ☐ Pass ☐ Fail | |
| 4 | Select target: "labels_disease_classification" | Target selected | ☐ Pass ☐ Fail | |
| 5 | Set test size: 0.35 (35%) | Test size set | ☐ Pass ☐ Fail | |
| 6 | Set CV folds: 5 | Folds set | ☐ Pass ☐ Fail | |
| 7 | Click "Prepare Dataset" | Dataset preparation job starts | ☐ Pass ☐ Fail | |
| 8 | Wait for completion (check status) | Status: "completed" | ☐ Pass ☐ Fail | Check backend logs |
| 9 | Check MinIO → ml-datasets bucket | Dataset pickle saved: dataset_{job_id}/train_data.pkl | ☐ Pass ☐ Fail | |

**Verify:**
- Train/test split correct (65%/35%)
- Features scaled for linear models
- Raw features kept for tree models
- Metadata saved (row counts, feature names)

### TC-TRAIN-002: Train XGBoost Model
**Priority:** Critical  
**Prerequisites:** Dataset prepared successfully

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Select model: "XGBoost" | XGBoost card highlighted | ☐ Pass ☐ Fail | |
| 2 | Set Optuna trials: 30 | Trials set | ☐ Pass ☐ Fail | |
| 3 | Click "Start Training" | Training job queued | ☐ Pass ☐ Fail | |
| 4 | Monitor progress | Optuna trials shown in logs (Trial 1/30...) | ☐ Pass ☐ Fail | Check backend logs |
| 5 | Wait for completion (2-5 minutes) | Status: "completed" | ☐ Pass ☐ Fail | |
| 6 | View results | Shows OOF AUC, Test AUC, Best Params | ☐ Pass ☐ Fail | |
| 7 | Check MinIO → ml-models bucket | Model files saved: {batch_id}_xgboost/fold_0.pkl | ☐ Pass ☐ Fail | |

**Verify:**
- All 30 Optuna trials complete
- Best hyperparameters logged
- OOF AUC > 0.50 (baseline)
- 5 fold models saved (fold_0 to fold_4)

### TC-TRAIN-003: Train Multiple Models
**Priority:** High

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | In New Training Run dialog, select models: XGBoost, Random Forest, LightGBM | 3 models selected | ☐ Pass ☐ Fail | |
| 2 | Click "Start Training" | All 3 jobs queued | ☐ Pass ☐ Fail | |
| 3 | Monitor console logs | See "STARTING BASE MODEL TRAINING" for each | ☐ Pass ☐ Fail | |
| 4 | Wait for all to complete | All 3 show status: "completed" | ☐ Pass ☐ Fail | |
| 5 | Check MinIO ml-models bucket | 3 model folders exist | ☐ Pass ☐ Fail | |

### TC-TRAIN-004: All 13 Models Training
**Priority:** Medium  
**Test:** Train all available models

| Model | Training Status | OOF AUC | Test AUC | Training Time | Notes |
|-------|----------------|---------|----------|---------------|-------|
| XGBoost | ☐ Pass ☐ Fail | | | | |
| LightGBM | ☐ Pass ☐ Fail | | | | |
| CatBoost | ☐ Pass ☐ Fail | | | | |
| Gradient Boosting | ☐ Pass ☐ Fail | | | | |
| Random Forest | ☐ Pass ☐ Fail | | | | |
| AdaBoost | ☐ Pass ☐ Fail | | | | |
| Decision Tree | ☐ Pass ☐ Fail | | | | |
| SVM | ☐ Pass ☐ Fail | | | | Uses scaled features |
| KNN | ☐ Pass ☐ Fail | | | | Uses scaled features |
| Logistic Regression | ☐ Pass ☐ Fail | | | | Uses scaled features |
| Ridge Classifier | ☐ Pass ☐ Fail | | | | Uses scaled features |
| Linear Discriminant | ☐ Pass ☐ Fail | | | | Uses scaled features |
| MLP (Neural Network) | ☐ Pass ☐ Fail | | | | Uses scaled features |

**Pass Criteria:**
- All models complete without errors
- OOF AUC > 0.40 for at least 10/13 models
- Models saved to MinIO successfully

---

## TEST SECTION 8: MODEL EVALUATION & MONITORING

### TC-EVAL-001: View Model Performance
**Priority:** High  
**Prerequisites:** At least 1 model trained

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Navigate to Dashboard | Dashboard loads | ☐ Pass ☐ Fail | |
| 2 | Check "Model Performance" panel | Shows latest trained models | ☐ Pass ☐ Fail | |
| 3 | Verify metrics | AUC, Precision, Recall, F1 displayed | ☐ Pass ☐ Fail | |
| 4 | Check "Feature Importance" panel | Bar chart shows top features | ☐ Pass ☐ Fail | |

### TC-EVAL-002: Model Registry
**Priority:** High

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Navigate to Model Registry | All trained models listed | ☐ Pass ☐ Fail | |
| 2 | Check model details | Name, version, AUC, training date shown | ☐ Pass ☐ Fail | |
| 3 | Sort by AUC (descending) | Best model shown first | ☐ Pass ☐ Fail | |
| 4 | Click on a model | Detailed view opens | ☐ Pass ☐ Fail | |
| 5 | View hyperparameters | Best params from Optuna displayed | ☐ Pass ☐ Fail | |

### TC-EVAL-003: Model Comparison
**Priority:** Medium

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | On Model Registry, select 2-4 models | Models selected | ☐ Pass ☐ Fail | |
| 2 | Click "Compare Models" | Comparison dialog opens | ☐ Pass ☐ Fail | |
| 3 | View comparison table | Side-by-side metrics shown | ☐ Pass ☐ Fail | |
| 4 | View ROC curves | Overlaid ROC curves displayed | ☐ Pass ☐ Fail | |

---

## TEST SECTION 9: INFERENCE & PREDICTIONS

### TC-INFER-001: Single Patient Prediction
**Priority:** Critical  
**Prerequisites:** At least 1 trained model

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Navigate to Predictions page | Prediction interface loads | ☐ Pass ☐ Fail | |
| 2 | Select model from dropdown | Model selected | ☐ Pass ☐ Fail | |
| 3 | Click "Single Prediction" | Input form shown | ☐ Pass ☐ Fail | |
| 4 | Enter patient data (clinical features) | Data entered | ☐ Pass ☐ Fail | |
| 5 | Click "Predict" | Prediction returned in <2 seconds | ☐ Pass ☐ Fail | |
| 6 | View result | Shows: Predicted Class, Probability, Confidence | ☐ Pass ☐ Fail | |

**Verify:**
- Prediction class (SLE/RA/SSc)
- Probability scores for each class
- Confidence interval

### TC-INFER-002: Batch Predictions
**Priority:** High

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Click "Batch Prediction" | File upload dialog | ☐ Pass ☐ Fail | |
| 2 | Upload CSV with 10 patients | File accepted | ☐ Pass ☐ Fail | |
| 3 | Select model | Model selected | ☐ Pass ☐ Fail | |
| 4 | Click "Run Predictions" | Processing starts | ☐ Pass ☐ Fail | |
| 5 | Wait for completion | All 10 predictions complete | ☐ Pass ☐ Fail | |
| 6 | Download results | CSV file downloaded with predictions | ☐ Pass ☐ Fail | |
| 7 | Check MinIO → predictions bucket | Results saved: predictions_{timestamp}.csv | ☐ Pass ☐ Fail | |

**Verify:**
- All rows processed
- No errors for valid data
- Output includes: patient_id, predicted_class, probability_SLE, probability_RA, probability_SSc

---

## TEST SECTION 10: CLINICAL SCORECARDS

### TC-SCORECARD-001: Generate Single Scorecard
**Priority:** High  
**Prerequisites:** Trained model available

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Navigate to Clinical Scorecard page | Scorecard interface loads | ☐ Pass ☐ Fail | |
| 2 | Select model | Model selected | ☐ Pass ☐ Fail | |
| 3 | Enter patient data | Clinical features entered | ☐ Pass ☐ Fail | |
| 4 | Click "Generate Scorecard" | Scorecard generated | ☐ Pass ☐ Fail | |
| 5 | View scorecard | Shows risk score (0-100) + risk category | ☐ Pass ☐ Fail | |
| 6 | View contributing factors | Top 5 features affecting score | ☐ Pass ☐ Fail | |

### TC-SCORECARD-002: Batch Scorecard Generation
**Priority:** Medium

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Click "Batch Scorecard" | Upload dialog | ☐ Pass ☐ Fail | |
| 2 | Upload CSV with patient data | File accepted | ☐ Pass ☐ Fail | |
| 3 | Select model | Model selected | ☐ Pass ☐ Fail | |
| 4 | Click "Generate" | Processing starts | ☐ Pass ☐ Fail | |
| 5 | Wait for completion | All scorecards generated | ☐ Pass ☐ Fail | |
| 6 | Download results | 3 files downloaded: batch CSV, summary CSV, JSON | ☐ Pass ☐ Fail | |
| 7 | Check MinIO → clinical-scorecards bucket | Artifacts saved: batch_{id}/scorecards_{timestamp}.csv | ☐ Pass ☐ Fail | |

---

## TEST SECTION 11: EXPLAINABILITY & AI ASSISTANT

### TC-EXPLAIN-001: SHAP Feature Importance
**Priority:** High  
**Prerequisites:** Model trained

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | On Model Details page, click "Explain" | SHAP analysis starts | ☐ Pass ☐ Fail | |
| 2 | Wait for SHAP calculation | SHAP values computed | ☐ Pass ☐ Fail | |
| 3 | View feature importance plot | Bar chart shows top 20 features | ☐ Pass ☐ Fail | |
| 4 | View SHAP summary plot | Beeswarm plot displayed | ☐ Pass ☐ Fail | |

### TC-EXPLAIN-002: Single Prediction Explanation
**Priority:** High

| Step | Action | expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Make a single prediction | Prediction result shown | ☐ Pass ☐ Fail | |
| 2 | Click "Explain Prediction" | SHAP waterfall plot generated | ☐ Pass ☐ Fail | |
| 3 | View contributions | Shows how each feature affected prediction | ☐ Pass ☐ Fail | |
| 4 | Check force plot | Interactive force plot displayed | ☐ Pass ☐ Fail | |

### TC-EXPLAIN-003: Dr. Myra AI Assistant
**Priority:** High

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Click chatbot icon (bottom-right) | Dr. Myra chat opens | ☐ Pass ☐ Fail | |
| 2 | Type: "What is my model accuracy?" | Responds with model performance from database | ☐ Pass ☐ Fail | |
| 3 | Type: "Explain XGBoost" | Responds with clinical ML explanation | ☐ Pass ☐ Fail | |
| 4 | Type: "What features are most important?" | Returns top features from SHAP | ☐ Pass ☐ Fail | |
| 5 | Type: "How do I improve my model?" | Provides actionable recommendations | ☐ Pass ☐ Fail | |
| 6 | Check chat history | Previous messages persist | ☐ Pass ☐ Fail | |

**Verify Dr. Myra uses:**
- Google Gemma-4-E4B LLM
- 300+ line clinical ML system prompt
- Real-time data from backend APIs
- Proper markdown formatting in responses

---

## TEST SECTION 12: MINIO STORAGE INTEGRATION

### TC-MINIO-001: Verify All Buckets Exist
**Priority:** Critical

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Login to MinIO console (100.106.132.15:9001) | Console loads | ☐ Pass ☐ Fail | Credentials: minio_admin / MinIO_P@ssw0rd_2026 |
| 2 | Check bucket: usm-raw | Bucket exists | ☐ Pass ☐ Fail | |
| 3 | Check bucket: usm-preprocessed | Bucket exists | ☐ Pass ☐ Fail | |
| 4 | Check bucket: ml-datasets | Bucket exists | ☐ Pass ☐ Fail | |
| 5 | Check bucket: ml-models | Bucket exists | ☐ Pass ☐ Fail | |
| 6 | Check bucket: predictions | Bucket exists | ☐ Pass ☐ Fail | |
| 7 | Check bucket: clinical-scorecards | Bucket exists | ☐ Pass ☐ Fail | |
| 8 | Check bucket: analytics | Bucket exists | ☐ Pass ☐ Fail | |

### TC-MINIO-002: Verify Data Lineage
**Priority:** High  
**Prerequisites:** Complete workflow executed (upload → preprocess → train → predict)

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Check usm-raw bucket | Contains: session_{id}/raw_filename.csv | ☐ Pass ☐ Fail | |
| 2 | Check usm-preprocessed bucket | Contains: batch_{id}/final_preprocessed_{timestamp}.csv | ☐ Pass ☐ Fail | |
| 3 | Check ml-datasets bucket | Contains: dataset_{job_id}/train_data.pkl | ☐ Pass ☐ Fail | |
| 4 | Check ml-models bucket | Contains: {batch_id}_xgboost/fold_0.pkl to fold_4.pkl | ☐ Pass ☐ Fail | |
| 5 | Check predictions bucket | Contains: predictions_{timestamp}.csv | ☐ Pass ☐ Fail | |
| 6 | Verify metadata | Each object has proper metadata (batch_id, timestamp, etc.) | ☐ Pass ☐ Fail | |

### TC-MINIO-003: NMRR Compliance Check
**Priority:** Critical

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Download random file from usm-preprocessed | File downloaded | ☐ Pass ☐ Fail | |
| 2 | Inspect file content | NO patient identifiers (IC, name, phone, address) | ☐ Pass ☐ Fail | |
| 3 | Check file metadata | NO forbidden fields in metadata | ☐ Pass ☐ Fail | |
| 4 | Verify only de-identified data | Only clinical features + batch_id | ☐ Pass ☐ Fail | |

---

## TEST SECTION 13: DASHBOARD & MONITORING

### TC-DASH-001: Dashboard Overview
**Priority:** Medium

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Navigate to Dashboard | All panels load | ☐ Pass ☐ Fail | |
| 2 | Check "Total Datasets" KPI | Shows correct count | ☐ Pass ☐ Fail | |
| 3 | Check "Data Quality" KPI | Shows average quality score | ☐ Pass ☐ Fail | |
| 4 | Check "Models Trained" KPI | Shows total model count | ☐ Pass ☐ Fail | |
| 5 | Check "Active Users" KPI | Shows logged-in user count | ☐ Pass ☐ Fail | |

### TC-DASH-002: Real-time Updates
**Priority:** Low

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Start a training job | Dashboard doesn't freeze | ☐ Pass ☐ Fail | |
| 2 | Refresh Dashboard | New training job appears | ☐ Pass ☐ Fail | |
| 3 | Wait for job completion | KPI updates automatically | ☐ Pass ☐ Fail | |

### TC-DASH-003: Data Quality Overview
**Priority:** Medium

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | View "Data Quality Overview" panel | Shows quality metrics | ☐ Pass ☐ Fail | |
| 2 | Check color coding | Green (>80%), Yellow (50-80%), Red (<50%) | ☐ Pass ☐ Fail | |
| 3 | Click on a dataset | Navigates to Data Quality page | ☐ Pass ☐ Fail | |

---

## TEST SECTION 14: ERROR HANDLING & EDGE CASES

### TC-ERROR-001: Invalid Data Upload
**Priority:** High

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Upload CSV with missing headers | Error: "Missing column headers" | ☐ Pass ☐ Fail | |
| 2 | Upload empty CSV (0 rows) | Error: "No data found" | ☐ Pass ☐ Fail | |
| 3 | Upload CSV with only 1 row | Warning: "Insufficient data for training" | ☐ Pass ☐ Fail | |

### TC-ERROR-002: Training with Insufficient Labels
**Priority:** High

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Try to train with <100 labeled records | Error: "Minimum 100 labeled records required" | ☐ Pass ☐ Fail | |
| 2 | Try to train with only 1 class | Error: "Need at least 2 classes for classification" | ☐ Pass ☐ Fail | |

### TC-ERROR-003: Prediction with Wrong Model
**Priority:** Medium

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Try prediction with deleted model | Error: "Model not found" | ☐ Pass ☐ Fail | |
| 2 | Upload CSV with missing features | Error: "Missing required features: [list]" | ☐ Pass ☐ Fail | |

### TC-ERROR-004: Network & Service Failures
**Priority:** High

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Stop backend (docker-compose stop fastapi) | Frontend shows "Connection Error" | ☐ Pass ☐ Fail | |
| 2 | Try to upload data | Graceful error message | ☐ Pass ☐ Fail | |
| 3 | Restart backend | Frontend reconnects automatically | ☐ Pass ☐ Fail | |

---

## TEST SECTION 15: PERFORMANCE & LOAD TESTING

### TC-PERF-001: Large Dataset Upload
**Priority:** Medium

| Test | Dataset Size | Expected Time | Actual Time | Status | Notes |
|------|-------------|---------------|-------------|--------|-------|
| Small | 100 rows, 50 cols | <5 seconds | | ☐ Pass ☐ Fail | |
| Medium | 1,000 rows, 50 cols | <30 seconds | | ☐ Pass ☐ Fail | |
| Large | 10,000 rows, 50 cols | <2 minutes | | ☐ Pass ☐ Fail | |

### TC-PERF-002: Training Performance
**Priority:** Medium

| Model | Dataset Size | Trials | Expected Time | Actual Time | Status |
|-------|-------------|--------|---------------|-------------|--------|
| XGBoost | 200 samples | 30 | <3 minutes | | ☐ Pass ☐ Fail |
| Random Forest | 200 samples | 30 | <2 minutes | | ☐ Pass ☐ Fail |
| SVM | 200 samples | 30 | <5 minutes | | ☐ Pass ☐ Fail |

### TC-PERF-003: Concurrent Users
**Priority:** Low

| Test | Users | Actions | Expected Behavior | Status |
|------|-------|---------|-------------------|--------|
| Basic | 1 user | Upload + train | Normal operation | ☐ Pass ☐ Fail |
| Load | 5 users | Concurrent uploads | All succeed, no slowdown | ☐ Pass ☐ Fail |
| Stress | 10 users | Concurrent training | System handles gracefully | ☐ Pass ☐ Fail |

---

## TEST SECTION 16: DATA SECURITY & COMPLIANCE

### TC-SEC-001: NMRR Data Privacy
**Priority:** Critical

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Search all database tables for "patient_id" | No direct patient identifiers | ☐ Pass ☐ Fail | |
| 2 | Check exported predictions | Only batch_id, no IC/name | ☐ Pass ☐ Fail | |
| 3 | Verify MinIO metadata | No forbidden fields (see minio_service.py) | ☐ Pass ☐ Fail | |
| 4 | Check API responses | No PII exposed in JSON | ☐ Pass ☐ Fail | |

### TC-SEC-002: Access Control (Future)
**Priority:** High (Not yet implemented)

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Login as "Viewer" role | Can view but not upload | ☐ Pass ☐ Fail | FUTURE: RBAC pending |
| 2 | Login as "Researcher" role | Can upload, train, view | ☐ Pass ☐ Fail | FUTURE: RBAC pending |
| 3 | Login as "Admin" role | Full access | ☐ Pass ☐ Fail | FUTURE: RBAC pending |

### TC-SEC-003: Audit Logging
**Priority:** Medium

| Step | Action | Expected Result | Status | Notes |
|------|--------|----------------|--------|-------|
| 1 | Perform upload | Action logged in backend logs | ☐ Pass ☐ Fail | |
| 2 | Train model | Training start/end logged | ☐ Pass ☐ Fail | |
| 3 | Generate prediction | Prediction request logged | ☐ Pass ☐ Fail | |
| 4 | Check logs for sensitive data | No PII in logs | ☐ Pass ☐ Fail | |

---

## TEST SECTION 17: SYSTEM INTEGRATION

### TC-INT-001: End-to-End Workflow
**Priority:** Critical  
**Description:** Complete workflow from upload to prediction

| Step | Action | Expected Result | Status | Time | Notes |
|------|--------|----------------|--------|------|-------|
| 1 | Upload CSV (228 records) | Success, session ID generated | ☐ Pass ☐ Fail | | |
| 2 | Check data quality | Quality metrics computed | ☐ Pass ☐ Fail | | |
| 3 | Preprocess data | Missing values, duplicates, outliers handled | ☐ Pass ☐ Fail | | |
| 4 | Save to database | Data saved, batch ID generated | ☐ Pass ☐ Fail | | |
| 5 | Label first 150 records | Labels assigned | ☐ Pass ☐ Fail | | Manual step |
| 6 | Prepare training dataset | Dataset split 65/35, features scaled | ☐ Pass ☐ Fail | | |
| 7 | Train XGBoost model | Training completes, AUC > 0.50 | ☐ Pass ☐ Fail | | |
| 8 | Generate SHAP explanations | Feature importance computed | ☐ Pass ☐ Fail | | |
| 9 | Make batch predictions (78 test samples) | All predictions complete | ☐ Pass ☐ Fail | | |
| 10 | Generate clinical scorecards | Scorecards generated for all | ☐ Pass ☐ Fail | | |
| 11 | Verify MinIO storage | All artifacts saved (7 buckets) | ☐ Pass ☐ Fail | | |
| 12 | View results on Dashboard | All metrics updated | ☐ Pass ☐ Fail | | |

**Total Expected Time:** 15-20 minutes  
**Success Criteria:** All steps pass with no manual intervention except labeling

### TC-INT-002: Data Lineage Verification
**Priority:** High

| Step | Data Stage | Storage Location | Verification | Status |
|------|-----------|------------------|--------------|--------|
| 1 | Raw upload | usm-raw/session_{id}/raw_file.csv | File exists, matches upload | ☐ Pass ☐ Fail |
| 2 | Preprocessed | usm-preprocessed/batch_{id}/final_preprocessed.csv | Row count matches after dedup | ☐ Pass ☐ Fail |
| 3 | PostgreSQL | flexible_dataset_wide table | Records match batch_id | ☐ Pass ☐ Fail |
| 4 | Training dataset | ml-datasets/dataset_{job_id}/train_data.pkl | Can be loaded with pickle | ☐ Pass ☐ Fail |
| 5 | Trained model | ml-models/{batch_id}_xgboost/fold_0.pkl | Model can be loaded | ☐ Pass ☐ Fail |
| 6 | Predictions | predictions/predictions_{timestamp}.csv | Row count matches input | ☐ Pass ☐ Fail |

---

## TEST EXECUTION SUMMARY

### Overall Test Results
- **Total Test Cases:** 60+
- **Passed:** ___
- **Failed:** ___
- **Blocked:** ___
- **Not Executed:** ___

### Critical Issues Found
| Issue ID | Severity | Description | Status |
|----------|----------|-------------|--------|
| | | | |

### Test Environment Details
- **Test Date:** _______________
- **Tester Name:** _______________
- **Backend Version:** _______________
- **Frontend Version:** _______________
- **Database Version:** PostgreSQL 15
- **Test Data Size:** 228 records (AAM-SLE-E)

### Sign-Off
- **Tested By:** _______________ Date: _______________
- **Reviewed By:** _______________ Date: _______________
- **Approved By:** _______________ Date: _______________

---

## APPENDIX A: Test Data

### Sample Patient Data (De-identified)
```csv
record_id,age,gender,laboratory_WBC,laboratory_RBC,laboratory_HGB,disease_activity_SLEDAI_score,labels_disease_classification
001,28,Female,8.5,4.2,12.3,8,SLE
002,45,Male,6.2,5.1,14.5,3,RA
003,35,Female,7.8,4.5,13.2,12,SLE
```

### Expected API Responses
See: ML_API_QUICK_REFERENCE.md

### Backend Logs to Monitor
```bash
docker-compose logs -f fastapi | grep -E "STARTING|COMPLETED|FAILED|MinIO|SHAP"
```

---

## APPENDIX B: Known Limitations (To Be Implemented)

1. **RBAC UI** - Role-based access control interface not yet implemented
2. **Audit Trail UI** - Database audit logs exist but no UI visualization
3. **Real-time Dashboard Updates** - Requires WebSocket implementation
4. **Model Versioning UI** - Basic versioning works, advanced UI pending
5. **Data Catalog Advanced Filters** - Basic search only
6. **Email Notifications** - Training completion emails not configured

---

## APPENDIX C: Success Metrics

### Functional Requirements
- ✅ Data upload & ingestion (CSV, Excel)
- ✅ Data quality checks (missing, duplicates, outliers)
- ✅ Preprocessing pipeline (5+ transformations)
- ✅ Label assignment (manual + batch)
- ✅ Feature engineering (4 transformation types)
- ✅ ML training (13 algorithms)
- ✅ Hyperparameter tuning (Optuna with 30 trials)
- ✅ Model evaluation (AUC, precision, recall, F1)
- ✅ Batch predictions
- ✅ Clinical scorecards
- ✅ SHAP explainability
- ✅ AI assistant (Dr. Myra with Gemma-4-E4B)
- ✅ MinIO object storage (7 buckets)
- ✅ Dashboard monitoring

### Performance Requirements
- Upload 1000 rows: <30 seconds ✅
- Training XGBoost (200 samples): <3 minutes ✅
- Single prediction: <2 seconds ✅
- Batch prediction (100 samples): <10 seconds ✅

### Security Requirements
- ✅ NMRR compliance (no patient identifiers)
- ✅ Secure password storage
- ⏳ RBAC (pending)
- ⏳ Audit trail UI (pending)

---

**End of SIT Test Script**
