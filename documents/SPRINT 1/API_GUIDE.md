# API Documentation & Usage Guide

## Base URL
```
http://172.24.175.24:8000
```

## Interactive Documentation
- **Swagger UI:** `http://172.24.175.24:8000/docs`
- **ReDoc:** `http://172.24.175.24:8000/redoc`

---

## Authentication

### Login
**Endpoint:** `POST /api/v1/auth/login`

**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 43200
}
```

**cURL Example:**
```bash
curl -X POST http://172.24.175.24:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

**Using Token:**
```bash
# Save token to variable
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Use in subsequent requests
curl -H "Authorization: Bearer $TOKEN" http://172.24.175.24:8000/api/v1/patients/
```

### Swagger UI Authorization
1. Click **"Authorize"** button (🔓 lock icon at top right)
2. Enter: `Bearer YOUR_ACCESS_TOKEN`
3. Click "Authorize" → "Close"
4. All subsequent requests will include token

---

## Upload & Import

### Import Clinical Dataset
**Endpoint:** `POST /api/v1/upload/import`

**Content-Type:** `multipart/form-data`

**Parameters:**
- `file` (file, required) - CSV, XLSX, Parquet, JSON, XML
- `disease_name` (string, required) - Disease name (e.g., "SLE", "Sjogren")
- `icd10_code` (string, optional) - ICD-10 code (e.g., "M32.9")
- `description` (string, optional) - Import notes

**Request (Swagger UI):**
1. Click "Try it out"
2. Click "Choose File" → Select your Excel/CSV file
3. Fill in `disease_name`: `SLE`
4. Fill in `icd10_code`: `M32.9`
5. Click "Execute"

**Response:**
```json
{
  "message": "Import completed",
  "file_id": 5,
  "results": {
    "total_rows": 110,
    "successful_patients": 109,
    "failed_patients": 1,
    "total_lab_results": 4907,
    "total_diagnoses": 109,
    "errors": [
      {
        "row": 59,
        "error": "Invalid date format",
        "details": "Could not parse '0 No 1 Yes' as date"
      }
    ]
  },
  "audit_id": 15
}
```

**cURL Example:**
```bash
curl -X POST http://172.24.175.24:8000/api/v1/upload/import \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/sle_patients.xlsx" \
  -F "disease_name=SLE" \
  -F "icd10_code=M32.9" \
  -F "description=Initial SLE cohort import"
```

**Python Example:**
```python
import requests

url = "http://172.24.175.24:8000/api/v1/upload/import"
headers = {"Authorization": f"Bearer {token}"}
files = {"file": open("sle_patients.xlsx", "rb")}
data = {
    "disease_name": "SLE",
    "icd10_code": "M32.9"
}

response = requests.post(url, headers=headers, files=files, data=data)
print(response.json())
```

---

### List Uploaded Files
**Endpoint:** `GET /api/v1/upload/files`

**Parameters:**
- `skip` (int) - Pagination offset (default: 0)
- `limit` (int) - Results per page (default: 50, max: 100)

**Response:**
```json
{
  "files": [
    {
      "file_id": 5,
      "original_filename": "sle_patients.xlsx",
      "file_hash": "sha256:abc123...",
      "file_size": 524288,
      "file_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "uploaded_at": "2026-03-16T12:00:00",
      "uploaded_by": "admin",
      "disease_name": "SLE",
      "import_status": "completed",
      "total_rows": 110,
      "successful_rows": 109
    }
  ],
  "total": 1
}
```

**cURL Example:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://172.24.175.24:8000/api/v1/upload/files?limit=10"
```

---

### Get Upload Details
**Endpoint:** `GET /api/v1/upload/files/{file_id}`

**Response:**
```json
{
  "file_id": 5,
  "original_filename": "sle_patients.xlsx",
  "file_hash": "sha256:abc123...",
  "uploaded_at": "2026-03-16T12:00:00",
  "disease_name": "SLE",
  "icd10_code": "M32.9",
  "column_mapping": {
    "WBC": {"test_code": "wbc", "confidence": 100},
    "CRP": {"test_code": "crp", "confidence": 95}
  },
  "import_results": {
    "total_rows": 110,
    "successful_patients": 109,
    "failed_patients": 1,
    "errors": [...]
  },
  "audit_records": [
    {
      "audit_id": 15,
      "import_timestamp": "2026-03-16T12:00:05",
      "status": "completed"
    }
  ]
}
```

---

## Patient Queries

### Search Patients
**Endpoint:** `GET /api/v1/patients/`

**Parameters:**
- `disease_name` (string) - Filter by disease (partial match)
- `disease_code` (string) - Filter by ICD-10 code
- `age_min` (int) - Minimum age
- `age_max` (int) - Maximum age
- `gender` (string) - Male/Female/Other
- `test_code` (string) - Filter patients who have this test
- `test_abnormal` (boolean) - Filter patients with abnormal results
- `limit` (int) - Results per page (default: 50, max: 500)
- `offset` (int) - Pagination offset

**Example 1: All Patients**
```bash
GET /api/v1/patients/?limit=10
```

**Example 2: Female SLE Patients**
```bash
GET /api/v1/patients/?disease_name=sle&gender=f&limit=20
```

**Example 3: Patients with Abnormal WBC**
```bash
GET /api/v1/patients/?test_code=wbc&test_abnormal=true
```

**Example 4: Age Range 30-50**
```bash
GET /api/v1/patients/?age_min=30&age_max=50
```

**Response:**
```json
{
  "patients": [
    {
      "id": 171,
      "anonymous_id": "USMA-2026-0059",
      "age": 32,
      "age_range": "30-39",
      "gender": "Male",
      "ethnicity": null,
      "diagnoses": [
        {
          "disease_name": "SLE",
          "icd10_code": "M32.9",
          "diagnosis_date": "2025-01-15",
          "severity": "Moderate"
        }
      ]
    }
  ],
  "total": 52,
  "limit": 10,
  "offset": 0
}
```

**cURL Example:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://172.24.175.24:8000/api/v1/patients/?disease_name=sle&limit=10"
```

**Python Example:**
```python
params = {
    "disease_name": "sle",
    "gender": "f",
    "age_min": 25,
    "age_max": 45,
    "limit": 20
}
response = requests.get(
    "http://172.24.175.24:8000/api/v1/patients/",
    headers={"Authorization": f"Bearer {token}"},
    params=params
)
patients = response.json()["patients"]
```

---

### Get Patient Details
**Endpoint:** `GET /api/v1/patients/{patient_id}`

**Response:**
```json
{
  "patient_id": 171,
  "anonymous_id": "USMA-2026-0059",
  "age": 32,
  "age_range": "30-39",
  "gender": "Male",
  "ethnicity": null,
  "diagnoses": [
    {
      "diagnosis_id": 201,
      "disease_name": "SLE",
      "icd10_code": "M32.9",
      "diagnosis_date": "2025-01-15",
      "severity": "Moderate"
    }
  ],
  "lab_results": [
    {
      "result_id": 5001,
      "test_code": "wbc",
      "test_name": "WBC",
      "test_category": "Hematology",
      "test_date": "2026-03-01",
      "value_numeric": 5.2,
      "value_text": null,
      "unit": "10^9/L",
      "is_abnormal": false,
      "abnormal_flag": null
    },
    {
      "result_id": 5002,
      "test_code": "crp",
      "test_name": "CRP",
      "test_category": "Inflammation",
      "test_date": "2026-03-01",
      "value_numeric": 15.3,
      "value_text": null,
      "unit": "mg/L",
      "is_abnormal": true,
      "abnormal_flag": "H"
    }
  ],
  "disease_data": [
    {
      "data_id": 301,
      "disease_name": "SLE",
      "data_category": "Clinical_Score",
      "data": {
        "sledai_score": 8,
        "organ_involvement": ["Renal", "Joint"]
      }
    }
  ]
}
```

---

### Get Patient Summary
**Endpoint:** `GET /api/v1/patients/{patient_id}/summary`

**Response:**
```json
{
  "patient_id": 171,
  "anonymous_id": "USMA-2026-0059",
  "age": 32,
  "gender": "Male",
  "summary": {
    "total_diagnoses": 1,
    "total_lab_results": 45,
    "abnormal_results": 18,
    "abnormal_rate": 40.0,
    "unique_tests": 12,
    "first_test_date": "2025-02-10",
    "last_test_date": "2026-03-01"
  }
}
```

---

### Get Patient Lab Results
**Endpoint:** `GET /api/v1/patients/{patient_id}/labs`

**Parameters:**
- `test_code` (string) - Filter by specific test
- `test_category` (string) - Filter by category (Hematology, Inflammation, etc.)
- `date_from` (date) - Filter from date (YYYY-MM-DD)
- `date_to` (date) - Filter to date (YYYY-MM-DD)
- `abnormal_only` (boolean) - Show only abnormal results
- `limit` (int) - Results per page

**Example: All WBC Results**
```bash
GET /api/v1/patients/171/labs?test_code=wbc
```

**Example: Inflammatory Markers**
```bash
GET /api/v1/patients/171/labs?test_category=Inflammation
```

**Example: Recent Tests (Last 3 Months)**
```bash
GET /api/v1/patients/171/labs?date_from=2025-12-01&date_to=2026-03-01
```

**Response:**
```json
{
  "patient_id": 171,
  "total_results": 45,
  "results": [
    {
      "result_id": 5001,
      "test_code": "wbc",
      "test_name": "WBC",
      "test_date": "2026-03-01",
      "value_numeric": 5.2,
      "unit": "10^9/L",
      "is_abnormal": false
    }
  ]
}
```

---

### Get Lab Trends (Time Series)
**Endpoint:** `GET /api/v1/patients/{patient_id}/labs/trends`

**Parameters:**
- `test_code` (string, required) - Test to track
- `test_category` (string) - Alternative to test_code
- `date_from` (date) - Start date
- `date_to` (date) - End date
- `limit` (int) - Max results

**Example: Track CRP Over Time**
```bash
GET /api/v1/patients/171/labs/trends?test_code=crp&date_from=2026-01-01
```

**Response:**
```json
{
  "patient_id": 171,
  "test_code": "crp",
  "test_name": "CRP",
  "unit": "mg/L",
  "trends": [
    {
      "test_date": "2026-01-15",
      "value_numeric": 8.5,
      "is_abnormal": false
    },
    {
      "test_date": "2026-02-01",
      "value_numeric": 12.3,
      "is_abnormal": true,
      "abnormal_flag": "H"
    },
    {
      "test_date": "2026-03-01",
      "value_numeric": 15.3,
      "is_abnormal": true,
      "abnormal_flag": "H"
    }
  ]
}
```

**Use Case:** Track treatment response - is CRP decreasing after medication?

---

### Get Abnormal Lab Results
**Endpoint:** `GET /api/v1/patients/{patient_id}/labs/abnormal`

**Parameters:**
- `severity` (string) - Filter by flag (H, L, HH, LL)

**Example: Only Critically High**
```bash
GET /api/v1/patients/171/labs/abnormal?severity=HH
```

**Response:**
```json
{
  "patient_id": 171,
  "abnormal_results": [
    {
      "result_id": 5002,
      "test_code": "crp",
      "test_name": "CRP",
      "test_date": "2026-03-01",
      "value_numeric": 15.3,
      "unit": "mg/L",
      "is_abnormal": true,
      "abnormal_flag": "H",
      "reference_range": {
        "normal": {"min": 0, "max": 5},
        "critical_high": 10
      }
    }
  ],
  "total": 18
}
```

---

### Compare Test Results Across Patients
**Endpoint:** `POST /api/v1/patients/compare`

**Request:**
```json
{
  "patient_ids": [171, 172, 173],
  "test_code": "crp",
  "date_from": "2026-01-01",
  "date_to": "2026-03-01"
}
```

**Response:**
```json
{
  "test_code": "crp",
  "test_name": "CRP",
  "unit": "mg/L",
  "comparison": [
    {
      "patient_id": 171,
      "anonymous_id": "USMA-2026-0059",
      "results": [
        {"test_date": "2026-03-01", "value_numeric": 15.3}
      ],
      "mean": 12.0,
      "latest_value": 15.3
    },
    {
      "patient_id": 172,
      "anonymous_id": "USMA-2026-0060",
      "results": [
        {"test_date": "2026-03-01", "value_numeric": 4.2}
      ],
      "mean": 4.8,
      "latest_value": 4.2
    }
  ]
}
```

**Use Case:** Compare CRP levels across a cohort

---

## Test Statistics & Analytics

### Get Test Statistics
**Endpoint:** `GET /api/v1/patients/tests/{test_code}/statistics`

**Parameters:**
- `disease_name` (string) - Filter by disease

**Example: WBC Statistics for All Patients**
```bash
GET /api/v1/patients/tests/wbc/statistics
```

**Example: CRP Statistics for SLE Only**
```bash
GET /api/v1/patients/tests/crp/statistics?disease_name=sle
```

**Response:**
```json
{
  "test_code": "wbc",
  "test_name": "WBC",
  "test_category": "Hematology",
  "unit": "10^9/L",
  "statistics": {
    "mean": 5.73,
    "median": 4.8,
    "std": 3.97,
    "min": 1.23,
    "max": 26.64,
    "total_results": 51,
    "abnormal_count": 18,
    "abnormal_rate": 35.29
  },
  "reference_range": {
    "normal": {"min": 4.0, "max": 11.0},
    "critical_low": 2.0,
    "critical_high": 20.0
  }
}
```

**Use Case:** Population-level statistics for research

**cURL Example:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://172.24.175.24:8000/api/v1/patients/tests/wbc/statistics"
```

**Python Example:**
```python
response = requests.get(
    "http://172.24.175.24:8000/api/v1/patients/tests/crp/statistics",
    headers={"Authorization": f"Bearer {token}"},
    params={"disease_name": "sle"}
)
stats = response.json()["statistics"]
print(f"Mean CRP: {stats['mean']}, Abnormal Rate: {stats['abnormal_rate']}%")
```

---

### Query Disease-Specific Data (JSONB)
**Endpoint:** `GET /api/v1/patients/disease-data`

**Parameters:**
- `disease_name` (string, required) - Disease to query
- `data_category` (string) - Category filter
- `jsonb_filter` (JSON string) - Key-value filters

**Example 1: All SLE Clinical Scores**
```bash
GET /api/v1/patients/disease-data?disease_name=SLE&data_category=Clinical_Score
```

**Example 2: Patients with SLEDAI > 8**
```bash
GET /api/v1/patients/disease-data?disease_name=SLE&jsonb_filter={"sledai_score":{"gt":8}}
```

**Response:**
```json
{
  "disease_name": "SLE",
  "data_category": "Clinical_Score",
  "results": [
    {
      "data_id": 301,
      "patient_id": 171,
      "anonymous_id": "USMA-2026-0059",
      "data": {
        "sledai_score": 12,
        "sledai_date": "2026-03-01",
        "organ_involvement": ["Renal", "CNS", "Joint"]
      }
    }
  ],
  "total": 15
}
```

**Use Case:** Find high-risk patients (SLEDAI > 10)

---

## Admin: Test Management

### List All Lab Tests
**Endpoint:** `GET /api/v1/admin/tests/`

**Parameters:**
- `test_category` (string) - Filter by category
- `is_active` (boolean) - Show active/inactive tests
- `include_inactive` (boolean) - Include inactive tests
- `limit` (int) - Results per page

**Response:**
```json
{
  "tests": [
    {
      "test_id": 1,
      "test_code": "wbc",
      "test_name": "WBC",
      "test_category": "Hematology",
      "data_type": "numeric",
      "unit": "10^9/L",
      "reference_ranges": {
        "normal": {"min": 4.0, "max": 11.0}
      },
      "is_active": true,
      "created_date": "2026-03-16"
    }
  ],
  "total": 56,
  "limit": 50,
  "offset": 0
}
```

---

### Get Test Categories
**Endpoint:** `GET /api/v1/admin/tests/categories`

**Response:**
```json
{
  "categories": [
    {
      "category": "Hematology",
      "test_count": 5,
      "tests": ["wbc", "neu_percent", "lym_percent", "hgb", "plt"]
    },
    {
      "category": "Inflammation",
      "test_count": 3,
      "tests": ["crp", "esr", "alb"]
    },
    {
      "category": "Complement",
      "test_count": 2,
      "tests": ["c3", "c4"]
    }
  ],
  "total_categories": 12,
  "total_tests": 56
}
```

---

### Get Pending Tests (Approval Workflow)
**Endpoint:** `GET /api/v1/admin/tests/pending`

**Response:**
```json
{
  "pending_tests": [
    {
      "test_id": 99,
      "test_code": "custom_test_123",
      "test_name": "Custom Test 123",
      "test_category": "Biomarker",
      "data_type": "numeric",
      "is_active": false,
      "created_date": "2026-03-16",
      "reason": "Auto-created during import (unmapped column)"
    }
  ],
  "total": 2
}
```

---

### Get Test Statistics (Admin View)
**Endpoint:** `GET /api/v1/admin/tests/statistics`

**Response:**
```json
{
  "total_tests": 56,
  "active_tests": 54,
  "pending_approval": 2,
  "categories": 12,
  "numeric_tests": 42,
  "qualitative_tests": 14,
  "most_used_tests": [
    {"test_code": "wbc", "result_count": 51},
    {"test_code": "crp", "result_count": 48}
  ]
}
```

---

### Create New Test
**Endpoint:** `POST /api/v1/admin/tests/`

**Request:**
```json
{
  "test_code": "il6",
  "test_name": "Interleukin-6",
  "test_category": "Cytokine",
  "data_type": "numeric",
  "unit": "pg/mL",
  "reference_ranges": {
    "normal": {"min": 0, "max": 5},
    "critical_high": 10
  }
}
```

**Response:**
```json
{
  "test_id": 100,
  "test_code": "il6",
  "message": "Test created successfully",
  "is_active": true
}
```

---

### Update Test
**Endpoint:** `PUT /api/v1/admin/tests/{test_id}`

**Request:**
```json
{
  "test_name": "Interleukin-6 (Updated)",
  "reference_ranges": {
    "normal": {"min": 0, "max": 7}
  },
  "is_active": true
}
```

---

### Delete Test
**Endpoint:** `DELETE /api/v1/admin/tests/{test_id}`

**Note:** This marks test as inactive, not hard delete (preserves audit trail)

---

## Health & System Status

### Health Check
**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "api_version": "1.0.0",
  "uptime_seconds": 86400
}
```

---

## Error Handling

### Error Response Format
```json
{
  "detail": "Error message",
  "error_code": "VALIDATION_ERROR",
  "field": "disease_name",
  "timestamp": "2026-03-16T12:00:00"
}
```

### Common HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation error)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `422` - Unprocessable Entity (invalid data)
- `500` - Internal Server Error

### Example Error Responses

**401 Unauthorized:**
```json
{
  "detail": "Not authenticated"
}
```

**404 Not Found:**
```json
{
  "detail": "Patient with ID 999 not found"
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "disease_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Rate Limiting & Performance

### Current Limits
- No rate limiting implemented yet
- Recommended: 100 requests/minute per user

### Performance Guidelines
- Use pagination (`limit` parameter) for large datasets
- Cache frequently accessed data (test catalog)
- Use specific filters to reduce result size
- Batch operations when possible (compare endpoint)

---

## Python SDK Example

```python
import requests
from typing import List, Dict, Optional

class USMAutoimmunePlatform:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.token = self._login(username, password)
        
    def _login(self, username: str, password: str) -> str:
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        return response.json()["access_token"]
    
    def _headers(self) -> Dict:
        return {"Authorization": f"Bearer {self.token}"}
    
    def upload_dataset(self, file_path: str, disease_name: str, icd10_code: str = None):
        with open(file_path, "rb") as f:
            files = {"file": f}
            data = {"disease_name": disease_name}
            if icd10_code:
                data["icd10_code"] = icd10_code
            
            response = requests.post(
                f"{self.base_url}/api/v1/upload/import",
                headers=self._headers(),
                files=files,
                data=data
            )
            response.raise_for_status()
            return response.json()
    
    def search_patients(self, disease_name: str = None, age_min: int = None, 
                       age_max: int = None, limit: int = 50):
        params = {"limit": limit}
        if disease_name:
            params["disease_name"] = disease_name
        if age_min:
            params["age_min"] = age_min
        if age_max:
            params["age_max"] = age_max
        
        response = requests.get(
            f"{self.base_url}/api/v1/patients/",
            headers=self._headers(),
            params=params
        )
        response.raise_for_status()
        return response.json()["patients"]
    
    def get_test_statistics(self, test_code: str, disease_name: str = None):
        params = {}
        if disease_name:
            params["disease_name"] = disease_name
        
        response = requests.get(
            f"{self.base_url}/api/v1/patients/tests/{test_code}/statistics",
            headers=self._headers(),
            params=params
        )
        response.raise_for_status()
        return response.json()["statistics"]

# Usage
platform = USMAutoimmunePlatform(
    "http://172.24.175.24:8000",
    "admin",
    "admin123"
)

# Upload dataset
result = platform.upload_dataset("sle_patients.xlsx", "SLE", "M32.9")
print(f"Imported {result['results']['successful_patients']} patients")

# Search patients
patients = platform.search_patients(disease_name="sle", age_min=30, age_max=50)
print(f"Found {len(patients)} patients")

# Get statistics
stats = platform.get_test_statistics("wbc", "sle")
print(f"WBC mean: {stats['mean']}, abnormal rate: {stats['abnormal_rate']}%")
```

---

## Next Steps

1. **Test All Endpoints:** Use Swagger UI to verify functionality
2. **Import More Data:** Test with Sjogren dataset
3. **Build Frontend:** Create UI for common workflows
4. **Add More Tests:** Cover edge cases and error handling
5. **Performance Testing:** Load test with large datasets
6. **Documentation:** Add more examples and use cases
