# Dynamic Category Management System
## ZERO Hardcoding - Database-Driven Diagnosis Categorization

---

## 🎯 Problem Solved

**BEFORE (Hardcoded)**:
```python
# BAD: Hardcoded categories in SQL
UPDATE flexible_dataset_wide SET data = jsonb_set(
    data, '{clinical,diagnosis_category}',
    to_jsonb(CASE 
        WHEN data->'clinical'->>'diagnosis' LIKE '%lupus nephritis%' THEN 'SLE_with_LN'
        WHEN data->'clinical'->>'diagnosis' LIKE '%antiphospholipid%' THEN 'SLE_with_APL'
        ...
    END)
);
```
❌ Cannot add new categories without code changes  
❌ Requires developer intervention for category updates  
❌ No audit trail  
❌ Difficult to maintain  

**AFTER (Dynamic Lookup)**:
```sql
-- Database-driven - admins can manage via API/UI
SELECT get_diagnosis_category('Systemic lupus erythematosus with lupus nephritis');
-- Returns: 'SLE_with_LN' (from lookup table)
```
✅ Add categories via admin API (NO code changes)  
✅ Pattern matching (exact, contains, regex)  
✅ Priority-based conflict resolution  
✅ Full audit trail  
✅ Testable via `/categories/test-categorization` endpoint  

---

## 📁 Files Created

### **Database Layer**
1. **init-db/04-category-management.sql**
   - `dim_disease_categories` - Category definitions table
   - `diagnosis_category_mappings` - Diagnosis → Category mappings
   - `category_audit_log` - Change tracking
   - `get_diagnosis_category()` - SQL function for lookups

### **Models**
2. **app/models/disease_category.py**
   - `DiseaseCategory` - ORM model for categories
   - `DiagnosisCategoryMapping` - ORM model for mappings
   - `CategoryAuditLog` - Audit trail model

### **Service Layer**
3. **app/services/category_lookup_service.py**
   - `CategoryLookupService` - Dynamic category lookup
   - `get_category_for_diagnosis()` - Main lookup method
   - `categorize_batch()` - Bulk categorization
   - `validate_category_coverage()` - Test coverage

### **API Endpoints**
4. **app/api/endpoints/category_management.py**
   - `GET /api/v1/categories` - List all categories
   - `POST /api/v1/categories` - Create new category (admin)
   - `PATCH /api/v1/categories/{id}` - Update category (admin)
   - `DELETE /api/v1/categories/{id}` - Delete category (admin)
   - `GET /api/v1/mappings` - List diagnosis mappings
   - `POST /api/v1/mappings` - Create mapping (admin)
   - `POST /api/v1/test-categorization` - Test diagnosis categorization
   - `GET /api/v1/audit-log` - View change history (admin)

### **ETL Integration**
5. **app/services/flexible_import_service.py** (UPDATED)
   - `_auto_categorize_diagnosis()` - Automatic categorization during CSV import
   - Uses `CategoryLookupService` for dynamic lookup
   - NO hardcoded categories!

---

## 🚀 Quick Start

### Step 1: Initialize Database
```bash
# Run the SQL migration (adds tables + seed data)
docker exec -i usm-autoimmune-postgres psql -U postgres -d usm_autoimmune < init-db/04-category-management.sql
```

**Seed Data Includes**:
- 4 SLE categories: `SLE_with_LN`, `SLE_uncomplicated`, `SLE_with_APL`, `SLE_with_ILD`
- 12 diagnosis patterns with priority ranking
- PostgreSQL function for lookups

### Step 2: Test Categorization
```bash
# Test if a diagnosis maps correctly
curl -X POST "http://localhost:8001/api/v1/categories/test-categorization?diagnosis_text=Systemic%20lupus%20erythematosus%20with%20lupus%20nephritis" \
  -H "Authorization: Bearer $TOKEN"
```

**Response**:
```json
{
  "diagnosis_text": "Systemic lupus erythematosus with lupus nephritis",
  "matched_category": "SLE_with_LN",
  "mapping_details": {
    "mapping_id": 1,
    "pattern": "lupus nephritis",
    "match_type": "contains",
    "priority": 100
  }
}
```

### Step 3: Apply to Existing Data
```sql
-- Update existing records in flexible_dataset_wide
UPDATE flexible_dataset_wide
SET data = jsonb_set(
    data, 
    '{clinical,diagnosis_category}', 
    to_jsonb(get_diagnosis_category(data->'clinical'->>'diagnosis'))
)
WHERE data->'clinical'->>'diagnosis' IS NOT NULL;
```

### Step 4: Verify Results
```sql
-- Check category distribution
SELECT 
    data->'clinical'->>'diagnosis_category' AS category,
    COUNT(*) AS count
FROM flexible_dataset_wide
WHERE data->'clinical'->>'diagnosis_category' IS NOT NULL
GROUP BY category
ORDER BY count DESC;
```

---

## 🔧 Admin Operations

### Add New Category
```bash
curl -X POST "http://localhost:8001/api/v1/categories" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "category_name": "SLE_with_CNS",
    "category_code": "sle_cns",
    "category_label": "SLE with CNS Involvement",
    "description": "SLE with central nervous system manifestations",
    "is_active": true
  }'
```

### Add Diagnosis Mapping
```bash
curl -X POST "http://localhost:8001/api/v1/categories/mappings" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "category_id": 5,
    "diagnosis_pattern": "cerebral lupus",
    "match_type": "contains",
    "priority": 95,
    "is_active": true
  }'
```

**Match Types**:
- `exact` - Exact string match (case-insensitive)
- `contains` - Substring search
- `starts_with` - Prefix match
- `regex` - Regular expression (advanced)

**Priority System**:
- Higher priority wins if multiple patterns match
- Range: 0-100
- Example: "lupus nephritis" (100) > "lupus" (10)

### List All Mappings
```bash
curl -X GET "http://localhost:8001/api/v1/categories/mappings?category_id=1" \
  -H "Authorization: Bearer $TOKEN"
```

### View Audit Log
```bash
curl -X GET "http://localhost:8001/api/v1/categories/audit-log" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## 🔀 Automatic ETL Integration

### How It Works

When CSV files are uploaded via `/flexible/preview/upload`:

1. **CSV Parser** reads raw data
2. **Schema Detector** organizes into categories (demographics, lab_results, clinical, etc.)
3. **`_organize_data()`** groups fields
4. **`_auto_categorize_diagnosis()`** 🆕 → Looks up category dynamically
5. **`CategoryLookupService`** queries `diagnosis_category_mappings` table
6. **`diagnosis_category`** field added to `clinical` section automatically

**Code Flow**:
```python
# app/services/flexible_import_service.py
def _organize_data(self, row_data):
    organized = {...}  # Group by categories
    
    # Automatic categorization (NO hardcoding)
    self._auto_categorize_diagnosis(organized)
    
    return organized

def _auto_categorize_diagnosis(self, organized_data):
    diagnosis_text = organized_data['clinical'].get('diagnosis')
    
    lookup_service = CategoryLookupService(self.db)
    category = lookup_service.get_category_for_diagnosis(diagnosis_text)
    
    organized_data['clinical']['diagnosis_category'] = category
    organized_data['clinical']['diagnosis_category_source'] = 'auto_lookup'
```

**Result in Database**:
```json
{
  "clinical": {
    "diagnosis": "Systemic lupus erythematosus with lupus nephritis",
    "diagnosis_category": "SLE_with_LN",
    "diagnosis_category_source": "auto_lookup"
  }
}
```

---

## 📊 Validation & Testing

### Test Coverage for New Dataset
```python
# Use the validation endpoint
import requests

response = requests.post(
    "http://localhost:8001/api/v1/categories/validate-coverage",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "diagnosis_samples": [
            "Systemic lupus erythematosus with lupus nephritis",
            "SLE with antiphospholipid syndrome",
            "Uncomplicated SLE",
            "Rheumatoid arthritis"  # Should return 'Unknown'
        ]
    }
)

print(response.json())
```

**Response**:
```json
{
  "total_samples": 4,
  "categorized": 3,
  "unknown": 1,
  "coverage_rate": 75.0,
  "category_distribution": {
    "SLE_with_LN": 1,
    "SLE_with_APL": 1,
    "SLE_uncomplicated": 1
  },
  "uncategorized_samples": ["Rheumatoid arthritis"]
}
```

### Batch Categorization
```python
from app.services.category_lookup_service import CategoryLookupService

lookup = CategoryLookupService(db)
results = lookup.categorize_batch([
    "Systemic lupus erythematosus with lupus nephritis",
    "SLE with ILD",
    "Lupus with renal involvement"
])

# Returns:
# {
#   "Systemic lupus erythematosus with lupus nephritis": "SLE_with_LN",
#   "SLE with ILD": "SLE_with_ILD",
#   "Lupus with renal involvement": "SLE_with_LN"
# }
```

---

## 🎯 Production Workflow

### For Initial Setup (Current Testing Data)

1. **Deploy SQL migration**:
   ```bash
   docker exec -i usm-autoimmune-postgres psql -U postgres -d usm_autoimmune < init-db/04-category-management.sql
   ```

2. **Update existing data**:
   ```sql
   UPDATE flexible_dataset_wide
   SET data = jsonb_set(
       data, 
       '{clinical,diagnosis_category}', 
       to_jsonb(get_diagnosis_category(data->'clinical'->>'diagnosis'))
   )
   WHERE data->'clinical'->>'diagnosis' IS NOT NULL;
   ```

3. **Verify ML pipeline uses correct target**:
   ```bash
   curl -X POST "http://localhost:8001/api/v1/ml/train/prepare-dataset" \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"target_column": "clinical_diagnosis_category", "test_size": 0.3}'
   ```

### For New Data Upload (n=191 Full Dataset)

1. **Upload CSV** via `/flexible/preview/upload`
2. **Automatic categorization** happens during import (NO manual SQL needed)
3. **Verify** via frontend UI or API:
   ```bash
   curl -X GET "http://localhost:8001/api/v1/flexible/preview?limit=10"
   ```

---

## 🔐 Security & Permissions

| Endpoint | Permission | Purpose |
|----------|------------|---------|
| `GET /categories` | User | View categories |
| `POST /categories` | **Admin Only** | Create category |
| `PATCH /categories/{id}` | **Admin Only** | Update category |
| `DELETE /categories/{id}` | **Admin Only** | Delete category |
| `POST /mappings` | **Admin Only** | Create mapping |
| `POST /test-categorization` | User | Test diagnosis |
| `GET /audit-log` | **Admin Only** | View audit trail |

**Admin Authentication**:
```python
from app.api.deps import get_current_superuser

@router.post("/categories")
async def create_category(
    current_user: User = Depends(get_current_superuser)  # Admin only
):
    ...
```

---

## 📈 Monitoring & Maintenance

### Check Category Usage
```sql
-- See which categories are used most
SELECT 
    data->'clinical'->>'diagnosis_category' AS category,
    COUNT(*) AS usage_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage
FROM flexible_dataset_wide
WHERE data->'clinical'->>'diagnosis_category' IS NOT NULL
GROUP BY category
ORDER BY usage_count DESC;
```

### Find Uncategorized Diagnoses
```sql
-- Diagnoses that returned 'Unknown'
SELECT DISTINCT
    data->'clinical'->>'diagnosis' AS diagnosis
FROM flexible_dataset_wide
WHERE 
    data->'clinical'->>'diagnosis_category' = 'Unknown'
    AND data->'clinical'->>'diagnosis' IS NOT NULL;
```

### Audit Trail Query
```sql
-- Recent category changes
SELECT 
    audit_id,
    table_name,
    action,
    new_data::json->>'category_name' AS category_changed,
    changed_at
FROM category_audit_log
ORDER BY changed_at DESC
LIMIT 20;
```

---

## 🔄 Migration Path for Existing Projects

### If you have hardcoded categories in code:

**Step 1**: Run the SQL migration
```bash
docker exec -i usm-autoimmune-postgres psql -U postgres -d usm_autoimmune < init-db/04-category-management.sql
```

**Step 2**: Populate with existing categories
```python
# Extract from your existing code
existing_categories = {
    "SLE_with_LN": "SLE with Lupus Nephritis",
    "SLE_uncomplicated": "SLE Uncomplicated",
    # ... add all your current categories
}

# Import via API
for code, label in existing_categories.items():
    requests.post(
        "http://localhost:8001/api/v1/categories",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "category_name": code,
            "category_code": code.lower(),
            "category_label": label
        }
    )
```

**Step 3**: Update import service (ALREADY DONE ✅)
- `flexible_import_service.py` now uses `CategoryLookupService`
- Remove any hardcoded CASE statements

**Step 4**: Deploy to production
```bash
# Upload changed files
scp app/services/flexible_import_service.py user@server:/path/
scp app/services/category_lookup_service.py user@server:/path/
scp app/models/disease_category.py user@server:/path/
scp app/api/endpoints/category_management.py user@server:/path/

# Restart backend
docker restart usm-autoimmune-api
```

---

## 🧪 Testing Checklist

- [ ] SQL migration runs successfully
- [ ] Seed data inserted (4 categories, 12 mappings)
- [ ] `get_diagnosis_category()` function works
- [ ] API endpoints accessible at `/api/v1/categories`
- [ ] Test categorization endpoint returns correct matches
- [ ] Existing data updated with categories
- [ ] New CSV upload auto-categorizes diagnoses
- [ ] ML pipeline uses `clinical_diagnosis_category` target
- [ ] Audit log tracks admin changes
- [ ] Only admins can create/modify categories

---

## 🎓 Key Concepts

### Why Dynamic Lookup > Hardcoding?

| Aspect | Hardcoded | Dynamic Lookup |
|--------|-----------|----------------|
| **Add Category** | Requires code change, deploy, restart | API call, instant |
| **Update Pattern** | Edit SQL, redeploy | Admin UI update |
| **Audit Trail** | None | Full change history |
| **Testing** | Manual SQL queries | `/test-categorization` endpoint |
| **Maintainability** | Developer-dependent | Admin-friendly |
| **Scalability** | Limited by code complexity | Unlimited categories |

### Pattern Matching Strategy

1. **Exact Match** - Fast, deterministic
   - `"SLE"` matches `"SLE"` only

2. **Contains** - Flexible, substring search
   - `"lupus nephritis"` matches `"Systemic lupus erythematosus with lupus nephritis"`

3. **Starts With** - Prefix matching
   - `"Systemic lupus"` matches `"Systemic lupus erythematosus..."`

4. **Regex** - Advanced pattern matching
   - `"SLE.*nephritis"` matches `"SLE with lupus nephritis"`

**Best Practice**: Use priority system to resolve conflicts
- High priority (90-100): Specific diagnoses (e.g., "lupus nephritis")
- Medium priority (50-89): Specific subtypes (e.g., "antiphospholipid syndrome")
- Low priority (1-49): Catch-all patterns (e.g., "SLE")

---

## 📞 Support & Next Steps

### Troubleshooting

**Issue**: Categories not appearing
```bash
# Check seed data installed
docker exec -i usm-autoimmune-postgres psql -U postgres -d usm_autoimmune -c "SELECT * FROM dim_disease_categories;"
```

**Issue**: Categorization returns 'Unknown'
```bash
# Test the pattern matching
curl -X POST "http://localhost:8001/api/v1/categories/test-categorization?diagnosis_text=YOUR_DIAGNOSIS_HERE"
```

**Issue**: API 404 errors
```bash
# Verify router registered
docker logs usm-autoimmune-api | grep "category_management"
```

### Future Enhancements

- [ ] Frontend UI for category management (admin panel)
- [ ] Bulk import categories from CSV
- [ ] Machine learning-based category suggestions
- [ ] Multi-language diagnosis support
- [ ] Category hierarchy (parent-child relationships)
- [ ] Automatic pattern learning from historical data

---

## ✅ Summary

You now have a **ZERO-HARDCODING** category management system:

1. **Database Tables** - Store categories and mappings
2. **API Endpoints** - Admin can manage via Swagger UI or frontend
3. **Service Layer** - Dynamic lookup with pattern matching
4. **ETL Integration** - Automatic categorization during CSV import
5. **Audit Trail** - Track all changes
6. **Testing Tools** - Validate patterns before deployment

**NO MORE CODE CHANGES FOR CATEGORIES!** 🎉
