# Database Migration Guide

## 📋 Migration: Create Flexible Schema

**Date:** March 16, 2026  
**Version:** 001  
**Description:** Create flexible database schema supporting multiple autoimmune diseases

---

## 🎯 What This Migration Does

Creates 8 new/updated tables:

1. **patients** - Updated to flexible anonymous schema
2. **diagnoses** - Track multiple diseases per patient
3. **lab_test_definitions** - Catalog of all lab tests (167+ tests)
4. **lab_results_flexible** - Flexible lab results storage
5. **lab_results_batch** - Batch/panel results (JSONB)
6. **disease_specific_data** - Pure JSONB for unknown data types
7. **uploaded_files** - File upload tracking
8. **data_ingestion_audit** - Complete audit trail

---

## 🚀 Run Migration

### **Option 1: Python Script (Recommended)**

```bash
# On server
cd ~/usm-autoimmune-ml-platform

# Run migration
sudo docker exec usm-autoimmune-api python scripts/create_flexible_schema.py create
```

### **Option 2: Direct SQL**

```bash
# On server
cd ~/usm-autoimmune-ml-platform

# Run SQL migration
sudo docker exec -i usm-autoimmune-postgres psql -U usm_db_admin -d usm_autoimmune_registry < scripts/migrations/001_create_flexible_schema.sql
```

### **Option 3: Manual via psql**

```bash
# Connect to database
sudo docker exec -it usm-autoimmune-postgres psql -U usm_db_admin -d usm_autoimmune_registry

# Copy-paste SQL from 001_create_flexible_schema.sql
\i /path/to/001_create_flexible_schema.sql
```

---

## ✅ Verify Migration

```bash
# Check tables exist
sudo docker exec usm-autoimmune-postgres psql -U usm_db_admin -d usm_autoimmune_registry -c "\dt"

# Check patient table structure
sudo docker exec usm-autoimmune-postgres psql -U usm_db_admin -d usm_autoimmune_registry -c "\d patients"

# Check lab_test_definitions
sudo docker exec usm-autoimmune-postgres psql -U usm_db_admin -d usm_autoimmune_registry -c "SELECT COUNT(*) FROM lab_test_definitions;"
```

Expected output:
```
 patients
 users
 diagnoses
 lab_test_definitions
 lab_results_flexible
 lab_results_batch
 disease_specific_data
 uploaded_files
 data_ingestion_audit
```

---

## 🔄 Rollback (If Needed)

```sql
-- WARNING: This drops all new tables!
DROP TABLE IF EXISTS data_ingestion_audit CASCADE;
DROP TABLE IF EXISTS uploaded_files CASCADE;
DROP TABLE IF EXISTS disease_specific_data CASCADE;
DROP TABLE IF EXISTS lab_results_batch CASCADE;
DROP TABLE IF EXISTS lab_results_flexible CASCADE;
DROP TABLE IF EXISTS lab_test_definitions CASCADE;
DROP TABLE IF EXISTS diagnoses CASCADE;
```

---

## 📊 Next Steps After Migration

1. ✅ Verify tables created
2. ✅ Seed lab_test_definitions with SLE + Sjogren tests (Task 2)
3. ✅ Test data insertion
4. ✅ Import existing patient data

---

## 🐛 Troubleshooting

### Error: "relation already exists"
```bash
# Tables already exist, safe to ignore
# Or drop tables first (see Rollback section)
```

### Error: "column does not exist"
```bash
# Check if old patient table has data
sudo docker exec usm-autoimmune-postgres psql -U usm_db_admin -d usm_autoimmune_registry -c "SELECT COUNT(*) FROM patients;"

# Backup data if needed before migration
```

### Error: "permission denied"
```bash
# Check database user permissions
sudo docker exec usm-autoimmune-postgres psql -U usm_db_admin -d usm_autoimmune_registry -c "\du"
```

---

**Status:** ✅ Ready to deploy  
**Time to run:** ~2-3 seconds  
**Downtime:** None (can run while API is running)
