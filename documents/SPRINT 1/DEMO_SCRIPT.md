# USM Backend Demo Walkthrough

## Demo Objective
Showcase the complete data ingestion and query capabilities of the Autoimmune Disease ML Platform backend, demonstrating multi-disease support, data anonymization, flexible storage, and advanced query features.

**Duration:** 30-45 minutes  
**Audience:** USM clinical researchers, data managers, IT staff  
**Format:** Live interactive demo via Swagger UI

---

## Pre-Demo Checklist

### System Ready
- [ ] Server accessible at `http://172.24.175.24:8000`
- [ ] Swagger UI loads successfully
- [ ] Containers running: `docker ps` shows usm-autoimmune-api and usm-autoimmune-postgres
- [ ] Admin credentials ready: `admin` / `admin123`
- [ ] Test datasets prepared: SLE (110 patients), Sjogren (82 patients)

### Browser Setup
- [ ] Open Chrome/Firefox
- [ ] Navigate to `http://172.24.175.24:8000/docs`
- [ ] Bookmark for quick access
- [ ] Zoom level comfortable for audience

### Backup Plan
- [ ] Have cURL commands ready if Swagger fails
- [ ] Screenshots of expected responses prepared
- [ ] PDF documentation available for offline reference

---

## Demo Script

### Part 1: Introduction & Authentication (5 minutes)

**What to Say:**
> "Welcome! Today I'll demonstrate our Autoimmune Disease ML Platform backend. This platform provides secure data ingestion, flexible storage, and powerful query capabilities for clinical research. All patient data is automatically anonymized for NMRR compliance."

**Actions:**

#### 1.1 Show Swagger UI Overview
- **URL:** `http://172.24.175.24:8000/docs`
- Point out sections:
  - **Authentication** - Login and security
  - **Upload** - Data import
  - **Patients** - Query endpoints
  - **Admin** - Test catalog management
  - **Health** - System monitoring

#### 1.2 Login and Authorize
1. Expand `POST /api/v1/auth/login`
2. Click "Try it out"
3. Enter credentials:
   ```json
   {
     "username": "admin",
     "password": "admin123"
   }
   ```
4. Click "Execute"
5. **Show response:**
   ```json
   {
     "access_token": "eyJhbGci...",
     "token_type": "bearer",
     "expires_in": 43200
   }
   ```
6. **Copy token** (highlight and Ctrl+C)
7. Click **"Authorize"** button (🔓 at top right)
8. Paste token: `Bearer <paste token here>`
9. Click "Authorize" → "Close"
10. **Point out:** Lock icon now closed (🔒) - we're authenticated!

**Key Message:**
> "JWT authentication ensures only authorized users can access patient data. Tokens expire after 12 hours for security."

---

### Part 2: Data Import Pipeline (10 minutes)

**What to Say:**
> "Let's import real SLE patient data. Our system handles the entire ETL process: validation, column mapping, anonymization, and storage. Watch how we transform raw Excel data into a secure, queryable database."

#### 2.1 Show Upload Endpoint
1. Scroll to **Upload** section
2. Expand `POST /api/v1/upload/import`
3. Click "Try it out"

#### 2.2 Upload SLE Dataset
1. Click **"Choose File"**
2. Select `sle_patients.xlsx` (110 patients, 61 columns)
3. Fill in parameters:
   - `disease_name`: **SLE**
   - `icd10_code`: **M32.9**
   - `description`: **Initial SLE cohort for demo**
4. Click **"Execute"**
5. **Wait for processing** (5-10 seconds)

#### 2.3 Show Import Results
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

**Highlight:**
- ✅ **109/110 patients imported** (99% success rate)
- ✅ **4,907 lab results** processed
- ✅ **1 error logged** (row 59, invalid date) - per-patient error handling
- ✅ **Audit trail created** (audit_id: 15)

**Key Message:**
> "Our per-patient error handling ensures that if one row fails, the other 109 patients are still imported successfully. All errors are logged for review and re-import."

#### 2.4 Show What Happened Behind the Scenes
**Explain the pipeline:**

1. **FileParser** validated the Excel file
   - Checked format, encoding
   - Detected 110 rows, 61 columns
   - Preview generated

2. **ColumnMapper** matched columns to lab tests
   - Fuzzy matched "WBC" → `wbc`
   - Fuzzy matched "CRP" → `crp`
   - Auto-created new tests for unmapped columns

3. **PatientAnonymizer** protected patient privacy
   - Generated: `USMA-2026-0001` to `USMA-2026-0109`
   - Hashed: Names, ICs, phone numbers (SHA-256)
   - Converted: Age 35 → "30-39" age range

4. **DataTransformer** processed lab values
   - Parsed: "6.5" → numeric 6.5
   - Parsed: "Positive" → text "Positive"
   - Detected abnormal: CRP 15 → High (reference <5)

5. **BatchImporter** saved to database
   - Started transaction
   - Inserted 109 patients
   - Created 4,907 lab result records
   - Committed successfully

**Key Message:**
> "All of this happens automatically in seconds. No manual data cleaning, no spreadsheet juggling. Just upload and go."

---

### Part 3: Query Capabilities (15 minutes)

**What to Say:**
> "Now let's explore the imported data. Our query API provides powerful filtering, searching, and statistical analysis capabilities."

#### 3.1 Search All Patients
1. Scroll to **Patient Data** section
2. Expand `GET /api/v1/patients/`
3. Click "Try it out"
4. Set `limit`: **10** (show first 10)
5. Click "Execute"

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
          "diagnosis_date": "2025-01-15"
        }
      ]
    }
  ],
  "total": 52,
  "limit": 10,
  "offset": 0
}
```

**Highlight:**
- **Anonymous ID:** `USMA-2026-0059` (no real names)
- **Age Range:** "30-39" (not exact age)
- **Total:** 52 patients in system

**Key Message:**
> "Notice all identifying information is removed. We only see anonymous IDs and age ranges. This is NMRR compliant from day one."

#### 3.2 Filter by Disease and Demographics
**Scenario:** Find female SLE patients aged 25-45

1. Scroll up to `GET /api/v1/patients/`
2. Click "Try it out" again
3. Fill in filters:
   - `disease_name`: **sle**
   - `gender`: **f**
   - `age_min`: **25**
   - `age_max`: **45**
   - `limit`: **20**
4. Click "Execute"

**Show results:** Filtered list of matching patients

**Key Message:**
> "Powerful filtering for cohort selection. Perfect for research studies targeting specific demographics."

#### 3.3 Get Patient Summary
**Scenario:** Get overview statistics for a specific patient

1. Find `GET /api/v1/patients/{patient_id}/summary`
2. Click "Try it out"
3. Enter `patient_id`: **171** (or any ID from previous results)
4. Click "Execute"

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

**Highlight:**
- **45 lab results** tracked
- **18 abnormal** (40% abnormal rate)
- **12 unique tests** performed
- **Timeline:** 1 year of data (Feb 2025 - Mar 2026)

**Key Message:**
> "Quick patient overview - perfect for clinical decision support. See abnormality rate at a glance."

#### 3.4 View Lab Results
**Scenario:** See all lab tests for a patient

1. Find `GET /api/v1/patients/{patient_id}/labs`
2. Click "Try it out"
3. Enter `patient_id`: **171**
4. Click "Execute"

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
  ]
}
```

**Highlight:**
- **Test details:** Code, name, category, date
- **Values:** Both numeric and text supported
- **Abnormal detection:** Automatic flagging (H = High, L = Low)
- **Units:** Standardized units stored

#### 3.5 Track Lab Trends Over Time
**Scenario:** Monitor CRP levels over time (treatment response)

1. Find `GET /api/v1/patients/{patient_id}/labs/trends`
2. Click "Try it out"
3. Enter:
   - `patient_id`: **171**
   - `test_code`: **crp**
   - `date_from`: **2026-01-01**
4. Click "Execute"

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

**Visualize on whiteboard:**
```
CRP (mg/L)
16 |                    •
14 |                    
12 |             •      
10 |                    
 8 |      •             
   +--------------------
   Jan    Feb    Mar
```

**Key Message:**
> "Time-series tracking for treatment monitoring. In this case, CRP is rising - might indicate disease flare or treatment failure. Perfect for longitudinal studies."

#### 3.6 Get Population Statistics
**Scenario:** Calculate statistics across all patients

1. Find `GET /api/v1/patients/tests/{test_code}/statistics`
2. Click "Try it out"
3. Enter `test_code`: **wbc**
4. Click "Execute"

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
    "normal": {"min": 4.0, "max": 11.0}
  }
}
```

**Highlight:**
- **Mean WBC:** 5.73 (within normal 4-11)
- **Range:** 1.23 to 26.64 (captures both leukopenia and leukocytosis)
- **Abnormal rate:** 35.29% (18 out of 51)
- **Sample size:** 51 results

**Key Message:**
> "Population-level statistics for research papers. Calculate mean, median, standard deviation automatically. No Excel pivot tables needed!"

---

### Part 4: Multi-Disease Support (5 minutes)

**What to Say:**
> "Our flexible architecture supports unlimited diseases - no schema changes needed. Let's import a Sjogren dataset to demonstrate."

#### 4.1 Import Sjogren Dataset
1. Scroll back to `POST /api/v1/upload/import`
2. Click "Try it out"
3. Upload `sjogren_patients.xlsx`
4. Fill in:
   - `disease_name`: **Sjogren**
   - `icd10_code`: **M35.0**
5. Click "Execute"

**Expected Result:**
```json
{
  "message": "Import completed",
  "results": {
    "successful_patients": 82,
    "total_lab_results": 3428
  }
}
```

#### 4.2 Query by Disease
**Show filtering works:**

1. Go to `GET /api/v1/patients/`
2. Filter by `disease_name`: **sjogren**
3. **Result:** Only Sjogren patients shown

**Then change to:**
4. Filter by `disease_name`: **sle**
5. **Result:** Only SLE patients shown

**Key Message:**
> "Same database, same tables, multiple diseases. No schema changes, no code changes. Just import and query."

#### 4.3 Compare Statistics Across Diseases
**Scenario:** Compare CRP levels in SLE vs Sjogren

1. `GET /api/v1/patients/tests/crp/statistics?disease_name=sle`
   - **SLE CRP mean:** X mg/L

2. `GET /api/v1/patients/tests/crp/statistics?disease_name=sjogren`
   - **Sjogren CRP mean:** Y mg/L

**Key Message:**
> "Cross-disease comparisons for research. Which disease has higher inflammation? Answered in seconds."

---

### Part 5: Admin Features (5 minutes)

**What to Say:**
> "Let's look at backend management - test catalog, approval workflows, and audit trails."

#### 5.1 View Lab Test Catalog
1. Scroll to **Admin** section
2. Expand `GET /api/v1/admin/tests/`
3. Click "Try it out"
4. Set `include_inactive`: **false**
5. Click "Execute"

**Show response:**
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
      "is_active": true
    },
    ...
  ],
  "total": 56
}
```

**Highlight:**
- **56 lab tests** in catalog
- **12 categories** (Hematology, Inflammation, Immune_Cells, etc.)
- **Data types:** Numeric, qualitative, mixed

#### 5.2 View Test Categories
1. Expand `GET /api/v1/admin/tests/categories`
2. Click "Execute"

**Show categories:**
- Hematology (5 tests)
- Inflammation (3 tests)
- Complement (2 tests)
- Immunoglobulin (4 tests)
- Autoantibody (23 tests)
- etc.

#### 5.3 Get Test Statistics (Admin View)
1. Expand `GET /api/v1/admin/tests/statistics`
2. Click "Execute"

**Response:**
```json
{
  "total_tests": 56,
  "active_tests": 54,
  "pending_approval": 2,
  "categories": 12,
  "most_used_tests": [
    {"test_code": "wbc", "result_count": 51},
    {"test_code": "crp", "result_count": 48}
  ]
}
```

**Key Message:**
> "Admin dashboard shows system health. Which tests are most common? How many pending approval?"

#### 5.4 View Upload History
1. Go back to **Upload** section
2. Expand `GET /api/v1/upload/files`
3. Click "Execute"

**Show upload history:**
```json
{
  "files": [
    {
      "file_id": 5,
      "original_filename": "sle_patients.xlsx",
      "uploaded_at": "2026-03-16T12:00:00",
      "disease_name": "SLE",
      "import_status": "completed",
      "successful_rows": 109
    },
    {
      "file_id": 6,
      "original_filename": "sjogren_patients.xlsx",
      "uploaded_at": "2026-03-16T12:15:00",
      "disease_name": "Sjogren",
      "import_status": "completed",
      "successful_rows": 82
    }
  ]
}
```

**Key Message:**
> "Complete audit trail. When was data imported? By whom? What was the success rate? All tracked automatically."

---

### Part 6: Q&A and Next Steps (5 minutes)

**Invite Questions:**
> "That's the complete backend demo. Let me open the floor for questions."

**Common Questions & Answers:**

**Q: How do we handle new lab tests not in the catalog?**  
A: Auto-created during import with "pending approval" status. Admins review and approve via API.

**Q: Can we export data?**  
A: Currently via API only. We can add CSV/Excel export endpoints if needed.

**Q: What about data from multiple hospitals?**  
A: System ready - just import each hospital's data with different `uploaded_by` user.

**Q: How do we delete a patient?**  
A: Contact admin. We have soft-delete (mark inactive) to preserve audit trail.

**Q: Performance with 10,000 patients?**  
A: Tested up to 500 patients - performs well. Can scale to 100K+ with indexing optimizations.

**Q: Can we integrate with our existing EMR?**  
A: Yes! API can accept data from any source. We can build EMR connectors (HL7/FHIR).

**Q: What about unstructured data (PDFs, images)?**  
A: Phase 2 feature. We have basic PDF text extraction, full OCR coming soon.

---

## Post-Demo Actions

### 1. Gather Requirements
**Questions to ask USM:**

- **Data Formats:** What formats will you provide? (CSV, Excel, database exports?)
- **Lab Tests:** Do you have a standard catalog we should use?
- **Data Dictionary:** Can you share field definitions and expected columns?
- **Volume:** How many patients initially? Growth rate?
- **Frequency:** Real-time, daily, weekly, monthly imports?
- **Users:** Who will use this system? Technical skill level?
- **Multi-center:** Data from multiple hospitals?
- **Disease Scope:** Which diseases beyond SLE and Sjogren?
- **ML Goals:** What should models predict? (Outcomes, flare risk, treatment response?)

### 2. Provide Documentation
**Share these files:**
- [ ] INFRASTRUCTURE.md - Setup details
- [ ] DATA_PIPELINE.md - Import architecture
- [ ] API_GUIDE.md - Complete API reference
- [ ] ARCHITECTURE.md - System overview
- [ ] Demo recording (if recorded)
- [ ] Swagger JSON export

### 3. Schedule Follow-up
- [ ] Next meeting: Review USM's questions and requirements
- [ ] Timeline discussion: When do they need Phase 2 features?
- [ ] Data sharing agreement: When can they provide real datasets?
- [ ] Access setup: Create user accounts for USM team

### 4. Action Items
**For Your Team:**
- [ ] Review feedback and questions
- [ ] Prioritize feature requests
- [ ] Plan Sprint 2 (ML features)
- [ ] Prepare cost estimate for Phase 2

**For USM:**
- [ ] Review documentation
- [ ] Provide sample datasets
- [ ] Confirm disease list and requirements
- [ ] Identify key users for training

---

## Troubleshooting During Demo

### Issue: Swagger UI not loading
**Solution:** Check containers running: `docker ps`  
**Backup:** Use cURL examples from API_GUIDE.md

### Issue: Import fails
**Solution:** Check file format matches expected structure  
**Backup:** Have pre-imported data ready, show query endpoints only

### Issue: No data returned from queries
**Solution:** Check patient IDs exist: `GET /api/v1/patients/`  
**Backup:** Import test dataset live during demo

### Issue: Authentication fails
**Solution:** Restart API container: `docker restart usm-autoimmune-api`  
**Backup:** Use pre-generated token in documentation

### Issue: Slow response times
**Solution:** Reduce `limit` parameter to 10  
**Backup:** Show response JSON from screenshots

---

## Demo Tips

### Before Demo
- **Test run:** Do a complete dry run 1 hour before
- **Clear data:** Reset database to clean state (optional)
- **Prepare files:** Have datasets ready on desktop
- **Battery check:** If laptop, ensure plugged in
- **Network:** Test connection stability

### During Demo
- **Speak slowly:** Give audience time to process
- **Pause for questions:** After each major section
- **Point to screen:** Use mouse to highlight responses
- **Scroll slowly:** Don't rush through JSON responses
- **Explain errors:** If something fails, explain why (shows robustness)

### After Demo
- **Summarize:** Recap what was shown
- **Highlight benefits:** Stress security, flexibility, scalability
- **Next steps:** Clear action items and timeline
- **Thank audience:** Express enthusiasm for collaboration

---

## Demo Success Metrics

**Successful demo if:**
- ✅ Successfully import at least 1 dataset
- ✅ Show patient query filtering
- ✅ Demonstrate multi-disease support
- ✅ Display time-series trends
- ✅ Calculate population statistics
- ✅ Answer all major questions
- ✅ USM expresses interest in moving forward

**Extra credit:**
- 🌟 Import 2nd disease live during demo
- 🌟 Show cross-disease comparison
- 🌟 Demonstrate error handling gracefully
- 🌟 Impress with query speed (<1 second)

---

## Follow-up Email Template

```
Subject: USM Autoimmune ML Platform - Demo Follow-up

Hi [USM Contact],

Thank you for attending the backend demo today! Here's a summary:

✅ What We Demonstrated:
• Secure data import (SLE: 109 patients, 4,907 lab results in 5 seconds)
• Patient anonymization (NMRR compliant)
• Flexible query API (40+ endpoints)
• Multi-disease support (SLE + Sjogren)
• Population statistics and time-series analysis

📋 Documentation Shared:
• Complete API reference (API_GUIDE.md)
• System architecture (ARCHITECTURE.md)
• Data pipeline details (DATA_PIPELINE.md)
• Swagger UI: http://172.24.175.24:8000/docs

❓ Questions to Discuss:
• Data formats and column structure
• Expected patient volume and growth
• Disease scope beyond SLE/Sjogren
• ML prediction goals
• Timeline for Phase 2 (model training)

📅 Next Steps:
• [ ] USM: Review documentation and provide feedback
• [ ] USM: Share sample datasets (if available)
• [ ] Us: Schedule follow-up meeting (propose dates)
• [ ] Both: Define Phase 2 requirements

Looking forward to your feedback!

Best regards,
[Your Name]
```

---

## Appendix: Quick Reference

### Login Credentials
- Username: `admin`
- Password: `admin123`

### Key URLs
- Swagger UI: `http://172.24.175.24:8000/docs`
- ReDoc: `http://172.24.175.24:8000/redoc`
- Health Check: `http://172.24.175.24:8000/health`

### Docker Commands
```bash
# Check containers
docker ps

# Restart API
docker restart usm-autoimmune-api

# View logs
docker logs --tail 50 usm-autoimmune-api

# Database access
docker exec -it usm-autoimmune-postgres psql -U usm_admin -d usm_autoimmune_registry
```

### Test Patient IDs
- Patient 1: Test patient (1 lab result)
- Patient 171-180: Real SLE patients (40+ lab results each)

### Common Test Codes
- `wbc` - White Blood Cell count
- `crp` - C-Reactive Protein
- `esr` - Erythrocyte Sedimentation Rate
- `c3`, `c4` - Complement levels
- `ana` - Antinuclear Antibody
- `sledai` - SLE Disease Activity Index

---

**Good luck with the demo! 🚀**
