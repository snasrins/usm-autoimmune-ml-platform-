# 🎯 USM Autoimmune ML Platform - Complete UI Implementation Guide

**Date:** April 20, 2026  
**Purpose:** End-to-end UI/UX specifications for research-grade clinical ML platform  
**Based on:** Today's implementations (preprocessing + dynamic scorecard) + existing APIs

---

## 📋 **TABLE OF CONTENTS**

1. [Dashboard (Home)](#1-dashboard-home)
2. [Data Ingestion](#2-data-ingestion)
3. [Data Quality & Preprocessing](#3-data-quality--preprocessing)
4. [Exploratory Data Analysis (EDA)](#4-exploratory-data-analysis-eda)
5. [Label Assignment](#5-label-assignment)
6. [Feature Engineering](#6-feature-engineering)
7. [Model Training](#7-model-training)
8. [Model Registry & Comparison](#8-model-registry--comparison)
9. [Clinical Scorecard System](#9-clinical-scorecard-system-new)
10. [Model Explainability (SHAP + LLM)](#10-model-explainability-shap--llm-new)
11. [Batch Prediction & Deployment](#11-batch-prediction--deployment)
12. [Patient Monitoring Dashboard](#12-patient-monitoring-dashboard-new)
13. [AI Assistant Chatbot](#13-ai-assistant-chatbot-optional)
14. [System Admin & Settings](#14-system-admin--settings)

---

## 🏠 **1. DASHBOARD (Home)**

**Route:** `/dashboard`  
**Sidebar Name:** 📊 **Dashboard**  
**Primary Function:** High-level overview of platform status and quick actions

### **Page Layout:**

#### **Top Section: Welcome Banner**
```
┌─────────────────────────────────────────────────────────────────┐
│  Welcome back, Dr. Syarifah Fajriyah                           │
│  Platform Status: ✅ All Systems Operational                    │
│  Last Activity: 2 hours ago                                     │
└─────────────────────────────────────────────────────────────────┘
```

#### **Key Metrics Cards (4 Cards in Row)**

1. **📁 Total Datasets**
   - Number: `125 datasets`
   - Status: `8 labeled`, `12 unlabeled`, `105 archived`
   - Quick Action: "Upload New Dataset"

2. **🤖 Models Trained**
   - Number: `47 models`
   - Status: `12 active`, `35 archived`
   - Best Accuracy: `0.9167 (RandomForest v2.1)`
   - Quick Action: "Train New Model"

3. **📋 Clinical Scorecards**
   - Number: `8 scorecards generated`
   - Latest: `RandomForest_v2.1_scorecard`
   - Quick Action: "Generate Scorecard"

4. **👥 Patients Predicted**
   - Total: `1,247 patients`
   - This Week: `23 new predictions`
   - Quick Action: "Run Batch Prediction"

#### **Recent Activity Timeline**
```
🕐 2 hours ago   | Model trained: XGBoost v1.3 (Accuracy: 0.8924)
🕐 5 hours ago   | Scorecard generated: RandomForest_v2.1
🕐 Yesterday     | 18 patients labeled (Batch: SLE-2026-04)
🕐 2 days ago    | Dataset uploaded: 111_patients_wide.csv
```

#### **Quick Actions Panel**
- **🚀 Start New Workflow** → Navigate to Data Ingestion
- **📊 View Model Performance** → Navigate to Model Comparison
- **🏥 Score New Patients** → Navigate to Batch Prediction
- **📈 Analyze Data** → Navigate to EDA

#### **System Status Cards**
- **GPU Usage:** Progress bar (45% utilized)
- **Storage:** 234 GB / 1 TB used
- **API Health:** All endpoints responding
- **Database:** PostgreSQL 15 (healthy)

---

## 📥 **2. DATA INGESTION**

**Route:** `/data-ingestion`  
**Sidebar Name:** 📥 **Data Ingestion**  
**Primary Function:** Upload and ingest patient data from multiple sources

### **Page Layout:**

#### **Top Banner with Instructions**
```
📥 DATA INGESTION
Upload patient data in CSV, Excel, or JSON format.
Platform supports both structured (wide format) and unstructured (clinical notes) data.
```

#### **Tab 1: Upload File**

##### **Upload Zone (Drag & Drop)**
```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                    📁 Drag & Drop Files Here                    │
│                                                                 │
│              or click to browse (CSV, XLSX, JSON)              │
│                                                                 │
│              Supported formats:                                 │
│              • Structured: CSV, Excel (.xlsx)                  │
│              • Unstructured: JSON (clinical notes)             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

##### **Upload Configuration**
- **Dataset Name:** Text input (e.g., "SLE Patients - April 2026")
- **Dataset Type:** Radio buttons
  - ○ Structured (Wide Format)
  - ○ Unstructured (Clinical Notes)
- **Source:** Dropdown (EMR Export, Manual Entry, Research Study, Other)
- **Description:** Textarea (Optional)

##### **Upload Button**
```
[🚀 Upload and Process Dataset]
```

**Expected Behavior:**
- Show progress bar during upload
- Display validation messages (file size, format check)
- On success: Create batch ID and show summary

#### **Tab 2: Recent Uploads**

##### **Batch Cards Grid (3 columns)**
Each card shows:
```
┌──────────────────────────────────────────┐
│ 📊 Batch: 9161cd88-e7bb-...             │
│                                          │
│ Dataset: 111_patients_wide.csv          │
│ Uploaded: 2026-04-19 14:30              │
│ Records: 111                             │
│ Status: ✅ Ready for Processing          │
│                                          │
│ [View Details] [Delete]                 │
└──────────────────────────────────────────┘
```

**Status Badges:**
- ✅ **Ready** (green) - Data validated, ready for labeling
- ⏳ **Processing** (yellow) - Currently being ingested
- ❌ **Failed** (red) - Validation errors detected
- 🏷️ **Labeled** (blue) - Labels assigned, ready for training

#### **Tab 3: Activity Log**

##### **Timeline View**
```
📅 April 20, 2026
  🕐 14:30 | Uploaded: 111_patients_wide.csv (111 records)
  🕐 12:15 | Deleted batch: test_data_old
  
📅 April 19, 2026
  🕐 16:45 | Uploaded: sle_cohort_2.xlsx (89 records)
  🕐 10:00 | Uploaded: ra_patients.csv (45 records)
```

**Filter Options:**
- Date range picker
- Filter by status
- Search by batch ID or filename

---

## 🔍 **3. DATA QUALITY & PREPROCESSING**

**Route:** `/data-quality`  
**Sidebar Name:** 🔍 **Data Quality**  
**Primary Function:** Check data quality and apply research-aligned preprocessing

### **Page Layout:**

#### **Top Section: Batch Selection**
```
Select Batch to Analyze:
[Dropdown: 9161cd88-e7bb... (111_patients_wide.csv)]  [Load Data]
```

#### **Tab 1: Quality Dashboard**

##### **Quality Score Card**
```
┌─────────────────────────────────────────────────────────────────┐
│                    QUALITY SCORE: 85/100                        │
│                   ●●●●●●●●●○ (Very Good)                        │
│                                                                 │
│  ✅ Data Completeness:      92% (Good)                          │
│  ⚠️  Missing Values:         8% (Acceptable)                    │
│  ✅ Duplicate Records:       0% (Excellent)                     │
│  ✅ Outliers Detected:       3% (Normal)                        │
│  ⚠️  Data Type Consistency:  89% (Needs Attention)              │
│                                                                 │
│  Recommendation: Apply imputation for missing values           │
└─────────────────────────────────────────────────────────────────┘
```

##### **Issues Found (Accordion)**
Click to expand each issue:
- **⚠️ Missing Values (8%)**
  - `WBC`: 5 missing (4.5%)
  - `HGB`: 3 missing (2.7%)
  - `PLT`: 1 missing (0.9%)
  
- **⚠️ Outliers Detected (3%)**
  - `CRP`: 2 extreme values (> 10.0)
  - `ESR`: 1 extreme value (> 120)

- **✅ No Duplicates Found**

#### **Tab 2: Preprocessing Configuration** ✨ **NEW** (Based on Today's Implementation)

##### **Preprocessing Options Panel**

**1. Imputation Settings**
```
☑ Apply Imputation for Missing Values

Numeric Strategy:  [Dropdown: Median ▼]
                   Options: Mean, Median, Most Frequent
                   
Categorical Strategy: [Dropdown: Most Frequent ▼]
                      Options: Most Frequent, Constant

[ℹ️ Info] Research study uses median for continuous, mode for categorical
```

**2. Outlier Handling (Winsorization)**
```
☑ Apply Winsorization

Lower Percentile: [Slider: 1%]  ──●────────────── 10%
Upper Percentile: [Slider: 99%] ──────────────●── 90%

[ℹ️ Info] Caps extreme values at specified percentiles
Research study uses 1% and 99%
```

**3. Composite Pathological Features**
```
☑ Create Composite Features

Low Risk Threshold:  [Slider: 10%]  ──●────────────── 30%
High Risk Threshold: [Slider: 70%] ─────────●────── 90%

Features to Create:
☑ Pancytopenia (ALL blood counts low)
☑ Cytopenia (ANY blood count low)
☑ Liver Damage (ANY liver enzyme high)
☑ High Inflammation (CRP/ESR ratio > 75th percentile)
☑ Low Complement (C3/C4 ratio < 25th percentile)

[ℹ️ Info] Based on research study methodology
```

**4. Target Variable Configuration**
```
Target Column: [Dropdown: labels_disease_severity ▼]
               Options: labels_disease_severity, disease_activity_SLEDAI_score

☐ Convert to SLEDAI Binary Target
  Threshold: [Input: 4.0]
  Rule: SLEDAI > 4.0 = High Activity
  
[ℹ️ Info] Research study uses SLEDAI binary for high activity prediction
```

**5. Standardization**
```
☑ Apply Feature Standardization

Method: [Dropdown: Standard (Z-score) ▼]
        Options: Standard, MinMax, Robust, None
        
[ℹ️ Info] Required for linear models (LR, SVM, MLP)
```

##### **Preset Configurations**
```
Quick Apply: [Dropdown: Research Study Configuration ▼]
             Options:
             • Research Study (median, 1%/99%, composite features)
             • Clinical Default (mean, no winsorization)
             • Custom (manual configuration)

[📄 Load Preset] [💾 Save as Preset]
```

##### **Apply Preprocessing Button**
```
[🔧 Apply Preprocessing to Dataset]
```

**Expected Behavior:**
- Show progress modal with steps:
  1. Imputing missing values...
  2. Winsorizing outliers...
  3. Creating composite features...
  4. Standardizing features...
- Display summary of changes:
  - "Imputed 234 missing values"
  - "Capped 87 outlier values"
  - "Created 5 composite features"
- Update quality score

#### **Tab 3: Preview Processed Data**

##### **Before/After Comparison Table**
```
Toggle View: (○ Before  ● After)

┌──────┬────────┬────────┬────────┬──────────────┐
│ ID   │ WBC    │ HGB    │ PLT    │ Pancytopenia │
├──────┼────────┼────────┼────────┼──────────────┤
│ P001 │ 4.5    │ 12.3   │ 250    │ No           │
│ P002 │ 2.1→2.8│ 10.5   │ 180    │ Yes          │ <-- Imputed
│ P003 │ 3.9    │ 11.2   │ 210    │ No           │
└──────┴────────┴────────┴────────┴──────────────┘

[📥 Export Processed Data (CSV)]
```

#### **Tab 4: Preprocessing Report**

##### **Summary Statistics Card**
```
PREPROCESSING SUMMARY
─────────────────────────────────────────────────────────
Original Records:     111
Final Records:        111 (no records dropped)
Original Features:    45
Final Features:       50 (+5 composite features)

Preprocessing Applied:
✅ Imputation:        234 values imputed
✅ Winsorization:     87 values capped
✅ Composite Features: 5 features created
✅ Standardization:   Applied (Standard scaler)

Quality Improvement:  78/100 → 92/100 (+14 points)
```

##### **Download Reports**
- **[📄 Download Preprocessing Report (PDF)]**
- **[📊 Download Quality Metrics (CSV)]**
- **[💾 Export Configuration (JSON)]**

---

## 📊 **4. EXPLORATORY DATA ANALYSIS (EDA)**

**Route:** `/eda`  
**Sidebar Name:** 📊 **EDA & Visualization**  
**Primary Function:** Interactive data exploration and statistical analysis

### **Page Layout:**

#### **Top Section: Dataset Selection**
```
Select Dataset: [Dropdown: 9161cd88... (preprocessed) ▼]  [Analyze]
```

#### **Tab 1: Statistical Overview**

##### **Summary Statistics Table**
```
┌────────────┬────────┬────────┬────────┬────────┬────────┐
│ Feature    │ Count  │ Mean   │ Std    │ Min    │ Max    │
├────────────┼────────┼────────┼────────┼────────┼────────┤
│ WBC        │ 111    │ 5.23   │ 2.14   │ 1.8    │ 12.5   │
│ HGB        │ 111    │ 11.85  │ 1.45   │ 8.2    │ 15.3   │
│ PLT        │ 111    │ 235.4  │ 67.2   │ 95     │ 450    │
└────────────┴────────┴────────┴────────┴────────┴────────┘

[📥 Export Statistics (CSV)]
```

##### **Missing Data Heatmap**
```
Interactive heatmap showing:
- Rows: Samples (patients)
- Columns: Features
- Color: Missing (red) vs Present (green)
- Hover tooltip: Show feature name and value
```

#### **Tab 2: Distributions**

##### **Feature Distribution Plots**
Select Feature: [Dropdown: WBC ▼]

**Visualization Options:**
- ○ Histogram
- ○ Box Plot
- ○ Violin Plot
- ● Density Plot

```
[Interactive Plot Area]
- Shows distribution of selected feature
- Overlay normal distribution curve
- Show mean, median, quartiles
- Highlight outliers
```

**Group By:** [Dropdown: Disease Severity ▼]
(Show distributions colored by target variable)

##### **Correlation Matrix**
```
Interactive heatmap:
- Correlation values between all features
- Color scale: Blue (negative) → White (0) → Red (positive)
- Click cell to see scatter plot of two features
- Highlight high correlations (>0.8)
```

#### **Tab 3: Feature Relationships**

##### **Scatter Plot Matrix**
```
Select Features (2-4): 
☑ WBC  ☑ HGB  ☑ PLT  ☐ CRP

[Generate Scatter Matrix]

Interactive grid showing:
- Pairwise scatter plots
- Diagonal: distributions
- Color by target variable
- Hover: show patient ID and values
```

##### **Parallel Coordinates Plot**
```
Shows multiple features simultaneously:
- Each vertical axis = one feature
- Each line = one patient
- Color by target variable
- Interactive: highlight/filter lines
```

#### **Tab 4: Target Variable Analysis**

##### **Class Distribution**
```
Target: labels_disease_severity

┌───────────┬───────┬────────────┐
│ Class     │ Count │ Percentage │
├───────────┼───────┼────────────┤
│ Mild      │ 45    │ 40.5%      │
│ Moderate  │ 38    │ 34.2%      │
│ Severe    │ 28    │ 25.2%      │
└───────────┴───────┴────────────┘

[Bar Chart Visualization]

Class Imbalance Ratio: 1.6:1 (Acceptable)
⚠️ Warning: If ratio > 3:1, consider SMOTE
```

##### **Feature Importance by Target**
```
Top 10 features correlated with target:

1. CRP_high         (ρ = 0.68)  ●●●●●●●●●●
2. ESR              (ρ = 0.62)  ●●●●●●●●●○
3. Anti-dsDNA       (ρ = 0.58)  ●●●●●●●●○○
4. C3               (ρ = -0.54) ●●●●●●●○○○
5. SLEDAI_score     (ρ = 0.52)  ●●●●●●●○○○
...

[📊 View Full Analysis]
```

---

## 🏷️ **5. LABEL ASSIGNMENT**

**Route:** `/labeling`  
**Sidebar Name:** 🏷️ **Label Assignment**  
**Primary Function:** Assign ground truth labels to patient records

### **Page Layout:**

#### **Top Section: Batch Selection & Statistics**
```
Select Batch: [Dropdown: 9161cd88... ▼]  [Load]

┌─────────────────────────────────────────────────────────────────┐
│  LABELING STATISTICS                                            │
│  ───────────────────────────────────────────────────────────    │
│  Total Records:     111                                         │
│  Labeled:           92  (82.9%)  ●●●●●●●●●○                     │
│  Unlabeled:         19  (17.1%)                                 │
│  Confidence:        High (>90%): 78, Medium (60-90%): 14        │
└─────────────────────────────────────────────────────────────────┘
```

#### **Tab 1: Manual Labeling**

##### **Patient Record Table**
```
Filter: [All ▼] [Unlabeled Only] [Labeled Only]
Search: [🔍 Search patient ID or features...]

┌─────┬──────────┬────────┬────────┬──────────┬───────────┬────────┐
│ ID  │ WBC      │ HGB    │ PLT    │ CRP      │ Label     │ Action │
├─────┼──────────┼────────┼────────┼──────────┼───────────┼────────┤
│ P001│ 4.5      │ 12.3   │ 250    │ 1.2      │ ⬜ Unlabel│ [Edit] │
│ P002│ 2.1      │ 10.5   │ 180    │ 3.5      │ Moderate  │ [Edit] │
│ P003│ 3.9      │ 11.2   │ 210    │ 0.8      │ Mild      │ [Edit] │
└─────┴──────────┴────────┴────────┴──────────┴───────────┴────────┘

Pagination: [< Prev] Page 1 of 12 [Next >]
```

**Click [Edit] to open Label Assignment Modal:**
```
┌─────────────────────────────────────────────────────────────────┐
│  ASSIGN LABEL - Patient P001                                    │
│  ───────────────────────────────────────────────────────────    │
│                                                                 │
│  Clinical Data Summary:                                         │
│  • WBC: 4.5 (Normal range: 4.0-11.0)                           │
│  • HGB: 12.3 (Normal)                                          │
│  • PLT: 250 (Normal)                                           │
│  • CRP: 1.2 (Slightly elevated)                                │
│  • SLEDAI Score: 6 (Moderate activity)                         │
│                                                                 │
│  Assign Diagnosis:                                              │
│  ○ SLE (Systemic Lupus Erythematosus)                         │
│  ○ RA (Rheumatoid Arthritis)                                   │
│  ○ Healthy Control                                             │
│  ● Other: [Text input]                                         │
│                                                                 │
│  Assign Severity:                                               │
│  ○ Mild                                                        │
│  ● Moderate                                                     │
│  ○ Severe                                                      │
│                                                                 │
│  Confidence:  [Slider: 85%] ──────────●──── 100%              │
│                                                                 │
│  Notes: [Textarea for additional comments]                    │
│                                                                 │
│  [Cancel]  [Save Label]                                        │
└─────────────────────────────────────────────────────────────────┘
```

#### **Tab 2: Batch Labeling**

##### **Rule-Based Labeling**
```
Create Labeling Rules:

Rule 1: IF SLEDAI_score > 12 THEN Severity = Severe

Conditions:
  Feature: [Dropdown: SLEDAI_score ▼]
  Operator: [Dropdown: > ▼]  (Options: >, <, =, >=, <=, between)
  Value: [Input: 12]

Assign Label:
  Label Type: [Dropdown: Severity ▼]
  Label Value: [Dropdown: Severe ▼]
  Confidence: [Slider: 95%]

[+ Add Another Rule]

[Apply Rules to Batch]
```

**Preview Affected Records:**
```
This rule will affect 23 records:
P005, P012, P018, P023... (show first 10, "and 13 more")

[Confirm and Apply]
```

#### **Tab 3: Import Labels**

##### **Upload Labels from File**
```
Upload CSV file with labels:

File Format:
┌──────────┬───────────┬──────────┬────────────┐
│ record_id│ diagnosis │ severity │ confidence │
├──────────┼───────────┼──────────┼────────────┤
│ P001     │ SLE       │ Moderate │ 0.90       │
│ P002     │ SLE       │ Severe   │ 0.95       │
└──────────┴───────────┴──────────┴────────────┘

[📁 Choose File]  [Upload and Import]
```

#### **Tab 4: Label Quality**

##### **Quality Metrics**
```
┌─────────────────────────────────────────────────────────────────┐
│  LABEL QUALITY ASSESSMENT                                       │
│  ───────────────────────────────────────────────────────────    │
│  Coverage:          82.9% (Need 90% for training)               │
│  Avg Confidence:    0.87 (Good)                                 │
│  Low Confidence:    14 records (need review)                    │
│  Label Distribution: Balanced ✅                                 │
│                                                                 │
│  ⚠️ Action Required: Label 9 more records to reach 90%          │
└─────────────────────────────────────────────────────────────────┘
```

##### **Label Distribution Chart**
```
[Pie Chart or Bar Chart]
- SLE: 65 (70.6%)
- RA: 18 (19.6%)
- Healthy: 9 (9.8%)
```

---

## ⚙️ **6. FEATURE ENGINEERING**

**Route:** `/feature-engineering`  
**Sidebar Name:** ⚙️ **Feature Engineering**  
**Primary Function:** Create, select, and transform features for ML

### **Page Layout:**

#### **Top Section: Dataset Selection**
```
Select Preprocessed Dataset: [Dropdown: 9161cd88... (preprocessed) ▼]
Current Features: 50  |  Target: labels_disease_severity
```

#### **Tab 1: Feature Selection (LASSO)**

##### **LASSO Configuration**
```
LASSO FEATURE SELECTION

Alpha (λ): [Slider: 0.01] ──●────────────── 1.0
          (Regularization strength)

Cross-Validation Folds: [Input: 5]

[🔍 Run LASSO Feature Selection]
```

**After running LASSO:**

##### **Feature Importance Chart**
```
TOP 15 SELECTED FEATURES (by coefficient magnitude)

1. CRP_high         Coef: 0.080  ●●●●●●●●●●
2. ESR_high         Coef: 0.071  ●●●●●●●●●○
3. C4               Coef: 0.066  ●●●●●●●●○○
4. Urine_protein    Coef: 0.065  ●●●●●●●●○○
5. ACR              Coef: 0.058  ●●●●●●●○○○
...

Total Features Selected: 12 / 50
R² Score: 0.78
Mean Absolute Error: 0.23

[📥 Export Feature Importance (CSV)]
```

##### **Feature Selection Table**
```
Manual Selection:

┌──────────────────────┬────────────┬──────────┬────────┐
│ Feature              │ LASSO Coef │ Selected │ Action │
├──────────────────────┼────────────┼──────────┼────────┤
│ CRP_high             │ 0.080      │ ☑        │ [Keep] │
│ ESR_high             │ 0.071      │ ☑        │ [Keep] │
│ C4                   │ 0.066      │ ☑        │ [Keep] │
│ WBC_low              │ 0.000      │ ☐        │ [Remove]│
└──────────────────────┴────────────┴──────────┴────────┘

[Select All LASSO Features]  [Clear Selection]
```

#### **Tab 2: Feature Transformation**

##### **Transformation Options**
```
AVAILABLE TRANSFORMATIONS

1. ☐ Log Transform
   Apply to skewed features (skewness > 1.5)
   Features: CRP, ESR, Anti-dsDNA (3 features)
   
2. ☐ Square Root Transform
   Apply to count data
   Features: WBC, PLT, Neutrophils (3 features)
   
3. ☐ Polynomial Features (Degree 2)
   Create interaction terms
   ⚠️ Warning: Increases features from 50 to 1,275
   
4. ☐ Binning (Discretization)
   Convert continuous to categorical bins
   Features: [Multi-select dropdown]
   Number of bins: [Input: 5]

[Apply Transformations]
```

#### **Tab 3: Feature Engineering Pipeline** ✨ **NEW**

##### **Pipeline Builder (Drag & Drop)**
```
Build Your Feature Engineering Pipeline:

┌─────────────────────────────────────────────────────────────────┐
│  PIPELINE STEPS                                                 │
│  ───────────────────────────────────────────────────────────    │
│  1. [Imputation]         (median/mode)                          │
│  2. [Winsorization]      (1%, 99%)                              │
│  3. [Composite Features] (pancytopenia, cytopenia, ...)         │
│  4. [LASSO Selection]    (α=0.01, 12 features)                  │
│  5. [Standardization]    (Standard scaler)                      │
│                                                                 │
│  [+ Add Step ▼]                                                 │
│  Options: Log Transform, Polynomial Features, Binning, ...     │
└─────────────────────────────────────────────────────────────────┘

[💾 Save Pipeline]  [▶️ Run Pipeline]  [📋 Load Saved Pipeline]
```

**Pipeline Presets:**
- **Research Study Pipeline** (Matches paper methodology)
- **Clinical Default Pipeline** (Conservative, explainable)
- **Deep Learning Pipeline** (More aggressive transformations)

#### **Tab 4: Feature Summary**

##### **Final Feature Set**
```
FINAL FEATURE SET SUMMARY

Original Features:     50
After Selection:       12
After Transformation:  15 (+3 engineered features)

Selected Features:
✅ CRP_high, ESR_high, C4, Urine_protein_quantification
✅ ACR, C3, PLT_high, NK, ALB, PLT_low
✅ Anticardiolipin_anti_antibody_IGM, HGB_high
✅ pancytopenia (composite)
✅ liver_damage (composite)
✅ high_inflammation (composite)

[📄 Export Feature List (CSV)]
[📊 Export Feature Statistics (JSON)]
```

---

## 🤖 **7. MODEL TRAINING**

**Route:** `/training`  
**Sidebar Name:** 🤖 **Model Training**  
**Primary Function:** Train ML models with hyperparameter tuning

### **Page Layout:**

#### **Top Section: Configuration Summary**
```
┌─────────────────────────────────────────────────────────────────┐
│  TRAINING CONFIGURATION                                         │
│  ───────────────────────────────────────────────────────────    │
│  Dataset: 9161cd88-e7bb... (111 samples)                        │
│  Features: 15 selected                                          │
│  Target: labels_disease_severity (3 classes: Mild, Moderate, Severe)│
│  Train/Test Split: 65% / 35% (72 train, 39 test)               │
│  Preprocessing: Research Study Configuration                    │
└─────────────────────────────────────────────────────────────────┘

[⚙️ Edit Configuration]
```

#### **Tab 1: Model Selection**

##### **All 11 Models from Research Study** ✨ **Based on Framework**
```
SELECT MODELS TO TRAIN (Check multiple):

Base Learners:
☑ Random Forest          (Ensemble, robust, interpretable)
☑ XGBoost               (Gradient boosting, high performance)
☑ LightGBM              (Fast gradient boosting)
☑ CatBoost              (Handles categorical features)
☑ Logistic Regression   (Linear, interpretable)
☑ Ridge Classifier      (Regularized linear)
☑ SVM (RBF Kernel)      (Non-linear decision boundary)
☑ MLP Neural Network    (Deep learning)
☑ K-Nearest Neighbors   (Instance-based learning)
☑ Naive Bayes           (Probabilistic classifier)
☑ Linear Discriminant   (Linear projection)

Meta-Learner (for Ensemble):
☐ Stacking Ensemble     (Combine all base learners above)
  Meta-model: [Dropdown: Logistic Regression ▼]

[Select All]  [Clear Selection]
```

#### **Tab 2: Hyperparameter Configuration**

##### **Per-Model Hyperparameter Tuning**

**Expand each model to configure:**

```
▼ Random Forest
  Hyperparameter Tuning: ● Optuna  ○ Grid Search  ○ Manual
  
  Number of Trials: [Input: 50]
  CV Folds: [Input: 5]
  
  Search Space:
  • n_estimators:     [10, 300]
  • max_depth:        [3, 20]
  • min_samples_split: [2, 20]
  • min_samples_leaf:  [1, 10]
  
  [Reset to Defaults]

▼ XGBoost
  (Similar configuration panel)
  
▼ Logistic Regression
  (Similar configuration panel)
```

**Quick Configuration Options:**
```
Preset Tuning Strategies:
[Dropdown: Balanced (Default) ▼]
  Options:
  • Fast (10 trials, quick results)
  • Balanced (50 trials, good performance)
  • Thorough (100 trials, best performance)
  • Custom (manual configuration)
```

#### **Tab 3: Training Progress**

##### **Training Dashboard (Real-Time Updates)**

**Overall Progress:**
```
┌─────────────────────────────────────────────────────────────────┐
│  TRAINING IN PROGRESS                                           │
│  ───────────────────────────────────────────────────────────    │
│  Models to Train: 11 base learners + 1 ensemble                 │
│  Progress: ●●●●●●●○○○○○ 6/12 (50%)                              │
│  Elapsed Time: 12m 34s                                          │
│  Estimated Remaining: 10m 15s                                   │
└─────────────────────────────────────────────────────────────────┘
```

**Model-by-Model Status:**
```
✅ Random Forest        Completed (Accuracy: 0.7568, Time: 2m 15s)
✅ XGBoost             Completed (Accuracy: 0.8108, Time: 3m 42s)
✅ LightGBM            Completed (Accuracy: 0.7838, Time: 2m 05s)
✅ CatBoost            Completed (Accuracy: 0.7838, Time: 3m 20s)
✅ Logistic Regression Completed (Accuracy: 0.8649, Time: 0m 45s)
⏳ Ridge Classifier     Training... (Trial 32/50)
⬜ SVM                  Queued
⬜ MLP                  Queued
⬜ KNN                  Queued
⬜ Naive Bayes          Queued
⬜ Linear Discriminant  Queued
⬜ Stacking Ensemble    Queued (after base learners)
```

**Live Metrics Chart:**
```
[Line Chart showing accuracy over trials for current model]
X-axis: Trial number
Y-axis: Accuracy
Animated update every 5 seconds
```

##### **Logs Panel (Collapsible)**
```
[2026-04-20 15:30:45] Starting training for Random Forest...
[2026-04-20 15:30:47] Trial 1/50: accuracy=0.7297
[2026-04-20 15:30:49] Trial 2/50: accuracy=0.7432
...
[2026-04-20 15:33:00] Best trial: 48 (accuracy=0.7568)
[2026-04-20 15:33:01] ✅ Random Forest training completed
```

#### **Tab 4: Training Results**

##### **Results Summary Table**
```
TRAINING COMPLETED ✅

┌───────────────────┬──────────┬───────────┬────────┬─────────┬─────────┐
│ Model             │ Accuracy │ Precision │ Recall │ F1 Score│ AUC-ROC │
├───────────────────┼──────────┼───────────┼────────┼─────────┼─────────┤
│ 🏆 Logistic Reg   │ 0.8649   │ 0.8571    │ 0.7359 │ 0.7921  │ 0.8667  │
│ XGBoost           │ 0.8108   │ 0.6923    │ 0.7200 │ 0.7059  │ 0.8600  │
│ SVM               │ 0.8378   │ 0.8000    │ 0.7273 │ 0.7619  │ 0.8667  │
│ Ridge Classifier  │ 0.8108   │ 0.6923    │ 0.7200 │ 0.7059  │ 0.8533  │
│ LightGBM          │ 0.7838   │ 0.6364    │ 0.6087 │ 0.6222  │ 0.8333  │
│ CatBoost          │ 0.7838   │ 0.6364    │ 0.6364 │ 0.6364  │ 0.8333  │
│ Random Forest     │ 0.7568   │ 0.6667    │ 0.5714 │ 0.6154  │ 0.8833  │
│ Linear Discriminant│0.7568   │ 0.5714    │ 0.6667 │ 0.6154  │ 0.8533  │
│ KNN               │ 0.7568   │ 0.6364    │ 0.6000 │ 0.6176  │ 0.8333  │
│ MLP               │ 0.7297   │ 0.5000    │ 0.5000 │ 0.5000  │ 0.7667  │
│ Naive Bayes       │ 0.7027   │ 0.5000    │ 0.5000 │ 0.5000  │ 0.7667  │
│ Stacking Ensemble │ 0.8649   │ 0.7333    │ 0.8148  │ 0.7719  │ 0.9167  │
└───────────────────┴──────────┴───────────┴────────┴─────────┴─────────┘

🏆 Best Model: Logistic Regression (Accuracy: 0.8649)
🎯 Best Ensemble: Stacking Ensemble (AUC: 0.9167)

[📊 View Detailed Comparison] → Navigate to Model Comparison
[🏥 Generate Scorecard] → Navigate to Scorecard System
[📥 Export All Results (CSV)]
```

---

## 📊 **8. MODEL REGISTRY & COMPARISON**

**Route:** `/models` (Registry) and `/model-comparison` (Comparison)  
**Sidebar Name:** 📊 **Model Registry** and **Model Comparison**

### **8.1 Model Registry Page** (`/models`)

#### **Page Layout:**

##### **Filter & Search**
```
Search Models: [🔍 Search by name, algorithm, or version...]

Filter By:
  Algorithm: [Dropdown: All ▼]
  Date Range: [Date Picker]
  Accuracy: [Slider: 0.0 ─────●──── 1.0]
  Status: [Dropdown: All ▼] (Active, Archived, Failed)

Sort By: [Dropdown: Accuracy (High to Low) ▼]
```

##### **Model Cards Grid (3 columns)**

Each card:
```
┌──────────────────────────────────────────┐
│ 🤖 Logistic Regression v2.1              │
│                                          │
│ Accuracy: 0.8649  ●●●●●●●●○○              │
│ F1 Score: 0.7921                         │
│ AUC-ROC:  0.8667                         │
│                                          │
│ Trained: 2026-04-20 15:45                │
│ Dataset: 111_patients (72/39 split)     │
│ Status: ✅ Active                         │
│                                          │
│ [View Details] [Compare] [Deploy]       │
│ [Generate Scorecard] [Archive]          │
└──────────────────────────────────────────┘
```

**Status Badges:**
- ✅ **Active** (green) - Ready for inference
- 🏆 **Best** (gold) - Highest performing model
- 📊 **Ensemble** (purple) - Stacking ensemble
- 📁 **Archived** (gray) - Old version

##### **Model Details Modal**

Click [View Details]:
```
┌─────────────────────────────────────────────────────────────────┐
│  LOGISTIC REGRESSION v2.1 - DETAILED METRICS                    │
│  ───────────────────────────────────────────────────────────    │
│                                                                 │
│  General Information:                                           │
│  • Model ID: lr-2026-04-20-154523                              │
│  • Algorithm: Logistic Regression (L2 regularization)          │
│  • Training Date: 2026-04-20 15:45:23                          │
│  • Training Duration: 45 seconds                               │
│  • Dataset: 9161cd88... (111 samples)                          │
│  • Features: 15 (after LASSO selection)                        │
│                                                                 │
│  Performance Metrics:                                           │
│  • Accuracy:  0.8649  (34/39 correct predictions)              │
│  • Precision: 0.8571  (30/35 positive predictions correct)     │
│  • Recall:    0.7359  (30/41 actual positives found)          │
│  • F1 Score:  0.7921                                           │
│  • AUC-ROC:   0.8667                                           │
│                                                                 │
│  Confusion Matrix:                                              │
│  ┌───────────┬──────────┬──────────┬──────────┐              │
│  │           │ Mild     │ Moderate │ Severe   │              │
│  ├───────────┼──────────┼──────────┼──────────┤              │
│  │ Mild      │ 21       │ 4        │ 0        │              │
│  │ Moderate  │ 1        │ 3        │ 0        │              │
│  │ Severe    │ 0        │ 1        │ 11       │              │
│  └───────────┴──────────┴──────────┴──────────┘              │
│                                                                 │
│  ROC Curve: [Interactive Plot]                                 │
│  • One-vs-Rest curves for each class                          │
│  • Area under curve for each                                  │
│                                                                 │
│  Hyperparameters:                                               │
│  • C (regularization): 1.0                                     │
│  • penalty: l2                                                 │
│  • solver: lbfgs                                               │
│  • max_iter: 1000                                              │
│                                                                 │
│  [📥 Export Metrics (JSON)]  [🔄 Retrain]  [Close]             │
└─────────────────────────────────────────────────────────────────┘
```

##### **Build Ensemble Button**
```
[🎯 Build Stacking Ensemble]
```

Opens modal:
```
┌─────────────────────────────────────────────────────────────────┐
│  BUILD STACKING ENSEMBLE                                        │
│  ───────────────────────────────────────────────────────────    │
│                                                                 │
│  Select Base Learners (2-11):                                   │
│  ☑ Logistic Regression v2.1     (Accuracy: 0.8649)             │
│  ☑ XGBoost v1.3                 (Accuracy: 0.8108)             │
│  ☑ SVM v2.0                     (Accuracy: 0.8378)             │
│  ☑ Random Forest v1.8           (Accuracy: 0.7568)             │
│  ☐ LightGBM v1.2                (Accuracy: 0.7838)             │
│  (... show all trained models)                                  │
│                                                                 │
│  Meta-Learner Algorithm:                                        │
│  ○ Logistic Regression (default, fast, interpretable)          │
│  ○ Random Forest (robust, handles non-linearity)               │
│  ○ XGBoost (best performance, slower)                          │
│                                                                 │
│  Cross-Validation Folds: [Input: 5]                            │
│                                                                 │
│  [Cancel]  [Train Ensemble]                                    │
└─────────────────────────────────────────────────────────────────┘
```

### **8.2 Model Comparison Page** (`/model-comparison`)

#### **Page Layout:**

##### **Model Selection**
```
SELECT MODELS TO COMPARE (2-4 models):

┌──────────────────────────────────────────┐
│ ☑ Logistic Regression v2.1               │
│   Accuracy: 0.8649  |  F1: 0.7921        │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│ ☑ XGBoost v1.3                           │
│   Accuracy: 0.8108  |  F1: 0.7059        │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│ ☑ Stacking Ensemble v1.0                 │
│   Accuracy: 0.8649  |  AUC: 0.9167       │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│ ☐ Random Forest v1.8                     │
│   Accuracy: 0.7568  |  F1: 0.6154        │
└──────────────────────────────────────────┘

[Compare Selected Models]
```

##### **Comparison Table**
```
SIDE-BY-SIDE COMPARISON

┌───────────────────┬────────────┬────────────┬──────────────────┐
│ Metric            │ Logistic   │ XGBoost    │ Stacking         │
│                   │ Regression │            │ Ensemble         │
├───────────────────┼────────────┼────────────┼──────────────────┤
│ Accuracy          │ 0.8649 🏆  │ 0.8108     │ 0.8649 🏆        │
│ Precision         │ 0.8571     │ 0.6923     │ 0.7333           │
│ Recall            │ 0.7359     │ 0.7200     │ 0.8148 🏆        │
│ F1 Score          │ 0.7921 🏆  │ 0.7059     │ 0.7719           │
│ AUC-ROC           │ 0.8667     │ 0.8600     │ 0.9167 🏆        │
│ Training Time     │ 45s 🏆     │ 3m 42s     │ 5m 15s           │
│ Inference Time    │ 2ms 🏆     │ 5ms        │ 8ms              │
│ Model Size        │ 12 KB 🏆   │ 245 KB     │ 380 KB           │
└───────────────────┴────────────┴────────────┴──────────────────┘

🏆 = Best in category
```

##### **Radar Chart Comparison**
```
[Interactive Radar Chart]
Axes: Accuracy, Precision, Recall, F1 Score, AUC-ROC
Each model as a different colored polygon
Hover to see exact values
```

##### **ROC Curves Overlay**
```
[Interactive Plot with 3 overlaid ROC curves]
- Logistic Regression (blue)
- XGBoost (orange)
- Stacking Ensemble (green)
Legend shows AUC for each
```

##### **Winner Summary Card**
```
┌─────────────────────────────────────────────────────────────────┐
│  🏆 RECOMMENDED MODEL                                            │
│  ───────────────────────────────────────────────────────────    │
│                                                                 │
│  Best Overall: Stacking Ensemble v1.0                           │
│  • Highest AUC-ROC: 0.9167                                      │
│  • Best Recall: 0.8148 (finds 81% of high-risk cases)          │
│  • Good Balance: Accuracy & Generalization                      │
│                                                                 │
│  Recommendation: Use for clinical decision support              │
│                                                                 │
│  Alternative: Logistic Regression v2.1                          │
│  • Fastest inference (2ms)                                      │
│  • Most interpretable (coefficients)                            │
│  • Use when explainability is critical                          │
│                                                                 │
│  [Deploy Stacking Ensemble]  [Generate Scorecard]               │
└─────────────────────────────────────────────────────────────────┘
```

##### **Export Options**
```
[📄 Export Comparison Report (PDF)]
[📊 Export Metrics Table (CSV)]
[📈 Export Charts (PNG)]
```

---

## 🏥 **9. CLINICAL SCORECARD SYSTEM** ✨ **NEW** (Based on Today's Implementation)

**Route:** `/scorecard`  
**Sidebar Name:** 🏥 **Clinical Scorecard**  
**Primary Function:** White-box clinical decision support with transparent scoring

### **Page Layout:**

#### **Top Section: Model Selection**
```
SELECT MODEL FOR SCORECARD GENERATION:

[Dropdown: Stacking Ensemble v1.0 (Best AUC: 0.9167) ▼]

Scorecard Status: ⬜ Not Generated  [Generate Scorecard]
                 or
                 ✅ Generated (2026-04-20 16:30)  [View Scorecard]
```

#### **Tab 1: Generate Scorecard**

##### **Configuration Panel**
```
SCORECARD GENERATION SETTINGS

Binning Method: [Dropdown: Rolling Mean (Research Study) ▼]
                Options:
                • Rolling Mean (data-driven cutpoints) 🏆
                • Quantile (equal frequency)
                • Equal Width (equal intervals)
                • Target-Based (maximize separation)
                • Tree-Based (decision tree splits)

Number of Bins per Feature: [Slider: 4] ──●────── 10

Use Youden Index: ☑ Optimize threshold statistically
                  [ℹ️] Maximizes sensitivity + specificity

[🎯 Generate Dynamic Scorecard]
```

**Progress Modal:**
```
┌─────────────────────────────────────────────────────────────────┐
│  GENERATING SCORECARD...                                        │
│  ───────────────────────────────────────────────────────────    │
│  ✅ Step 1: Fitting dynamic binning (rolling mean)...           │
│  ✅ Step 2: Calculating feature weights from model...           │
│  ✅ Step 3: Computing bin scores...                             │
│  ⏳ Step 4: Optimizing threshold with Youden Index...           │
│  ⬜ Step 5: Generating transparency tables...                    │
│                                                                 │
│  Progress: ●●●●●●●○○○ 70%                                       │
└─────────────────────────────────────────────────────────────────┘
```

#### **Tab 2: Bin-Score Tables** (White-Box System)

##### **Feature Selection**
```
View Bin-Score Table for: [Dropdown: NK (Natural Killer Cells) ▼]
```

##### **Transparent Lookup Table**
```
NK (NATURAL KILLER CELLS) - BIN-SCORE TABLE

┌────────────┬────────┬───────┬────────────┬─────────────────────┐
│    Bin     │ Score  │ Count │ Percentage │   Target Dist.      │
│   Range    │ Points │       │            │                     │
├────────────┼────────┼───────┼────────────┼─────────────────────┤
│  ≤ 1.10    │  1.7   │  15   │   13.5%    │ Mild: 20%, Sev: 80% │
│ 1.10-5.00  │  3.6   │  48   │   43.2%    │ Mild: 35%, Sev: 65% │
│ 5.00-6.10  │  2.7   │  32   │   28.8%    │ Mild: 45%, Sev: 55% │
│  > 6.10    │  1.8   │  16   │   14.4%    │ Mild: 60%, Sev: 40% │
└────────────┴────────┴───────┴────────────┴─────────────────────┘

💡 How to Use:
1. Find patient's NK value in lab results
2. Locate corresponding bin range
3. Note the score points
4. Repeat for all features
5. Sum total points
6. Compare to threshold (see Tab 3)

[📥 Export This Table (CSV)]
```

##### **All Features Table (Collapsible Sections)**
```
▼ Blood Count Features
  ├─ NK (Natural Killer Cells)      [View Table]
  ├─ WBC (White Blood Cells)        [View Table]
  ├─ HGB (Hemoglobin)              [View Table]
  └─ PLT (Platelets)               [View Table]

▼ Inflammatory Markers
  ├─ CRP (C-Reactive Protein)      [View Table]
  ├─ ESR (Erythrocyte Sedimentation Rate) [View Table]
  └─ Complement (C3, C4)           [View Table]

▼ Composite Features
  ├─ Pancytopenia                  [View Table]
  ├─ High Inflammation             [View Table]
  └─ Low Complement                [View Table]

[📥 Export All Tables (Excel)]
```

#### **Tab 3: Risk Stratification**

##### **Threshold Card**
```
┌─────────────────────────────────────────────────────────────────┐
│  YOUDEN INDEX OPTIMIZATION RESULTS                              │
│  ───────────────────────────────────────────────────────────    │
│  Optimal Threshold: 60.0 points                                 │
│  ═══════════════════════════════════                            │
│                                                                 │
│  Performance at This Threshold:                                 │
│  • Youden's J-Statistic: 0.582                                  │
│  • Sensitivity:  0.85  (Detects 85% of high-risk cases)        │
│  • Specificity:  0.73  (Correctly identifies 73% low-risk)     │
│                                                                 │
│  Clinical Decision Rule:                                        │
│  ────────────────────────                                       │
│  Score ≥ 60 points → HIGH RISK                                  │
│  Score < 60 points → LOW RISK                                   │
│                                                                 │
│  [ℹ️ Why Youden Index?]                                         │
│  Youden's J = Sensitivity + Specificity - 1                     │
│  Maximizes the balance between detecting true cases            │
│  and avoiding false alarms                                      │
└─────────────────────────────────────────────────────────────────┘
```

##### **Risk Stratification Performance (Test Set)**
```
TEST SET PERFORMANCE (39 patients)

┌──────────────────┬───────────┬──────────────┬──────────────┐
│   Risk Group     │   Count   │  Score Range │  High Risk % │
├──────────────────┼───────────┼──────────────┼──────────────┤
│   Low Risk       │    22     │  39.02-68.76 │    59.5%     │
│   High Risk      │    15     │  68.76-110.7 │    40.5%     │
└──────────────────┴───────────┴──────────────┴──────────────┘

Performance Metrics:
• Accuracy:   0.80  (31/39 correct classifications)
• Sensitivity: 0.85  (17/20 high-risk patients identified)
• Specificity: 0.73  (14/19 low-risk patients identified)
• PPV:        0.79  (17/22 predicted high-risk are correct)
• NPV:        0.81  (14/17 predicted low-risk are correct)

[📊 View Confusion Matrix]
```

##### **Score Distribution Chart**
```
[Histogram showing score distribution]
- X-axis: Total Score (0-100+)
- Y-axis: Number of patients
- Vertical line at threshold (60.0)
- Color: Blue (low risk) vs Red (high risk)
- Overlap region highlighted
```

#### **Tab 4: Patient Scoring Calculator** ✨ **Interactive Tool**

##### **Manual Score Calculation**
```
CALCULATE PATIENT RISK SCORE

Enter Patient Lab Values:

┌──────────────────┬─────────────┬─────────┬────────────┐
│ Feature          │ Lab Value   │ Bin     │ Score      │
├──────────────────┼─────────────┼─────────┼────────────┤
│ NK               │ [0.85     ]→│ ≤ 1.10  │ 1.7  ●○○○○ │
│ C4               │ [0.08     ]→│0.03-0.10│ 5.6  ●●●○○ │
│ IgM              │ [0.45     ]→│0.32-0.67│ 13.7 ●●●●● │
│ ALB              │ [0.85     ]→│0.67-1.22│ 4.5  ●●○○○ │
│ CRP              │ [1.20     ]→│ > 0.50  │ 19.0 ●●●●● │
│ Pancytopenia     │ [Yes ▼   ]→│ Present │ 8.3  ●●●●○ │
└──────────────────┴─────────────┴─────────┴────────────┘

                        TOTAL SCORE: 52.8 points

[🔄 Recalculate]  [📋 Clear Form]
```

##### **Risk Assessment Result**
```
┌─────────────────────────────────────────────────────────────────┐
│  RISK ASSESSMENT RESULT                                         │
│  ───────────────────────────────────────────────────────────    │
│                                                                 │
│  Total Score: 52.8 points                                       │
│  Threshold: 60.0 points                                         │
│                                                                 │
│  Decision: 52.8 < 60.0 → ✅ LOW RISK                            │
│                                                                 │
│  Clinical Recommendation:                                       │
│  • Routine monitoring                                           │
│  • Maintain current therapy                                     │
│  • Follow-up in 3-6 months                                      │
│                                                                 │
│  Confidence: Moderate (Score is 12% below threshold)            │
│                                                                 │
│  [📄 Generate Patient Report (PDF)]                             │
│  [💾 Save to Patient Record]                                    │
└─────────────────────────────────────────────────────────────────┘
```

**Visualization:**
```
[Score Gauge / Speedometer]
  0 ──────── 30 ──────── 60 ──────── 90 ──────── 100+
  │   LOW RISK         │      HIGH RISK            │
              ▲ 52.8
```

#### **Tab 5: Export Reports**

##### **Available Reports**
```
DOWNLOAD SCORECARD REPORTS

1. 📄 Bin-Score Tables (CSV)
   All features with transparent lookup tables
   Format: Feature, Bin_Range, Score_Points, Count, Target_Dist
   [Download]

2. 📊 Threshold Optimization Report (CSV)
   Youden Index results, sensitivity, specificity, threshold
   [Download]

3. 👥 Patient Scores (CSV) *if test data provided*
   Patient_ID, Total_Score, Risk_Group, Feature_Scores
   [Download]

4. 📑 Complete Scorecard Report (PDF)
   Comprehensive report with all tables, charts, and instructions
   [Download]

5. 📈 Model Performance Report (Excel)
   Risk stratification metrics, confusion matrix, ROC curve data
   [Download]

[📦 Download All Reports (ZIP)]
```

##### **Clinical Use Instructions (Collapsible)**
```
▼ How Clinicians Use the Scorecard

1. Open bin_score_tables.csv in Excel
2. Find patient's lab values
3. Look up each value in corresponding feature table
4. Note the score points for each feature
5. Sum all scores to get total
6. Compare total to threshold (60.0 points)
7. If Score ≥ 60 → High Risk (aggressive treatment)
8. If Score < 60 → Low Risk (routine monitoring)

✅ Clinicians can verify AI decision manually from lab results!
```

---

## 🔍 **10. MODEL EXPLAINABILITY (SHAP + LLM)** ✨ **NEW ADVANCED FEATURE**

**Route:** `/explainability`  
**Sidebar Name:** 🔍 **Model Explainability**  
**Primary Function:** Understand model predictions using SHAP values and AI-generated explanations

### **Page Layout:**

#### **Top Section: Model & Patient Selection**
```
Select Model: [Dropdown: Stacking Ensemble v1.0 ▼]

Explain Prediction For:
○ Single Patient (Upload patient data or select from test set)
● Batch Analysis (Explain multiple predictions)
○ Global Feature Importance (Overall model behavior)

[Load Explainability Analysis]
```

### **Tab 1: SHAP Values - Single Prediction**

##### **Patient Selection**
```
SELECT PATIENT TO EXPLAIN:

Option 1: Upload Patient Data
[📁 Upload CSV with patient features]

Option 2: Select from Test Set
[Dropdown: Patient P001 (Predicted: High Risk, Actual: High Risk) ▼]

[Analyze Prediction]
```

##### **SHAP Force Plot** (After Analysis)
```
┌─────────────────────────────────────────────────────────────────┐
│  SHAP FORCE PLOT - Patient P001                                 │
│  ───────────────────────────────────────────────────────────    │
│                                                                 │
│  Base Value: 0.45 (Average model prediction)                    │
│  ══════════════════════════════════════════════════             │
│                                                                 │
│  Features Pushing TOWARD High Risk:                             │
│  CRP_high (+0.18)    ████████████████                           │
│  ESR_high (+0.12)    ██████████                                 │
│  Low_C3 (+0.08)      ██████                                     │
│                                                                 │
│  Features Pushing TOWARD Low Risk:                              │
│  PLT_normal (-0.06)  ████                                       │
│  WBC_normal (-0.04)  ██                                         │
│                                                                 │
│  Final Prediction: 0.73 (High Risk)                             │
│  ══════════════════════════════════════════════════             │
│                                                                 │
│  [Interactive Visualization]                                    │
│  Hover over each feature to see exact SHAP value               │
└─────────────────────────────────────────────────────────────────┘
```

**Explanation:**
```
💡 What does this mean?

SHAP (SHapley Additive exPlanations) values show how much each 
feature contributed to moving the prediction from the average 
(base value = 0.45) to the final prediction (0.73).

• Positive SHAP values push toward HIGH RISK
• Negative SHAP values push toward LOW RISK
• Larger absolute values = stronger influence

For Patient P001:
✅ CRP_high has the strongest effect (+0.18)
✅ Combined inflammatory markers push risk up by +0.38
⚠️ Blood counts are normal, slightly reducing risk (-0.10)
📊 Final: 0.45 (base) + 0.28 (net push) = 0.73 (High Risk)
```

##### **SHAP Waterfall Plot**
```
[Interactive Waterfall Chart]

Starting Point (Base Value):              0.45
  + CRP_high = 1.5                       +0.18 → 0.63
  + ESR_high = 95                        +0.12 → 0.75
  + Low_C3 = 0.45                        +0.08 → 0.83
  - PLT_normal = 230                     -0.06 → 0.77
  - WBC_normal = 5.2                     -0.04 → 0.73
Final Prediction:                         0.73 (High Risk)

[📥 Export Chart (PNG)]
```

##### **Feature Contributions Table**
```
FEATURE CONTRIBUTIONS (Ranked by Absolute SHAP Value)

┌────────────────────┬───────────┬─────────────┬────────────┐
│ Feature            │ Value     │ SHAP Value  │ Effect     │
├────────────────────┼───────────┼─────────────┼────────────┤
│ CRP_high           │ 1.5       │ +0.18       │ ↑ High Risk│
│ ESR_high           │ 95        │ +0.12       │ ↑ High Risk│
│ Low_C3             │ 0.45      │ +0.08       │ ↑ High Risk│
│ PLT_normal         │ 230       │ -0.06       │ ↓ Low Risk │
│ WBC_normal         │ 5.2       │ -0.04       │ ↓ Low Risk │
│ Anti_dsDNA         │ 120       │ +0.03       │ ↑ High Risk│
└────────────────────┴───────────┴─────────────┴────────────┘

[📥 Export Table (CSV)]
```

### **Tab 2: AI-Generated Explanation** ✨ **LLM Integration**

##### **Natural Language Explanation (Generated by LLM)**

```
┌─────────────────────────────────────────────────────────────────┐
│  🤖 AI-GENERATED CLINICAL EXPLANATION                            │
│  ───────────────────────────────────────────────────────────    │
│                                                                 │
│  **Patient Risk Assessment for Patient P001**                   │
│                                                                 │
│  The model predicts this patient is at **HIGH RISK** (73%       │
│  confidence) for severe disease activity. Here's why:           │
│                                                                 │
│  **Key Risk Factors:**                                          │
│                                                                 │
│  1. **Elevated CRP (1.5 mg/dL)** - Strongest risk indicator    │
│     • CRP is significantly elevated, suggesting active          │
│       inflammation                                              │
│     • This single factor increases risk probability by 18%     │
│     • Clinical Note: CRP > 1.0 is associated with flare risk   │
│                                                                 │
│  2. **High ESR (95 mm/hr)** - Second strongest indicator        │
│     • ESR is markedly elevated, confirming systemic inflammation│
│     • Contributes an additional 12% to risk probability        │
│     • Combined CRP+ESR elevation is highly predictive           │
│                                                                 │
│  3. **Low Complement C3 (0.45 g/L)** - Immune system activation │
│     • C3 below normal range indicates complement consumption   │
│     • Adds 8% to risk probability                              │
│     • Suggests active immune complex formation                 │
│                                                                 │
│  **Protective Factors:**                                        │
│                                                                 │
│  1. **Normal Platelet Count (230 × 10⁹/L)**                     │
│     • Reduces risk by 6%                                       │
│     • No evidence of thrombocytopenia                          │
│                                                                 │
│  2. **Normal WBC (5.2 × 10⁹/L)**                                │
│     • Reduces risk by 4%                                       │
│     • No leukopenia detected                                   │
│                                                                 │
│  **Clinical Interpretation:**                                   │
│                                                                 │
│  The combination of elevated inflammatory markers (CRP, ESR) and│
│  low complement strongly suggests active disease. While blood    │
│  counts are reassuringly normal, the inflammatory profile       │
│  dominates the risk assessment.                                 │
│                                                                 │
│  **Recommended Actions:**                                       │
│  • Consider therapy escalation                                  │
│  • Repeat labs in 2-4 weeks                                     │
│  • Monitor for organ involvement                                │
│  • Assess SLEDAI score clinically                               │
│                                                                 │
│  **Confidence Assessment:**                                     │
│  The model is moderately confident (73%) due to:               │
│  ✅ Strong inflammatory markers                                  │
│  ✅ Consistent pattern across multiple features                  │
│  ⚠️ Some normal lab values create uncertainty                   │
│                                                                 │
│  This explanation was generated using advanced AI (GPT-4) based │
│  on SHAP analysis and clinical guidelines.                      │
│                                                                 │
│  [📄 Export Explanation (PDF)]  [🔄 Regenerate]                 │
└─────────────────────────────────────────────────────────────────┘
```

**LLM Configuration (Collapsible):**
```
▼ AI Explanation Settings

Model: [Dropdown: GPT-4 (Best Quality) ▼]
       Options: GPT-4, GPT-3.5-Turbo, Claude-3

Detail Level: [Slider] ──────●────── (Moderate)
              Options: Brief, Moderate, Detailed

Include Clinical Context: ☑
Include Lab Reference Ranges: ☑
Include Recommended Actions: ☑
Language: [Dropdown: English ▼]

[Apply Settings]
```

### **Tab 3: Global Feature Importance**

##### **SHAP Summary Plot (Beeswarm)**
```
[Interactive Beeswarm Plot]

Features (ranked by importance):
CRP_high         ●●●●●●●●●●●●●●●●●●●●●●●
ESR_high         ●●●●●●●●●●●●●●●●●
Low_C3           ●●●●●●●●●●●●●●
Anti_dsDNA       ●●●●●●●●●●●
Urine_protein    ●●●●●●●●●●
...

Color scale:
  Red (High feature value) → Blue (Low feature value)

Each dot = one patient
X-axis = SHAP value (impact on prediction)
Y-axis = Feature

Interpretation:
• Higher features have more impact on model predictions
• Red dots on right = high value pushes toward high risk
• Blue dots on left = low value pushes toward low risk
```

##### **SHAP Bar Plot (Mean Absolute SHAP)**
```
[Bar Chart]

Average Impact on Model Output (|SHAP|):

CRP_high             ●●●●●●●●●●  0.142
ESR_high             ●●●●●●●●○  0.118
Low_C3               ●●●●●●●○○  0.095
Anti_dsDNA           ●●●●●●○○○  0.087
Urine_protein        ●●●●●○○○○  0.076
C4                   ●●●●○○○○○  0.064
ALB                  ●●●○○○○○○  0.052
...

[📥 Export Global Importance (CSV)]
```

### **Tab 4: Batch Analysis**

##### **Upload Multiple Patients**
```
BATCH EXPLAINABILITY ANALYSIS

Upload CSV with multiple patients:
[📁 Choose File]

Expected format:
patient_id, WBC, HGB, PLT, CRP, ESR, ...

[Analyze Batch]
```

##### **Results Table**
```
BATCH SHAP ANALYSIS RESULTS (23 patients)

┌──────────┬───────────┬──────────────┬─────────────────────────┐
│ Patient  │ Prediction│ Confidence   │ Top Feature (SHAP)      │
├──────────┼───────────┼──────────────┼─────────────────────────┤
│ P001     │ High Risk │ 0.73         │ CRP_high (+0.18)        │
│ P002     │ High Risk │ 0.89         │ ESR_high (+0.22)        │
│ P003     │ Low Risk  │ 0.65         │ WBC_normal (-0.15)      │
│ ...      │ ...       │ ...          │ ...                     │
└──────────┴───────────┴──────────────┴─────────────────────────┘

[📊 View Individual SHAP Plots]  [📥 Export All (ZIP)]
```

##### **Aggregate Insights**
```
PATTERNS ACROSS BATCH

Most Important Features:
1. CRP_high (appeared in 18/23 explanations)
2. ESR_high (appeared in 16/23 explanations)
3. Low_C3 (appeared in 12/23 explanations)

Common Risk Patterns:
• Inflammatory markers dominate high-risk predictions
• Blood count abnormalities secondary indicators
• Complement levels critical for differentiation
```

### **Tab 5: Model Behavior Analysis**

##### **Dependence Plots**
```
Select Two Features to Compare:

Feature 1: [Dropdown: CRP_high ▼]
Feature 2: [Dropdown: ESR_high ▼]

[Generate Dependence Plot]

[Interactive Scatter Plot]
- X-axis: Feature 1 value
- Y-axis: SHAP value for Feature 1
- Color: Feature 2 value
- Shows interaction effects between features
```

##### **Decision Plot**
```
[SHAP Decision Plot]

Shows how prediction accumulates as model processes features:
- Y-axis: Features (in order processed)
- X-axis: Cumulative SHAP value
- Each line = one patient
- Diverging lines = different predictions

Useful for:
• Understanding feature order importance
• Comparing similar patients
• Identifying decision boundaries
```

---

### **💡 EXPLANATION: Why SHAP + LLM?**

#### **SHAP Values Provide:**
- **Quantitative** feature contributions
- **Mathematically rigorous** (game theory based)
- **Model-agnostic** (works with any ML model)
- **Local + Global** explanations
- **Visualizations** clinicians can understand

#### **LLM Enhancement Adds:**
- **Natural language** explanations
- **Clinical context** and interpretation
- **Actionable recommendations**
- **Personalized** to patient data
- **Accessible** to non-technical users

#### **Combined Benefits:**
1. **Trust**: Clinicians see exactly why model made prediction
2. **Transparency**: No "black box" - every decision explained
3. **Education**: Helps clinicians learn from model
4. **Safety**: Identify when model might be wrong
5. **Compliance**: Meets regulatory requirements for AI in healthcare

#### **Technical Implementation:**
```python
# Backend API endpoint
@router.post("/explainability/explain-prediction")
async def explain_prediction(
    model_name: str,
    patient_data: Dict
):
    # 1. Load model and make prediction
    model = load_model(model_name)
    prediction = model.predict(patient_data)
    
    # 2. Calculate SHAP values
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(patient_data)
    
    # 3. Generate LLM explanation
    llm_prompt = f"""
    Explain this prediction to a clinician:
    - Prediction: {prediction}
    - SHAP values: {shap_values}
    - Patient data: {patient_data}
    
    Provide clinical interpretation and recommendations.
    """
    llm_explanation = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": llm_prompt}]
    )
    
    return {
        "prediction": prediction,
        "shap_values": shap_values,
        "explanation": llm_explanation
    }
```

---

## 🚀 **11. BATCH PREDICTION & DEPLOYMENT**

**Route:** `/batch-prediction`  
**Sidebar Name:** 🚀 **Batch Prediction**  
**Primary Function:** Deploy models for inference on new patient data

### **Page Layout:**

#### **Step 1: Select Model**

##### **Model Selection Grid**
```
SELECT MODEL FOR DEPLOYMENT:

┌──────────────────────────────────────────┐
│ ○ Stacking Ensemble v1.0 🏆              │
│   Accuracy: 0.8649  |  AUC: 0.9167       │
│   Best for: High-stakes clinical decisions│
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│ ○ Logistic Regression v2.1               │
│   Accuracy: 0.8649  |  Inference: 2ms    │
│   Best for: Fast predictions, explainable│
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│ ○ Clinical Scorecard (Transparent)       │
│   Threshold: 60.0 points                 │
│   Best for: Manual verification required │
└──────────────────────────────────────────┘

[Next: Upload Data →]
```

#### **Step 2: Upload Patient Data**

##### **File Upload**
```
UPLOAD PATIENT DATA FOR PREDICTION

┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                    📁 Drag & Drop CSV File                       │
│                                                                 │
│                   or click to browse                            │
│                                                                 │
│  Required: CSV file with same features as training data        │
│  Format: patient_id, WBC, HGB, PLT, CRP, ESR, ...             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

File Requirements:
✅ CSV format
✅ Same column names as training data
✅ No missing target column (we'll predict it)
⚠️ Missing values will be imputed automatically

[📄 Download Template CSV]
```

**After Upload:**
```
FILE UPLOADED SUCCESSFULLY ✅

File: new_patients_april_2026.csv
Records: 23 patients
Columns: 15 features
Status: Validated ✅ (all required features present)

[← Back to Model Selection]  [Run Prediction →]
```

#### **Step 3: Run Prediction**

##### **Prediction Configuration**
```
PREDICTION OPTIONS

☑ Include Confidence Scores
☑ Include Probability Distribution
☑ Include SHAP Explanations (adds ~5s per patient)
☐ Generate Clinical Reports (PDF per patient)

[🚀 Run Batch Prediction]
```

**Progress Modal:**
```
┌─────────────────────────────────────────────────────────────────┐
│  RUNNING BATCH PREDICTION...                                    │
│  ───────────────────────────────────────────────────────────    │
│  Model: Stacking Ensemble v1.0                                  │
│  Patients: 23                                                   │
│                                                                 │
│  Progress: ●●●●●●●●●○ 18/23 (78%)                              │
│                                                                 │
│  Current: Processing Patient P018...                            │
│  Elapsed: 12s  |  Remaining: ~3s                                │
└─────────────────────────────────────────────────────────────────┘
```

#### **Step 4: View Results**

##### **Summary Cards**
```
┌────────────────────────┬────────────────────────┬────────────────────┐
│  TOTAL PROCESSED       │  PREDICTION DIST.      │  HIGH RISK CASES   │
│  ─────────────────     │  ─────────────────     │  ─────────────     │
│  23 patients           │  Severe:    8 (35%)    │  15 patients       │
│  ✅ Success: 23        │  Moderate: 10 (43%)    │  (Needs attention) │
│  ❌ Failed: 0          │  Mild:      5 (22%)    │                    │
└────────────────────────┴────────────────────────┴────────────────────┘
```

##### **Results Table**
```
PREDICTION RESULTS

Filter: [All ▼]  [High Risk Only]  [Low Confidence (<0.7)]
Sort By: [Confidence (Low to High) ▼]

┌─────────┬─────────────┬────────────┬─────────────────────────────┐
│ Patient │ Prediction  │ Confidence │ Probability Distribution    │
├─────────┼─────────────┼────────────┼─────────────────────────────┤
│ P001    │ Severe 🔴  │ 0.89       │ Mild:0.05|Mod:0.06|Sev:0.89 │
│ P002    │ Moderate🟡 │ 0.76       │ Mild:0.15|Mod:0.76|Sev:0.09 │
│ P003    │ Mild 🟢    │ 0.82       │ Mild:0.82|Mod:0.12|Sev:0.06 │
│ P004    │ Severe 🔴  │ 0.65 ⚠️    │ Mild:0.20|Mod:0.15|Sev:0.65 │
│ ...     │ ...         │ ...        │ ...                         │
└─────────┴─────────────┴────────────┴─────────────────────────────┘

⚠️ = Low confidence (< 0.70) - review manually

[📥 Export Results (CSV)]  [📊 View Detailed Report]
```

**Click on a row to see details:**
```
┌─────────────────────────────────────────────────────────────────┐
│  PATIENT P001 - DETAILED PREDICTION                             │
│  ───────────────────────────────────────────────────────────    │
│                                                                 │
│  Prediction: Severe (High Risk)                                 │
│  Confidence: 0.89 (Very High)                                   │
│                                                                 │
│  Probability Distribution:                                      │
│  • Mild:     0.05  ●○○○○○○○○○ (5%)                             │
│  • Moderate: 0.06  ●○○○○○○○○○ (6%)                             │
│  • Severe:   0.89  ●●●●●●●●●○ (89%) 🔴                          │
│                                                                 │
│  Top Contributing Features (SHAP):                              │
│  1. CRP_high: +0.22 (Very elevated CRP)                        │
│  2. ESR_high: +0.18 (High ESR)                                 │
│  3. Low_C3: +0.14 (Complement consumption)                     │
│                                                                 │
│  Clinical Recommendation:                                       │
│  • Urgent clinical evaluation required                         │
│  • Consider therapy escalation                                 │
│  • Monitor closely for organ involvement                       │
│                                                                 │
│  [View Full SHAP Explanation]  [Generate Clinical Report]     │
│  [Close]                                                       │
└─────────────────────────────────────────────────────────────────┘
```

##### **Download Options**
```
EXPORT PREDICTION RESULTS

Format:
○ CSV (predictions only)
● Excel (predictions + explanations + charts)
○ PDF Report (formatted clinical report)
○ JSON (for integration with other systems)

Include:
☑ Patient IDs
☑ Predictions
☑ Confidence scores
☑ Probability distributions
☑ SHAP values (if calculated)
☐ Clinical recommendations

[📥 Download Results]
```

#### **Step 5: Deploy as API**

##### **API Endpoint Generator**
```
DEPLOY MODEL AS REST API

Model: Stacking Ensemble v1.0
Endpoint: /api/v1/predict/stacking-ensemble-v1

API Documentation:

POST /api/v1/predict/stacking-ensemble-v1
Content-Type: application/json

Request Body:
{
  "patient_data": {
    "WBC": 4.5,
    "HGB": 12.3,
    "PLT": 250,
    "CRP": 1.2,
    "ESR": 45,
    ...
  }
}

Response:
{
  "prediction": "Moderate",
  "confidence": 0.76,
  "probabilities": {
    "Mild": 0.15,
    "Moderate": 0.76,
    "Severe": 0.09
  },
  "risk_score": 58.3,
  "risk_group": "Low Risk"
}

[📋 Copy cURL Command]  [📄 View Full API Docs]
```

**API Key Management:**
```
API KEYS

Create API key for external systems:
Name: [Input: EMR Integration]
Permissions: [Dropdown: Prediction Only ▼]
Rate Limit: [Input: 100] requests/hour

[+ Generate New API Key]

Existing Keys:
• emr_integration_2026  (Created: 2026-04-15, Last used: 2 hours ago)
• dashboard_app_key     (Created: 2026-04-01, Last used: 5 minutes ago)

[Revoke]  [Refresh]
```

---

## 👥 **12. PATIENT MONITORING DASHBOARD** ✨ **NEW CLINICAL FEATURE**

**Route:** `/patient-monitoring`  
**Sidebar Name:** 👥 **Patient Monitoring**  
**Primary Function:** Track individual patients over time, longitudinal analysis

### **Page Layout:**

#### **Top Section: Patient Search**
```
PATIENT MONITORING SYSTEM

Search Patient: [🔍 Enter patient ID or name...]

[+ Add New Patient]  [📊 View Cohort Analysis]
```

#### **Tab 1: Patient List**

##### **Patient Cards Grid**
```
MONITORED PATIENTS (45 patients)

Filter: [All ▼]  [High Risk]  [Requires Follow-up]
Sort By: [Last Prediction Date ▼]

┌──────────────────────────────────────────┐
│ 👤 Patient P001                          │
│    John Doe, 45M                         │
│                                          │
│ Current Risk: 🔴 High Risk (Score: 68.3) │
│ Trend: ↗️ Increasing (from 52.1)         │
│ Last Updated: 2 days ago                 │
│                                          │
│ Alerts: ⚠️ Score crossed threshold       │
│                                          │
│ [View Details] [Update Data]            │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│ 👤 Patient P002                          │
│    Jane Smith, 38F                       │
│                                          │
│ Current Risk: 🟢 Low Risk (Score: 45.2)  │
│ Trend: ↘️ Decreasing (from 58.7)         │
│ Last Updated: 1 week ago                 │
│                                          │
│ Alerts: ✅ Stable, routine follow-up     │
│                                          │
│ [View Details] [Update Data]            │
└──────────────────────────────────────────┘

(More cards...)
```

#### **Tab 2: Individual Patient Tracking**

##### **Patient Profile Header**
```
┌─────────────────────────────────────────────────────────────────┐
│  👤 PATIENT P001 - JOHN DOE                                      │
│  ───────────────────────────────────────────────────────────    │
│  Demographics: 45 years old, Male                               │
│  Diagnosis: SLE (Systemic Lupus Erythematosus)                 │
│  First Visit: 2025-06-15                                        │
│  Last Assessment: 2026-04-18 (2 days ago)                       │
│                                                                 │
│  Current Status: 🔴 HIGH RISK                                    │
│  Risk Score: 68.3 / 100 (Threshold: 60.0)                       │
│  Trend: ↗️ INCREASING (from 52.1 last month)                    │
└─────────────────────────────────────────────────────────────────┘
```

##### **Longitudinal Risk Score Chart**
```
[Interactive Line Chart]

Title: Risk Score Trajectory (Last 12 Months)

Y-axis: Risk Score (0-100)
X-axis: Date

Points on chart:
• 2025-05-15: 45.2 (Baseline)
• 2025-07-20: 48.3
• 2025-09-10: 52.1
• 2025-11-05: 55.8
• 2026-01-15: 51.3 (Treatment adjustment)
• 2026-03-20: 58.7
• 2026-04-18: 68.3 ⚠️ (Crossed threshold)

Horizontal line at threshold (60.0)
Color: Green (below threshold) → Red (above threshold)

Annotations:
📌 Treatment started (2025-06-20)
📌 Treatment adjusted (2026-01-15)
📌 Flare suspected (2026-04-18)

[📥 Export Chart (PNG)]
```

##### **Lab Values Over Time (Table)**
```
LONGITUDINAL LAB VALUES

┌────────────┬──────┬──────┬──────┬─────┬─────┬────────┐
│ Date       │ WBC  │ HGB  │ PLT  │ CRP │ ESR │ C3     │
├────────────┼──────┼──────┼──────┼─────┼─────┼────────┤
│ 2026-04-18 │ 3.2↓ │ 10.8↓│ 180↓ │ 2.5↑│ 95↑ │ 0.42↓  │
│ 2026-03-20 │ 4.1  │ 11.5 │ 210  │ 1.8↑│ 75↑ │ 0.55   │
│ 2026-01-15 │ 5.0  │ 12.1 │ 240  │ 1.2 │ 52  │ 0.68   │
│ 2025-11-05 │ 4.8  │ 12.5 │ 250  │ 0.9 │ 45  │ 0.72   │
└────────────┴──────┴──────┴──────┴─────┴─────┴────────┘

↑ = Above normal range
↓ = Below normal range

[📊 Visualize Trends] [📥 Export Table (CSV)]
```

##### **Feature Heatmap (Longitudinal)**
```
[Heatmap Visualization]

Rows: Features (WBC, HGB, PLT, CRP, ESR, C3, ...)
Columns: Date (visits)
Color: Red (abnormal) → Green (normal)

Shows patterns:
• Which features consistently abnormal
• Temporal correlation between features
• Response to treatment
```

##### **Alerts & Notifications**
```
CLINICAL ALERTS FOR PATIENT P001

⚠️  HIGH PRIORITY (2 alerts)
─────────────────────────────────────────────
• Risk score crossed threshold (68.3 > 60.0)
  Date: 2026-04-18
  Action: Schedule urgent follow-up
  
• CRP elevated > 2x normal for 2 consecutive visits
  Date: 2026-03-20, 2026-04-18
  Action: Consider therapy escalation

ℹ️  MEDIUM PRIORITY (1 alert)
─────────────────────────────────────────────
• Complement C3 declining trend
  Dates: Declining over last 6 months
  Action: Monitor closely

✅ LOW PRIORITY (0 alerts)

[Mark as Reviewed] [Create Follow-up Task]
```

##### **Treatment Timeline**
```
TREATMENT HISTORY

2025-06-20  Hydroxychloroquine 400mg started
2025-08-15  Prednisone 10mg added
2026-01-15  Prednisone increased to 20mg (flare)
2026-04-18  Awaiting rheumatology consult

[+ Add Treatment Note]
```

#### **Tab 3: Cohort Analysis**

##### **Risk Distribution (All Patients)**
```
COHORT RISK DISTRIBUTION (45 patients)

[Histogram]
X-axis: Risk Score (0-100)
Y-axis: Number of patients

Distribution:
• Low Risk (0-40):     12 patients (27%)
• Medium Risk (40-60): 18 patients (40%)
• High Risk (60-80):   10 patients (22%)
• Very High (80-100):   5 patients (11%)

Average Risk Score: 53.2
Median Risk Score: 51.8

[📊 View Detailed Statistics]
```

##### **Trending Patients (Action Needed)**
```
PATIENTS REQUIRING ATTENTION

Rapidly Worsening (Score increase > 10 in 30 days):
• P001: 52.1 → 68.3 (+16.2) ⚠️⚠️
• P015: 48.5 → 62.1 (+13.6) ⚠️⚠️
• P032: 55.2 → 66.8 (+11.6) ⚠️

Crossed Threshold Recently:
• P001, P015, P032, P038, P041 (5 patients)

Overdue for Follow-up (> 60 days):
• P008, P012, P023, P029 (4 patients)

[Generate Follow-up List] [Send Batch Reminders]
```

#### **Tab 4: Outcome Tracking**

##### **Clinical Outcomes**
```
OUTCOME TRACKING

Track patient outcomes over time:

┌──────────┬─────────────┬──────────────┬────────────────┐
│ Patient  │ Predicted   │ Actual       │ Outcome        │
│          │ (3mo ago)   │ (confirmed)  │ Accuracy       │
├──────────┼─────────────┼──────────────┼────────────────┤
│ P001     │ High Risk   │ Flare 🔴     │ ✅ Correct     │
│ P002     │ Low Risk    │ Stable 🟢    │ ✅ Correct     │
│ P003     │ High Risk   │ Stable 🟢    │ ❌ False Alarm │
│ P004     │ Low Risk    │ Flare 🔴     │ ❌ Missed      │
└──────────┴─────────────┴──────────────┴────────────────┘

Model Performance (Real-World):
• Accuracy: 0.82 (37/45 correct)
• Sensitivity: 0.88 (captures 88% of flares)
• Specificity: 0.78 (78% correct low-risk predictions)
• PPV: 0.75 (75% of high-risk predictions correct)

[Update Outcomes] [Generate Performance Report]
```

##### **Model Calibration**
```
[Calibration Plot]

X-axis: Predicted Risk Probability
Y-axis: Observed Event Rate

Ideal: Diagonal line (predicted = observed)
Actual: Shows if model over/under-predicts

Interpretation:
• Well-calibrated: Points close to diagonal
• Over-confident: Points below diagonal
• Under-confident: Points above diagonal
```

---

## 💬 **13. AI ASSISTANT CHATBOT** ✨ **OPTIONAL ADVANCED FEATURE**

**Route:** `/chatbot` or **Floating Widget** (accessible from any page)  
**Sidebar Name:** 💬 **AI Assistant**  
**Primary Function:** Conversational AI for platform guidance, data queries, and clinical decision support

### **💡 EXPLANATION: Should This Platform Have a Chatbot?**

#### **YES - Here's Why:**

**For Researchers:**
- ✅ **Natural Language Queries**: "Show me all patients with CRP > 2.0 and low C3"
- ✅ **Platform Guidance**: "How do I generate a scorecard?"
- ✅ **Data Insights**: "What's the average SLEDAI score in my cohort?"
- ✅ **Code Generation**: "Write Python code to load this dataset"

**For Clinicians:**
- ✅ **Quick Lookups**: "What does SHAP value mean?"
- ✅ **Risk Assessment**: "Is a risk score of 65 concerning?"
- ✅ **Treatment Guidance**: "What should I do for a high-risk patient?"
- ✅ **Lab Interpretation**: "Is CRP of 3.5 normal?"

**Technical Benefits:**
- ✅ **Reduces Training Time**: Users learn platform faster
- ✅ **Reduces Support Burden**: AI answers common questions
- ✅ **Improves Engagement**: More interactive experience
- ✅ **Data Accessibility**: Query data without SQL knowledge

**Challenges to Consider:**
- ⚠️ **Accuracy**: Medical advice must be accurate (use disclaimers)
- ⚠️ **Privacy**: Ensure patient data not sent to external LLM
- ⚠️ **Cost**: LLM API calls can be expensive
- ⚠️ **Liability**: Clear that AI is assistive, not prescriptive

**Recommendation:**
✅ **YES, implement chatbot BUT:**
1. Use for **platform guidance** and **data queries** primarily
2. Add **disclaimers** for clinical advice
3. Run LLM **locally** or use **private instance** (not OpenAI public API)
4. Store conversations for **audit trail**
5. Clear "This is AI assistance, not medical advice" messaging

---

### **Implementation:**

#### **Floating Chat Widget** (Accessible from Any Page)

```
[Bottom Right Corner of Screen]

┌────────────────────────────┐
│ 💬 AI Assistant            │
│ [Minimize] [X]             │
├────────────────────────────┤
│                            │
│ 🤖 Hi! I'm your AI         │
│    assistant. How can I    │
│    help you today?         │
│                            │
│    Try asking:             │
│    • "How do I train a     │
│      model?"               │
│    • "Show patients with   │
│      high CRP"             │
│    • "Explain SHAP values" │
│                            │
├────────────────────────────┤
│ [Type your question...]  ➤│
└────────────────────────────┘
```

#### **Conversation Examples:**

**Example 1: Platform Guidance**
```
User: How do I generate a clinical scorecard?

🤖 AI: To generate a clinical scorecard:

1. Navigate to "Clinical Scorecard" page (🏥 in sidebar)
2. Select your trained model from the dropdown
3. Configure scorecard settings:
   • Binning Method: Choose "Rolling Mean" (research-aligned)
   • Number of bins: 4 (recommended)
   • Enable "Use Youden Index" for optimal threshold
4. Click "Generate Dynamic Scorecard"
5. Wait 1-2 minutes for generation
6. View bin-score tables in Tab 2

Would you like me to navigate you there?

[Yes, take me there] [No, I'll do it myself]
```

**Example 2: Data Query**
```
User: Show me all patients with CRP > 2.0 and low complement

🤖 AI: I found 12 patients matching your criteria:

Patients with CRP > 2.0 AND C3 < 0.6:
• P001: CRP=2.5, C3=0.42 (High Risk)
• P015: CRP=3.1, C3=0.38 (High Risk)
• P022: CRP=2.8, C3=0.51 (Moderate Risk)
... (showing 3/12)

[View Full List] [Export to CSV] [Visualize]

Would you like me to:
• Generate predictions for these patients?
• Show their risk score trends?
• Compare lab values over time?
```

**Example 3: Clinical Question**
```
User: What does a risk score of 65 mean?

🤖 AI: A risk score of 65 means:

🔴 **HIGH RISK** (Above threshold of 60.0)

Clinical Interpretation:
• Patient is at elevated risk for disease flare
• Score is 8% above the statistical threshold
• Based on your model's Youden Index optimization

Recommended Actions:
• Schedule follow-up within 2-4 weeks
• Review lab trends (especially CRP, ESR, complement)
• Consider therapy adjustment if score increasing
• Monitor for organ involvement

⚠️ **Disclaimer**: This is AI-assisted guidance based on 
your model's scorecard. Always use clinical judgment and 
confirm with rheumatology assessment.

Would you like to see:
• SHAP explanation for a specific patient?
• Historical score trends?
• Treatment recommendations from literature?
```

**Example 4: Technical Assistance**
```
User: Write Python code to load my latest dataset

🤖 AI: Here's Python code to load your latest dataset:

```python
import requests

# API endpoint
url = "http://localhost:8000/api/v1/ml/train/prepare-dataset"

# Request payload
payload = {
    "batch_id": "9161cd88-e7bb-4ec7-9577-a129cde949ae",
    "target_column": "labels_disease_severity",
    "test_size": 0.35,
    "use_lasso_feature_selection": True,
    "lasso_alpha": 0.01,
    "apply_imputation": True,
    "apply_winsorization": True,
    "apply_composite_features": True
}

# Make request
response = requests.post(url, json=payload)
dataset = response.json()

# Access data
X_train = dataset['X_train']
y_train = dataset['y_train']
print(f"Loaded {len(X_train)} training samples")
```

[📋 Copy Code] [📖 View Full API Docs] [▶️ Run in Jupyter]

Need help understanding any part of this code?
```

#### **Chat Features:**

##### **Quick Actions Menu**
```
Click the ⚙️ icon in chat:

QUICK ACTIONS
─────────────────────────
📊 Show my datasets
🤖 List my models
👥 Recent predictions
📈 Training jobs status
🏥 Generate scorecard
📥 Export data
💡 Tutorial: Getting Started

SETTINGS
─────────────────────────
🔔 Enable notifications
🎨 Change theme
🔊 Voice input (beta)
🗑️ Clear conversation
```

##### **Context-Aware Responses**
```
AI is aware of:
• Current page you're viewing
• Your recent actions
• Your user role (researcher vs clinician)
• Platform state (models trained, datasets uploaded)

Example:
[You're on Model Training page]

User: How long will this take?

🤖 AI: Based on your current training configuration:
• Training 11 models (Random Forest, XGBoost, ...)
• 50 Optuna trials each
• 111 samples (72 train / 39 test)

Estimated Time:
• Fast models (Logistic Regression): ~45 seconds
• Medium models (Random Forest): ~2-3 minutes
• Slow models (XGBoost, MLP): ~3-5 minutes
• Total: ~25-30 minutes for all 11 models

💡 Tip: You're currently on page 6. You can navigate away 
and I'll notify you when training completes!

[OK] [Notify me when done]
```

##### **Multi-Modal Responses**
- **Text**: Explanations, guidance
- **Tables**: Query results
- **Charts**: Embedded visualizations
- **Code**: Copy-paste code snippets
- **Links**: Deep links to specific pages
- **Actions**: Buttons to execute tasks

#### **Privacy & Security:**

```
CHATBOT DATA POLICY

✅ What the AI can see:
• Your platform activity (anonymized)
• Aggregate statistics (no PHI)
• Documentation and guides
• Your explicit queries

❌ What the AI cannot see:
• Patient names or identifiable info
• Other users' data
• Unpublished research
• Your passwords/API keys

🔒 Data Security:
• Conversations stored encrypted
• Option to delete chat history
• No data sent to external LLM (runs locally)
• HIPAA-compliant logging

⚠️ Disclaimer:
This AI assistant is for guidance only. Always verify 
clinical decisions with licensed healthcare professionals.
Not a substitute for medical judgment.

[View Full Privacy Policy]
```

---

## ⚙️ **14. SYSTEM ADMIN & SETTINGS**

**Route:** `/admin` and `/settings`  
**Sidebar Name:** ⚙️ **Settings** and 🔧 **Admin** (admin only)

### **14.1 User Settings** (`/settings`)

#### **Profile Tab**
```
USER PROFILE

Name: [Input: Dr. Syarifah Fajriyah]
Email: [Input: syarifah@example.com]
Role: Researcher & Clinician

Organization: [Input: Universiti Sains Malaysia]
Department: [Input: School of Medical Sciences]

[Update Profile]
```

#### **Preferences Tab**
```
PLATFORM PREFERENCES

Theme:
○ Light Mode
● Dark Mode
○ Auto (Follow system)

Language: [Dropdown: English ▼]

Date Format: [Dropdown: YYYY-MM-DD ▼]

Notifications:
☑ Email notifications
☑ Browser notifications
☑ Training job completion alerts
☐ Daily digest emails

Default Settings:
Train/Test Split: [Input: 65% / 35%]
Random Seed: [Input: 42]
CV Folds: [Input: 5]

[Save Preferences]
```

#### **API Keys Tab**
```
API KEYS FOR EXTERNAL ACCESS

Personal API Keys:
┌────────────────┬──────────────┬─────────────┬────────┐
│ Key Name       │ Created      │ Last Used   │ Actions│
├────────────────┼──────────────┼─────────────┼────────┤
│ dashboard_key  │ 2026-04-01   │ 5 min ago   │[Revoke]│
│ jupyter_key    │ 2026-03-15   │ 2 days ago  │[Revoke]│
└────────────────┴──────────────┴─────────────┴────────┘

[+ Generate New API Key]

⚠️ Warning: Keep your API keys secure. Never share them or 
commit them to version control.

[View API Documentation]
```

### **14.2 Admin Panel** (`/admin`)

#### **Users Management Tab**
```
USER MANAGEMENT

[+ Add New User]  [Import from CSV]

┌───────────────┬──────────┬────────────┬──────────────┬────────┐
│ User          │ Email    │ Role       │ Last Login   │ Actions│
├───────────────┼──────────┼────────────┼──────────────┼────────┤
│ Syarifah F.   │ syari... │ Admin      │ 2 hours ago  │ [Edit] │
│ John Doe      │ john...  │ Researcher │ 1 day ago    │ [Edit] │
│ Jane Smith    │ jane...  │ Clinician  │ 3 days ago   │ [Edit] │
└───────────────┴──────────┴────────────┴──────────────┴────────┘

Roles:
• Admin: Full access
• Researcher: Data + ML access
• Clinician: View models + prediction access
• Viewer: Read-only access

[Export User List]
```

#### **System Status Tab**
```
SYSTEM HEALTH DASHBOARD

┌────────────────────────┬────────────────────────┐
│  DATABASE              │  API SERVICES          │
│  ─────────────────     │  ─────────────────     │
│  Status: ✅ Healthy    │  Status: ✅ All Up     │
│  Connections: 12/100   │  Avg Response: 85ms    │
│  Storage: 234 GB       │  Requests/min: 42      │
│  [View Details]        │  [View Logs]           │
└────────────────────────┴────────────────────────┘

┌────────────────────────┬────────────────────────┐
│  GPU                   │  STORAGE               │
│  ─────────────────     │  ─────────────────     │
│  Status: ✅ Available  │  Used: 234 GB / 1 TB   │
│  Utilization: 45%      │  Available: 766 GB     │
│  Memory: 8 GB / 24 GB  │  [Manage Storage]      │
│  [View GPU Monitor]    │                        │
└────────────────────────┴────────────────────────┘

[Run System Diagnostics] [View Error Logs] [Backup Database]
```

#### **Audit Logs Tab**
```
AUDIT LOG

Filter: [Date Range] [User: All ▼] [Action: All ▼]

┌─────────────────┬───────────────┬─────────────────────────────┐
│ Timestamp       │ User          │ Action                      │
├─────────────────┼───────────────┼─────────────────────────────┤
│ 2026-04-20 16:45│ Syarifah F.   │ Generated scorecard (RF v2.1)│
│ 2026-04-20 16:30│ Syarifah F.   │ Trained 11 models (Batch 91..)│
│ 2026-04-20 15:15│ John Doe      │ Uploaded dataset (111_pat...) │
│ 2026-04-20 14:00│ Jane Smith    │ Ran batch prediction (23 pat.)│
└─────────────────┴───────────────┴─────────────────────────────┘

[Export Audit Log (CSV)] [Filter]
```

---

## 📱 **RESPONSIVE DESIGN & MOBILE**

### **Desktop (Primary):**
- Full sidebar navigation
- Multi-column layouts
- Interactive charts and tables
- Drag-and-drop functionality

### **Tablet (1024px - 768px):**
- Collapsible sidebar
- 2-column layouts
- Touch-optimized buttons
- Simplified charts

### **Mobile (< 768px):**
- Bottom navigation bar
- Single-column layouts
- Swipe gestures
- Essential features only
- Progressive disclosure

---

## 🎨 **DESIGN SYSTEM SUMMARY**

### **Colors:**
- **Primary**: Purple (#6366F1)
- **Secondary**: Blue (#3B82F6)
- **Success**: Green (#10B981)
- **Warning**: Amber (#F59E0B)
- **Error**: Red (#EF4444)
- **Background**: Gradient (EBEBEE → E8E5F5 → F0EDF8)

### **Typography:**
- **Headings**: Inter, Bold
- **Body**: Inter, Regular
- **Code**: JetBrains Mono

### **Components:**
- Glass morphism cards
- Smooth transitions
- Purple gradient accents
- Rounded corners (16px)
- Shadows and depth
- Progress indicators

---

## 🚀 **IMPLEMENTATION PRIORITY**

### **Phase 1: Core (Weeks 1-4)**
1. ✅ Dashboard (already exists)
2. ✅ Data Ingestion (already exists)
3. ✅ Label Assignment (already exists)
4. ✅ Model Training (already exists)
5. ✅ Model Registry & Comparison (already exists)

### **Phase 2: Research Features (Weeks 5-8)** ✨ **HIGH PRIORITY**
6. **Data Quality & Preprocessing** (NEW - based on today's work)
7. **Clinical Scorecard System** (NEW - based on today's work)
8. **Batch Prediction** (already exists, enhance)

### **Phase 3: Advanced (Weeks 9-12)**
9. **Model Explainability (SHAP + LLM)** (NEW)
10. **Patient Monitoring Dashboard** (NEW)
11. **EDA Enhancement** (existing, add more viz)

### **Phase 4: Optional (Weeks 13-16)**
12. **AI Assistant Chatbot** (OPTIONAL)
13. **Advanced Analytics**
14. **Mobile App**

---

## 📊 **WHAT TO ADD / REMOVE**

### **✅ KEEP (Already Good):**
- Dashboard overview
- Data ingestion flow
- Model training workflow
- Model registry
- Basic model comparison

### **➕ ADD (Based on Today's Implementation):**
1. **Data Quality & Preprocessing Page** (research-aligned)
2. **Clinical Scorecard System** (white-box decision support)
3. **SHAP Explainability** (transparent AI)
4. **LLM-Generated Explanations** (natural language)
5. **Patient Monitoring Dashboard** (longitudinal tracking)
6. **AI Assistant Chatbot** (optional, but recommended)
7. **CSV Export for Scorecards** (already implemented backend)

### **❌ REMOVE / DEPRECATE:**
- Any hardcoded configurations (we made everything configurable today)
- Old preprocessing without research alignment
- Basic scorecard without dynamic binning
- Any manual threshold selection (now we use Youden Index)

---

## 📝 **FINAL RECOMMENDATIONS**

### **1. Immediate Actions (This Sprint):**
- ✅ Implement Data Quality & Preprocessing UI (Tab-based, like existing)
- ✅ Implement Clinical Scorecard UI (4 tabs: Generate, Tables, Risk, Calculator)
- ✅ Add CSV export buttons throughout

### **2. Next Sprint:**
- ✅ SHAP Explainability page
- ✅ LLM integration for explanations
- ✅ Patient Monitoring dashboard

### **3. Future Consideration:**
- AI Assistant Chatbot (3-4 weeks to implement well)
- Mobile app (6-8 weeks)
- Advanced analytics (ongoing)

---

🎯 **This is your complete UI roadmap based on today's implementations!**
