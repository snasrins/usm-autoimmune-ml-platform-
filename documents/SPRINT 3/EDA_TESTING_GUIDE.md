# EDA Platform Testing Guide
**Date:** April 2, 2026  
**Purpose:** Test EDA backend endpoints end-to-end

---

## 🎯 Test Preparation

### Prerequisites
1. ✅ Backend deployed with EDA endpoints
2. ✅ Database tables created (datasets, eda_reports)
3. ✅ User account with valid JWT token
4. ✅ Sample CSV/Excel dataset ready

### Get Authentication Token
```bash
# Login to get tokens
curl -X POST "http://192.168.196.97:8001/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testjwt&password=Test1234!"

# Save the access_token from response
export TOKEN="<your_access_token_here>"
```

---

## 📊 Test Scenarios

### Test 1: Upload Dataset (USMA-33)

**Objective:** Upload a CSV/Excel dataset successfully

**Prepare test data (test_sle_data.csv):**
```csv
patient_id,age,gender,ethnicity,ana_positive,complement_c3,complement_c4,sledai_score
P001,35,Female,Malay,TRUE,0.85,0.22,12
P002,42,Female,Chinese,TRUE,0.55,0.15,18
P003,28,Male,Indian,TRUE,0.92,0.25,8
P004,51,Female,Malay,TRUE,0.48,0.12,22
P005,39,Female,Chinese,TRUE,0.78,0.19,14
```

**Execute:**
```bash
curl -X POST "http://192.168.196.97:8001/api/v1/eda/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_sle_data.csv" \
  -F "name=SLE Test Dataset" \
  -F "description=Sample SLE patient data for testing"
```

**Expected Response (201):**
```json
{
  "success": true,
  "message": "Dataset uploaded successfully",
  "dataset": {
    "id": 1,
    "name": "SLE Test Dataset",
    "rows": 5,
    "columns": 8,
    "size_mb": 0.01,
    "missing_percentage": 0,
    "duplicate_rows": 0
  },
  "quality_summary": {
    "missing_values": 0,
    "duplicate_rows": 0,
    "columns_with_missing": 0
  }
}
```

**Validation:**
- ✅ Response status: 201 Created
- ✅ dataset.id returned (use in subsequent tests)
- ✅ Correct row count (5)
- ✅ Correct column count (8)

**Save dataset_id for next tests:**
```bash
export DATASET_ID=1
```

---

### Test 2: List Uploaded Datasets

**Execute:**
```bash
curl -X GET "http://192.168.196.97:8001/api/v1/eda/datasets" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response (200):**
```json
{
  "total": 1,
  "datasets": [
    {
      "id": 1,
      "name": "SLE Test Dataset",
      "description": "Sample SLE patient data for testing",
      "rows": 5,
      "columns": 8,
      "size_mb": 0.01,
      "missing_percentage": 0,
      "preprocessing_status": "raw",
      "uploaded_at": "2026-04-02T..."
    }
  ]
}
```

**Validation:**
- ✅ Dataset appears in list
- ✅ All metadata correct

---

### Test 3: Preview Dataset

**Execute:**
```bash
curl -X GET "http://192.168.196.97:8001/api/v1/eda/datasets/$DATASET_ID/preview?rows=3" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response (200):**
```json
{
  "dataset_id": 1,
  "dataset_name": "SLE Test Dataset",
  "total_rows": 5,
  "preview_rows": 3,
  "columns": [
    {"name": "patient_id", "dtype": "object", ...},
    {"name": "age", "dtype": "int64", ...},
    ...
  ],
  "data": [
    {"patient_id": "P001", "age": 35, "gender": "Female", ...},
    {"patient_id": "P002", "age": 42, "gender": "Female", ...},
    {"patient_id": "P003", "age": 28, "gender": "Male", ...}
  ]
}
```

**Validation:**
- ✅ Correct number of rows returned (3)
- ✅ Data matches uploaded CSV
- ✅ Column types detected correctly

---

### Test 4: Data Quality Analysis (USMA-26)

**Execute:**
```bash
curl -X GET "http://192.168.196.97:8001/api/v1/eda/datasets/$DATASET_ID/quality" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response (200):**
```json
{
  "dataset_id": 1,
  "dataset_name": "SLE Test Dataset",
  "quality_report": {
    "total_rows": 5,
    "total_columns": 8,
    "total_cells": 40,
    "memory_usage_mb": 0.01,
    "missing_values": {
      "total_missing": 0,
      "missing_percentage": 0,
      "columns_with_missing": {},
      "rows_with_missing": 0
    },
    "duplicates": {
      "duplicate_rows": 0,
      "duplicate_percentage": 0
    },
    "data_types": {
      "numeric_columns": ["age", "complement_c3", "complement_c4", "sledai_score"],
      "categorical_columns": ["patient_id", "gender", "ethnicity", "ana_positive"]
    },
    "column_info": [
      {
        "name": "age",
        "dtype": "int64",
        "non_null_count": 5,
        "null_count": 0,
        "unique_count": 5,
        "mean": 39.0,
        "min": 28,
        "max": 51
      },
      ...
    ]
  }
}
```

**Validation:**
- ✅ All columns analyzed
- ✅ Numeric columns have stats (mean, min, max)
- ✅ Categorical columns identified
- ✅ Missing value analysis present

---

### Test 5: Summary Statistics (USMA-33)

**Execute:**
```bash
curl -X GET "http://192.168.196.97:8001/api/v1/eda/datasets/$DATASET_ID/summary" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response (200):**
```json
{
  "dataset_id": 1,
  "dataset_name": "SLE Test Dataset",
  "summary_statistics": {
    "dataset_overview": {
      "total_rows": 5,
      "total_columns": 8,
      "memory_usage_mb": 0.01
    },
    "data_types": {
      "numeric_columns": 4,
      "categorical_columns": 4
    },
    "missing_data": {...},
    "duplicates": {...},
    "numeric_summary": {
      "age": {
        "count": 5,
        "mean": 39.0,
        "median": 39.0,
        "std": 8.6,
        "min": 28,
        "max": 51,
        "q25": 35,
        "q75": 42,
        "skewness": 0.45,
        "kurtosis": -1.2
      },
      "complement_c3": {...},
      "complement_c4": {...},
      "sledai_score": {...}
    },
    "categorical_summary": {
      "gender": {
        "count": 5,
        "unique_count": 2,
        "mode": "Female",
        "mode_frequency": 4,
        "mode_percentage": 80.0,
        "top_10_values": {"Female": 4, "Male": 1}
      },
      ...
    }
  }
}
```

**Validation:**
- ✅ Numeric summary has mean, median, std, etc.
- ✅ Categorical summary has mode, frequency
- ✅ Skewness and kurtosis calculated

---

### Test 6: Univariate Analysis (USMA-33)

**Execute:**
```bash
curl -X GET "http://192.168.196.97:8001/api/v1/eda/datasets/$DATASET_ID/univariate/age" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response (200):**
```json
{
  "column_name": "age",
  "data_type": "int64",
  "total_count": 5,
  "non_null_count": 5,
  "null_count": 0,
  "null_percentage": 0,
  "statistics": {
    "mean": 39.0,
    "median": 39.0,
    "std": 8.6,
    "min": 28,
    "max": 51,
    "range": 23,
    "q25": 35,
    "q75": 42,
    "iqr": 7,
    "skewness": 0.45,
    "kurtosis": -1.2
  },
  "distribution": {
    "is_normal": {
      "test": "shapiro_wilk",
      "p_value": 0.85,
      "is_normal": true,
      "interpretation": "Normal distribution"
    },
    "histogram_bins": {
      "bin_edges": [28, 30.7, 33.4, 36.1, 38.8, 41.5, 44.2, 46.9, 49.6, 52.3, 55],
      "counts": [1, 0, 1, 1, 1, 0, 1, 0, 0, 0]
    }
  },
  "outliers": {
    "outlier_count": 0,
    "outlier_percentage": 0,
    "lower_bound": 24.5,
    "upper_bound": 52.5
  }
}
```

**Validation:**
- ✅ Detailed statistics for column
- ✅ Normality test performed
- ✅ Histogram bins calculated
- ✅ Outlier detection performed

---

### Test 7: Bivariate Analysis (USMA-33)

**Execute:**
```bash
curl -X GET "http://192.168.196.97:8001/api/v1/eda/datasets/$DATASET_ID/bivariate" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response (200):**
```json
{
  "dataset_id": 1,
  "dataset_name": "SLE Test Dataset",
  "bivariate_analysis": {
    "correlation_matrix": {
      "columns": ["age", "complement_c3", "complement_c4", "sledai_score"],
      "values": [
        [1.0, -0.82, -0.75, 0.65],
        [-0.82, 1.0, 0.91, -0.78],
        [-0.75, 0.91, 1.0, -0.68],
        [0.65, -0.78, -0.68, 1.0]
      ]
    },
    "top_correlations": [
      {
        "variable_1": "complement_c3",
        "variable_2": "complement_c4",
        "correlation": 0.91,
        "abs_correlation": 0.91,
        "strength": "very_strong"
      },
      {
        "variable_1": "age",
        "variable_2": "complement_c3",
        "correlation": -0.82,
        "abs_correlation": 0.82,
        "strength": "strong"
      }
    ],
    "high_correlations": [...],
    "moderate_correlations": [...]
  }
}
```

**Validation:**
- ✅ Correlation matrix generated
- ✅ Top correlations identified
- ✅ Correlation strength classified

---

### Test 8: Outlier Detection (USMA-23)

**Execute (IQR method):**
```bash
curl -X GET "http://192.168.196.97:8001/api/v1/eda/datasets/$DATASET_ID/outliers?method=iqr&threshold=1.5" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response (200):**
```json
{
  "dataset_id": 1,
  "dataset_name": "SLE Test Dataset",
  "outlier_report": {
    "action": "outlier_detection",
    "method": "iqr",
    "outliers_detected": {
      "age": {
        "outlier_count": 0,
        "outlier_percentage": 0,
        "lower_bound": 24.5,
        "upper_bound": 52.5,
        "outlier_indices": []
      },
      "complement_c3": {...},
      "complement_c4": {...},
      "sledai_score": {...}
    },
    "total_outlier_rows": 0,
    "total_outlier_percentage": 0
  }
}
```

**Validation:**
- ✅ Outliers detected for each numeric column
- ✅ Bounds calculated correctly
- ✅ Outlier indices provided

---

### Test 9: Handle Missing Values (USMA-22)

**Prepare test data with missing values (test_with_nulls.csv):**
```csv
age,gender,complement_c3,sledai_score
35,Female,0.85,12
42,Male,,18
28,Female,0.92,
51,,0.48,22
39,Female,0.78,14
```

**Upload dataset with missing values:**
```bash
curl -X POST "http://192.168.196.97:8001/api/v1/eda/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_with_nulls.csv" \
  -F "name=Dataset with Missing Values"

# Save new dataset_id
export DATASET_ID_NULL=2
```

**Handle missing values:**
```bash
curl -X POST "http://192.168.196.97:8001/api/v1/eda/datasets/$DATASET_ID_NULL/preprocess/missing-values?threshold=0.5" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": {
      "complement_c3": "mean",
      "sledai_score": "median",
      "gender": "mode"
    }
  }'
```

**Expected Response (200):**
```json
{
  "success": true,
  "dataset_id": 2,
  "preprocessing_report": {
    "action": "missing_value_handling",
    "columns_dropped": [],
    "imputation_performed": {
      "complement_c3": {
        "strategy": "mean",
        "missing_before": 1,
        "missing_after": 0,
        "imputed_count": 1
      },
      "sledai_score": {
        "strategy": "median",
        "missing_before": 1,
        "missing_after": 0,
        "imputed_count": 1
      },
      "gender": {
        "strategy": "mode",
        "missing_before": 1,
        "missing_after": 0,
        "imputed_count": 1
      }
    },
    "rows_dropped": 0
  },
  "new_shape": {
    "rows": 5,
    "columns": 4
  }
}
```

**Validation:**
- ✅ Missing values imputed correctly
- ✅ No rows dropped (all imputed)
- ✅ Correct imputation counts

---

### Test 10: Categorical Encoding (USMA-24)

**Execute (auto encoding):**
```bash
curl -X POST "http://192.168.196.97:8001/api/v1/eda/datasets/$DATASET_ID/preprocess/encode?encoding_type=auto" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response (200):**
```json
{
  "success": true,
  "dataset_id": 1,
  "encoding_report": {
    "action": "categorical_encoding",
    "encoding_performed": {
      "gender": {
        "method": "label_encoding",
        "unique_values": 2,
        "mappings": {
          "Female": 0,
          "Male": 1
        }
      },
      "ethnicity": {
        "method": "onehot_encoding",
        "unique_values": 3,
        "new_columns": ["ethnicity_Chinese", "ethnicity_Indian", "ethnicity_Malay"]
      },
      "ana_positive": {
        "method": "label_encoding",
        "unique_values": 2,
        "mappings": {
          "TRUE": 1,
          "FALSE": 0
        }
      }
    }
  }
}
```

**Validation:**
- ✅ Binary variables label encoded
- ✅ Low cardinality variables one-hot encoded
- ✅ Mappings provided

---

### Test 11: Data Normalization (USMA-25)

**Execute (standard scaling):**
```bash
curl -X POST "http://192.168.196.97:8001/api/v1/eda/datasets/$DATASET_ID/preprocess/normalize?method=standard" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response (200):**
```json
{
  "success": true,
  "dataset_id": 1,
  "normalization_report": {
    "action": "normalization",
    "method": "standard",
    "normalization_performed": {
      "age": {
        "original_stats": {
          "mean": 39.0,
          "std": 8.6,
          "min": 28,
          "max": 51
        },
        "normalized_stats": {
          "mean": 0.0,
          "std": 1.0,
          "min": -1.28,
          "max": 1.40
        }
      },
      "complement_c3": {...},
      "complement_c4": {...},
      "sledai_score": {...}
    }
  }
}
```

**Validation:**
- ✅ Mean ≈ 0, Std ≈ 1 (standard scaling)
- ✅ Original stats preserved
- ✅ All numeric columns normalized

---

### Test 12: Get All EDA Reports

**Execute:**
```bash
curl -X GET "http://192.168.196.97:8001/api/v1/eda/datasets/$DATASET_ID/reports" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response (200):**
```json
{
  "dataset_id": 1,
  "dataset_name": "SLE Test Dataset",
  "total_reports": 4,
  "reports": [
    {
      "id": 1,
      "report_type": "summary",
      "generated_at": "2026-04-02T11:00:00",
      "analysis_results": {...}
    },
    {
      "id": 2,
      "report_type": "univariate",
      "generated_at": "2026-04-02T11:05:00",
      "analysis_results": {...}
    },
    {
      "id": 3,
      "report_type": "bivariate",
      "generated_at": "2026-04-02T11:10:00",
      "analysis_results": {...}
    },
    {
      "id": 4,
      "report_type": "outliers",
      "generated_at": "2026-04-02T11:15:00",
      "analysis_results": {...}
    }
  ]
}
```

**Validation:**
- ✅ All reports returned
- ✅ Correct report types
- ✅ Analysis results included

---

### Test 13: Delete Dataset

**Execute:**
```bash
curl -X DELETE "http://192.168.196.97:8001/api/v1/eda/datasets/$DATASET_ID" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response (200):**
```json
{
  "success": true,
  "message": "Dataset deleted successfully"
}
```

**Verify deletion:**
```bash
curl -X GET "http://192.168.196.97:8001/api/v1/eda/datasets" \
  -H "Authorization: Bearer $TOKEN"

# Dataset should not appear in list
```

**Validation:**
- ✅ Dataset soft deleted (is_deleted=true)
- ✅ No longer appears in list
- ✅ Cannot access deleted dataset

---

## ✅ All Tests Passed Checklist

- [ ] Test 1: Upload Dataset - PASS
- [ ] Test 2: List Datasets - PASS
- [ ] Test 3: Preview Dataset - PASS
- [ ] Test 4: Data Quality Analysis - PASS
- [ ] Test 5: Summary Statistics - PASS
- [ ] Test 6: Univariate Analysis - PASS
- [ ] Test 7: Bivariate Analysis - PASS
- [ ] Test 8: Outlier Detection - PASS
- [ ] Test 9: Handle Missing Values - PASS
- [ ] Test 10: Categorical Encoding - PASS
- [ ] Test 11: Data Normalization - PASS
- [ ] Test 12: Get All Reports - PASS
- [ ] Test 13: Delete Dataset - PASS

**All tests passed? EDA backend is production-ready!** 🎉
