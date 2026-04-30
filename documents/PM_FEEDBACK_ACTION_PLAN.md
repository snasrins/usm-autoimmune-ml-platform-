# 🎯 PM Feedback - Immediate Action Plan
**Date:** March 20, 2026  
**Priority:** URGENT - Architecture Changes Required  
**Based on:** PM Meeting Feedback (March 20, 2026)

---

## 📋 **What Changed?**

### **🚨 Critical Issues PM Identified:**

1. ❌ **Database schema too rigid** - can't handle new diseases/data types
2. ❌ **OCR in wrong place** - should be INSIDE unstructured pipeline
3. ❌ **No human validation** - system too automatic
4. ❌ **Missing security/RBAC**
5. ❌ **No audit trail**

### **✅ What PM Wants:**

> "Platform is a **framework** (not automation). User controls execution. System executes only after approval."

---

## 🔥 **Your Tasks (PM Assigned)**

### **Task 1: Design Flexible Database Schema** ✅ DONE

**File Created:** [`init-db/02-flexible-schema.sql`](../init-db/02-flexible-schema.sql)

**What It Has:**
- ✅ Fact tables (patient_visits, lab_results, diagnoses, prescriptions)
- ✅ Dimension tables (patients, diseases, hospitals, lab_tests, medications, time)
- ✅ Metadata tables (datasets, columns registry)
- ✅ Audit trail (full transparency)
- ✅ Validation queue (human checkpoints)
- ✅ Flexible design (new diseases/tests can be added without schema change)

**Key Features:**
```sql
-- OLD (Rigid): Need new table for each disease
CREATE TABLE sle_patients (...);  ❌

-- NEW (Flexible): Just insert row
INSERT INTO dim_diseases (disease_name) VALUES ('New Disease');  ✅
```

---

### **Task 2: Revise System Architecture** ✅ DONE

**File Created:** [`documents/ARCHITECTURE_REVISION.md`](../documents/ARCHITECTURE_REVISION.md)

**Major Changes:**

**OCR Pipeline (Fixed):**
```
OLD: Unstructured Data → Storage → Data Prep → [OCR Separate]  ❌

NEW: Unstructured Data → [OCR + NER + Cleaning INSIDE] → Storage  ✅
```

**Human Validation (Added):**
```
User uploads → Auto extract columns → USER REVIEWS
→ OCR processing → USER REVIEWS OUTPUT
→ Select cleaning operations → USER CONFIRMS
→ Feature extraction → USER VALIDATES
→ System proceeds ONLY after approval
```

**4 Validation Checkpoints:**
1. ✅ Column mapping review
2. ✅ OCR output approval
3. ✅ Cleaning operations selection
4. ✅ Extracted features confirmation

---

### **Task 3: Validate Full Pipeline Flow** ⏳ TO DO

**What PM Wants:**
> "Test yourself with sample data. Check: upload, validate, preview, versioning, audit trail works."

**Steps to Test:**
1. Upload SLE CSV file
2. System extracts columns automatically
3. User reviews column mapping
4. User confirms
5. Check `metadata_datasets` table (versioning)
6. Check `metadata_columns` table (column registry)
7. Check `audit_trail` (logs actions)
8. Upload PDF (unstructured)
9. System runs OCR → User reviews output
10. User selects cleaning operations
11. System executes → Check audit trail

---

### **Task 4: Ensure System Works End-to-End** ⏳ TO DO

**Checklist:**
- [ ] Upload works
- [ ] Column extraction automatic
- [ ] Validation queue functional
- [ ] Preview available
- [ ] Versioning tracks changes
- [ ] Audit trail logs everything
- [ ] Processing only after user approval

---

## ⚡ **What You Need to Do NOW**

### **Step 1: Deploy New Schema (30 minutes)**

Even with slow PuTTY, this MUST be done:

```bash
# In PuTTY (paste slowly if needed)
cd /home/mtuser2/usm-autoimmune-ml-platform

# Backup current database
docker exec usm-autoimmune-postgres pg_dump -U usm_db_admin usm_autoimmune_registry > backup_20260320.sql

# Apply new schema
docker exec -i usm-autoimmune-postgres psql -U usm_db_admin -d usm_autoimmune_registry < init-db/02-flexible-schema.sql

# Verify
docker exec usm-autoimmune-postgres psql -U usm_db_admin -d usm_autoimmune_registry -c "\dt"
```

**Expected Output:**
```
                List of relations
 Schema |         Name          | Type  |     Owner      
--------+-----------------------+-------+----------------
 public | dim_patients          | table | usm_db_admin
 public | dim_diseases          | table | usm_db_admin
 public | dim_lab_tests         | table | usm_db_admin
 public | fact_patient_visits   | table | usm_db_admin
 public | fact_lab_results      | table | usm_db_admin
 public | metadata_datasets     | table | usm_db_admin
 public | audit_trail           | table | usm_db_admin
 public | validation_queue      | table | usm_db_admin
 ...
```

---

### **Step 2: Create ValidationService (Tomorrow)**

**File to Create:** `app/services/validation_service.py`

```python
class ValidationService:
    """Human-in-the-loop validation framework"""
    
    def submit_for_review(self, dataset_id, stage, data):
        """
        Submit data for human review
        
        Stages:
        - "column_mapping": User reviews detected columns
        - "ocr_output": User reviews OCR extracted text
        - "cleaning_selection": User selects cleaning operations
        - "feature_validation": User confirms extracted features
        """
        pass
    
    def get_pending_validations(self, user_id):
        """Get items awaiting user's review"""
        pass
    
    def approve(self, validation_id, user_id, comments):
        """User approves and system proceeds"""
        pass
    
    def reject(self, validation_id, user_id, reason):
        """User rejects and system rolls back"""
        pass
```

---

### **Step 3: Create AuditService (Tomorrow)**

**File to Create:** `app/services/audit_service.py`

```python
class AuditService:
    """Complete audit trail for governance"""
    
    def log_action(self, user_id, action, target_entity, target_id, changes):
        """
        Log every user action
        
        Examples:
        - User uploads dataset
        - User approves OCR output
        - User executes cleaning
        - User validates features
        """
        pass
    
    def get_audit_trail(self, target_id):
        """Get complete history for entity"""
        pass
```

---

### **Step 4: Update API Endpoints (This Week)**

**New Endpoints Needed:**

```python
# app/routers/validation.py

@router.post("/validate/columns")
async def submit_column_mapping(dataset_id, mapping):
    """User reviews and confirms column mapping"""
    pass

@router.get("/validate/pending")
async def get_pending_validations(user_id):
    """Get items awaiting user review"""
    pass

@router.post("/validate/{validation_id}/approve")
async def approve_validation(validation_id, comments):
    """User approves checkpoint"""
    pass

@router.post("/validate/{validation_id}/reject")
async def reject_validation(validation_id, reason):
    """User rejects and stops pipeline"""
    pass

@router.get("/audit/{entity_id}")
async def get_audit_trail(entity_id):
    """View complete audit trail"""
    pass
```

---

### **Step 5: Test with Sample Data (This Week)**

**Test Scenario:**

1. **Upload CSV** (SLE patient data)
   - Check `metadata_datasets` created
   - Check `metadata_columns` extracted automatically
   - Check `audit_trail` logs upload

2. **Submit for Column Mapping Review**
   - Check `validation_queue` has pending item
   - User reviews in Swagger UI
   - User approves
   - Check `audit_trail` logs approval

3. **Upload PDF** (lab report)
   - System runs OCR
   - Submits OCR output for review
   - User reviews extracted text
   - User approves/rejects
   - Check audit trail

4. **Data Cleaning**
   - System shows cleaning options
   - User selects operations (checkboxes)
   - User clicks "Execute"
   - System cleans data
   - Check audit trail

5. **Feature Extraction**
   - System extracts entities (Name, Diagnosis, Meds)
   - Submits for user validation
   - User confirms
   - System inserts into fact tables
   - Check audit trail

---

## 📊 **Files Modified/Created**

### **✅ Created:**
1. `documents/ARCHITECTURE_REVISION.md` - Complete architecture redesign
2. `init-db/02-flexible-schema.sql` - New flexible database schema
3. `documents/PM_FEEDBACK_ACTION_PLAN.md` - This file

### **✅ Fixed:**
1. `requirements.txt` - Fixed typo (`accelerator` → `accelerate`)

### **⏳ To Create:**
1. `app/services/validation_service.py` - Human validation checkpoints
2. `app/services/audit_service.py` - Audit trail logging
3. `app/routers/validation.py` - Validation API endpoints
4. `app/routers/audit.py` - Audit trail API endpoints

---

## 🎯 **Timeline**

### **Today (March 20):**
- [x] Review PM feedback
- [x] Design flexible schema
- [x] Revise architecture
- [ ] Deploy new schema to database

### **Tomorrow (March 21):**
- [ ] Create ValidationService
- [ ] Create AuditService
- [ ] Add validation API endpoints
- [ ] Test column extraction and validation

### **This Week (March 22-26):**
- [ ] Test OCR → Validation workflow
- [ ] Test cleaning → User selection workflow
- [ ] Test feature extraction → User approval
- [ ] Verify audit trail logging
- [ ] Test end-to-end with sample data

### **Next Week (March 27-29):**
- [ ] Add RBAC (role-based access control)
- [ ] Add security layer (zero-trust)
- [ ] Prepare presentation for PM
- [ ] Demo full workflow

---

## 🔐 **Security Features (To Add)**

### **RBAC Roles:**

| Role | Upload | Validate | Execute | Train Models | View Audit |
|------|--------|----------|---------|--------------|------------|
| **Data Engineer** (You) | ✅ | ✅ | ✅ | ❌ | ✅ |
| **Clinician** (USM) | ✅ | ✅ | ❌ | ❌ | ❌ |
| **ML Engineer** (Iznie) | ❌ | ❌ | ❌ | ✅ | ❌ |
| **Admin** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Auditor** | ❌ | ❌ | ❌ | ❌ | ✅ |

### **Implementation:**

```python
# app/models/user.py
class UserRole(str, Enum):
    DATA_ENGINEER = "data_engineer"
    CLINICIAN = "clinician"
    ML_ENGINEER = "ml_engineer"
    ADMIN = "admin"
    AUDITOR = "auditor"

# Middleware checks role before allowing action
@router.post("/validate/approve")
@require_role([UserRole.DATA_ENGINEER, UserRole.CLINICIAN, UserRole.ADMIN])
async def approve_validation(...):
    pass
```

---

## 📈 **PM Meeting Preparation**

**What to Show PM:**

1. ✅ **Flexible schema diagram**
   - Show how new diseases can be added
   - Show fact/dimension tables
   - Explain Snowflake-style design

2. ✅ **Revised architecture**
   - User-controlled framework
   - 4 validation checkpoints
   - Audit trail transparency

3. ⏳ **Working demo**
   - Upload CSV → Auto column extraction
   - User reviews and approves
   - Show audit trail
   - Upload PDF → OCR → User reviews output

4. ⏳ **End-to-end test results**
   - Upload → Validate → Process → Audit
   - Show versioning works
   - Show metadata storage

---

## 🚨 **Network Issue (Deprioritized)**

**Your PuTTY/WinSCP slowness can wait.**  
**This architecture revision is MORE URGENT.**

**Quick Fix for Network:**
- Use WinSCP Preferences → Connection → Timeout: 120 seconds
- Use WinSCP Preferences → Transfer → Endurance → All options enabled
- Or just paste commands directly in PuTTY (slower but works)

**Qwen Models Installation:**
- Can be done AFTER schema is deployed
- Not blocking for PM meeting
- Models are nice-to-have, schema is MUST-have

---

## ✅ **Summary**

**PM's Key Message:**
> "This is a **framework**, not automation. User controls execution at every step."

**What You Fixed:**
1. ✅ Flexible schema (can add new diseases/tests without breaking)
2. ✅ Revised architecture (user-controlled workflow)
3. ✅ Human validation checkpoints (4 stages)
4. ✅ Audit trail system (full transparency)
5. ✅ Versioning support (track changes)

**What's Next:**
1. Deploy new schema NOW (even if PuTTY is slow)
2. Build ValidationService tomorrow
3. Test end-to-end this week
4. Present to PM next week

---

**🎯 Your immediate command to run in PuTTY:**

```bash
cd /home/mtuser2/usm-autoimmune-ml-platform

# Upload the new schema file via WinSCP first, or create it manually
# Then apply:
docker exec -i usm-autoimmune-postgres psql -U usm_db_admin -d usm_autoimmune_registry < init-db/02-flexible-schema.sql

# Verify tables created
docker exec usm-autoimmune-postgres psql -U usm_db_admin -d usm_autoimmune_registry -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"
```

**Priority: Schema deployment > Qwen installation > Network troubleshooting** 🚀
