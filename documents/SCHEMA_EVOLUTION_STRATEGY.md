# Schema Evolution Strategy
**USM Autoimmune ML Platform**  
**Tasks:** USMA-72 (Schema Evolution), USMA-73 (Migration Framework)  
**Date:** April 3, 2026  
**Data Engineer:** Syarifah Fajriyah

---

## 🎯 **Objectives**

1. **Enable schema changes** without data loss or downtime
2. **Track schema versions** across environments
3. **Support rollback** to previous schema versions
4. **Auto-detect schema drift** between code and database
5. **Maintain backward compatibility** for 2 versions

---

## 🏗️ **Architecture**

### **3-Layer Schema Evolution**

```
┌─────────────────────────────────────────────────────┐
│ Layer 1: Alembic (Database Migrations)             │
│  - Version control for schema changes               │
│  - Upgrade/downgrade scripts                        │
│  - Migration history in alembic_version table       │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│ Layer 2: Flexible Schema (Snowflake + JSONB)       │
│  - Fact/Dimension tables (structured)              │
│  - JSONB columns (semi-structured)                  │
│  - Dynamic entity registration                      │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│ Layer 3: Metadata Catalog (Schema Registry)        │
│  - Track all tables, columns, types                │
│  - Version history of schema changes                │
│  - Data lineage and dependencies                    │
└─────────────────────────────────────────────────────┘
```

---

## 🔧 **Migration Framework: Alembic**

### **Why Alembic?**
- ✅ **Version control** for database schemas
- ✅ **Automatic migration** generation
- ✅ **Rollback support** (upgrade/downgrade)
- ✅ **Branch management** (merge schema changes from multiple devs)
- ✅ **SQLAlchemy integration** (works with existing ORM)

### **Directory Structure**

```
usm-autoimmune-ml-platform/
├── alembic/
│   ├── versions/
│   │   ├── 9a2e81360415_add_refresh_tokens.py      ← Existing
│   │   ├── validation_queue_001_add_table.py       ← New (unstructured pipeline)
│   │   ├── metadata_002_add_versioning.py          ← New (schema tracking)
│   │   └── flexible_003_add_disease_registry.py    ← Future
│   └── env.py                                       ← Alembic environment
├── alembic.ini                                      ← Configuration
└── init-db/
    ├── 01-schema.sql                                 ← Base schema (manual backup)
    ├── 02-flexible-schema.sql                        ← Snowflake design (manual)
    └── 03-validation-queue.sql                       ← Legacy (to be replaced by Alembic)
```

---

## 📋 **Migration Workflow**

### **1. Create Migration (Auto-generate)**

```bash
# Auto-generate migration from SQLAlchemy models
cd /path/to/usm-autoimmune-ml-platform
alembic revision --autogenerate -m "Add validation_queue table"

# Creates: alembic/versions/<rev_id>_add_validation_queue_table.py
```

### **2. Review Migration Script**

```python
# alembic/versions/validation_queue_001.py
def upgrade() -> None:
    """Apply schema change"""
    op.create_table(
        'validation_queue',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('validation_data', postgresql.JSONB(), nullable=False),
        # ...
    )
    op.create_index('idx_validation_status', 'validation_queue', ['status'])

def downgrade() -> None:
    """Rollback schema change"""
    op.drop_index('idx_validation_status', table_name='validation_queue')
    op.drop_table('validation_queue')
```

### **3. Test Migration (Dev Environment)**

```bash
# Check current version
alembic current

# Show pending migrations
alembic history

# Dry-run (show SQL without executing)
alembic upgrade head --sql

# Apply migration
alembic upgrade head

# Verify
docker exec usm-autoimmune-postgres psql -U usm_db_admin -d usm_autoimmune_registry -c "\d validation_queue"
```

### **4. Rollback (if needed)**

```bash
# Rollback one version
alembic downgrade -1

# Rollback to specific version
alembic downgrade 9a2e81360415

# Rollback everything
alembic downgrade base
```

### **5. Deploy to Production**

```bash
# On server (via SSH)
cd ~/usm-autoimmune-ml-platform

# Pull latest code (includes migration)
git pull origin main

# Run migration
docker exec usm-autoimmune-api alembic upgrade head

# Verify
docker exec usm-autoimmune-postgres psql -U usm_db_admin -d usm_autoimmune_registry -c "SELECT version_num FROM alembic_version"
```

---

## 🗄️ **Flexible Schema Strategy**

### **Principle: Expand, Don't Break**

```sql
-- ❌ NEVER DO THIS (breaks existing queries)
ALTER TABLE patients DROP COLUMN age;
ALTER TABLE patients RENAME COLUMN name TO full_name;

-- ✅ DO THIS INSTEAD (backward compatible)
-- Add new column, keep old one for 2 versions
ALTER TABLE patients ADD COLUMN full_name VARCHAR(200);
UPDATE patients SET full_name = name WHERE full_name IS NULL;
-- Mark old column as deprecated
COMMENT ON COLUMN patients.name IS 'DEPRECATED: Use full_name instead. Will be removed in v3.0';
```

### **Migration Patterns**

#### **Pattern 1: Adding Columns (Always Safe)**

```python
# Migration: Add new column
def upgrade():
    op.add_column('patients', sa.Column('ethnicity', sa.String(50), nullable=True))
    
# No downgrade needed for backward compatibility
def downgrade():
    op.drop_column('patients', 'ethnicity')
```

#### **Pattern 2: Renaming Columns (Use View)**

```python
# Migration: Rename via view
def upgrade():
    # Add new column
    op.add_column('patients', sa.Column('full_name', sa.String(200)))
    
    # Copy data
    op.execute("UPDATE patients SET full_name = name WHERE full_name IS NULL")
    
    # Create view for backward compatibility
    op.execute("""
        CREATE OR REPLACE VIEW patients_v1 AS 
        SELECT id, full_name AS name, age, gender FROM patients
    """)
    
    # Mark old column deprecated
    op.execute("COMMENT ON COLUMN patients.name IS 'DEPRECATED: Use full_name'")

def downgrade():
    op.drop_column('patients', 'full_name')
    op.execute("DROP VIEW IF EXISTS patients_v1")
```

#### **Pattern 3: Changing Data Types (Staged Approach)**

```python
# Stage 1: Add new column with new type
def upgrade():
    # Add new column
    op.add_column('lab_results', sa.Column('test_date_new', sa.Date(), nullable=True))
    
    # Migrate data
    op.execute("""
        UPDATE lab_results 
        SET test_date_new = test_date::date 
        WHERE test_date_new IS NULL
    """)
    
# Stage 2: (Next release) Swap columns
def upgrade_stage2():
    op.drop_column('lab_results', 'test_date')
    op.alter_column('lab_results', 'test_date_new', new_column_name='test_date')
```

#### **Pattern 4: Adding Tables (Always Safe)**

```python
# Migration: Add validation_queue table
def upgrade():
    op.create_table(
        'validation_queue',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('validation_data', postgresql.JSONB()),
        # ...
    )

def downgrade():
    op.drop_table('validation_queue')
```

#### **Pattern 5: Flexible Columns (JSONB Evolution)**

```sql
-- No migration needed! Just update validation_data structure
-- Old format:
{"document": {"filename": "sample.pdf", "page_count": 7}}

-- New format (backward compatible):
{"document": {"filename": "sample.pdf", "page_count": 7, "file_hash": "sha256:..."}}

-- Queries work with both:
SELECT validation_data->'document'->>'filename' FROM validation_queue;
```

---

## 📊 **Schema Version Tracking**

### **Metadata Table: schema_versions**

```sql
CREATE TABLE schema_versions (
    version_id SERIAL PRIMARY KEY,
    schema_version VARCHAR(20) NOT NULL,           -- e.g., "v2.1.0"
    alembic_revision VARCHAR(50) NOT NULL,         -- e.g., "validation_queue_001"
    migration_name VARCHAR(200),                   -- e.g., "Add validation_queue table"
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    applied_by VARCHAR(100),                       -- e.g., "syarifah@usm.my"
    description TEXT,                              -- Migration notes
    is_breaking BOOLEAN DEFAULT FALSE,             -- Breaking change flag
    backward_compatible_until VARCHAR(20)          -- e.g., "v3.0.0"
);

-- Track table-level changes
CREATE TABLE schema_change_log (
    change_id SERIAL PRIMARY KEY,
    version_id INTEGER REFERENCES schema_versions(version_id),
    table_name VARCHAR(100) NOT NULL,
    change_type VARCHAR(50),                       -- ADD_COLUMN, DROP_COLUMN, RENAME_TABLE
    change_details JSONB,                          -- {"old": "name", "new": "full_name"}
    change_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **Auto-populate on Migration**

```python
# In each Alembic migration:
def upgrade():
    # ... actual schema changes ...
    
    # Log schema version
    op.execute("""
        INSERT INTO schema_versions (schema_version, alembic_revision, migration_name, applied_by, description)
        VALUES ('v2.1.0', 'validation_queue_001', 'Add validation_queue table', 'system', 
                'Added validation_queue for unstructured pipeline human-in-the-loop workflow')
    """)
    
    # Log table changes
    op.execute("""
        INSERT INTO schema_change_log (table_name, change_type, change_details)
        VALUES ('validation_queue', 'ADD_TABLE', 
                '{"columns": ["id", "dataset_id", "validation_data", "status"]}'::jsonb)
    """)
```

---

## 🚀 **Schema Evolution Examples**

### **Example 1: Add New Disease (No Migration)**

```python
# Just INSERT into dimension table
INSERT INTO dim_diseases (disease_name, category) 
VALUES ('Rheumatoid Arthritis', 'Autoimmune');

# No schema migration needed!
```

### **Example 2: Add New Lab Test (No Migration)**

```python
# Register test in catalog
INSERT INTO lab_test_definitions (test_code, test_name, category, unit)
VALUES ('il12_p70', 'IL-12 p70', 'Cytokine', 'pg/ml');

# Store results in existing fact table
INSERT INTO lab_results_flexible (patient_id, test_id, value_numeric)
VALUES (123, <new_test_id>, 45.7);

# No schema migration needed!
```

### **Example 3: Add Patient Consent Field (Migration Required)**

```python
# alembic/versions/002_add_consent_tracking.py
def upgrade():
    op.add_column('patients', 
        sa.Column('consent_date', sa.Date(), nullable=True))
    op.add_column('patients', 
        sa.Column('consent_version', sa.String(20), nullable=True))
    
    # Log change
    op.execute("""
        INSERT INTO schema_versions (schema_version, alembic_revision, migration_name)
        VALUES ('v2.2.0', 'consent_tracking_002', 'Add patient consent tracking')
    """)

def downgrade():
    op.drop_column('patients', 'consent_version')
    op.drop_column('patients', 'consent_date')
```

---

## 🔍 **Schema Drift Detection**

### **Automated Check**

```python
# app/services/schema_validator.py
class SchemaValidator:
    def check_drift(self):
        """Compare SQLAlchemy models vs actual database schema"""
        from alembic.runtime.migration import MigrationContext
        from alembic.autogenerate import compare_metadata
        from sqlalchemy import create_engine
        from app.core.database import Base
        
        engine = create_engine(DATABASE_URL)
        conn = engine.connect()
        
        # Get current database schema
        mc = MigrationContext.configure(conn)
        
        # Compare with SQLAlchemy models
        diff = compare_metadata(mc, Base.metadata)
        
        if diff:
            print("⚠️ Schema drift detected!")
            for change in diff:
                print(f"   - {change}")
            return False
        else:
            print("✅ Schema in sync with models")
            return True

# Run on startup
if __name__ == "__main__":
    validator = SchemaValidator()
    if not validator.check_drift():
        print("Run: alembic revision --autogenerate")
```

---

## 📅 **Migration Schedule**

### **Development**
- **Daily:** Auto-generate migrations from model changes
- **Weekly:** Review pending migrations, merge if conflicts
- **Sprint:** Test migrations in staging before sprint end

### **Production**
- **Monthly:** Scheduled migration windows (1st Saturday, 2am)
- **Hotfix:** Emergency migrations (requires PM approval)
- **Rollback Plan:** Always test downgrade before applying upgrade

---

## ✅ **Best Practices**

### **1. Always Write Reversible Migrations**
```python
# ✅ Good: Both upgrade() and downgrade()
def upgrade():
    op.add_column('patients', sa.Column('dob', sa.Date()))

def downgrade():
    op.drop_column('patients', 'dob')

# ❌ Bad: No downgrade
def downgrade():
    pass  # TODO: implement rollback
```

### **2. Test Migrations Locally First**
```bash
# Create test database
docker exec usm-autoimmune-postgres createdb -U usm_db_admin test_migration

# Run migration
DATABASE_URL=postgresql://usm_db_admin:password@localhost:5435/test_migration alembic upgrade head

# Verify
# ...

# Cleanup
docker exec usm-autoimmune-postgres dropdb -U usm_db_admin test_migration
```

### **3. Use Transactions**
```python
# Alembic uses transactions by default
# But for data migrations:
def upgrade():
    # Schema change (DDL)
    op.add_column('patients', sa.Column('full_name', sa.String(200)))
    
    # Data migration (DML) - wrap in transaction
    connection = op.get_bind()
    connection.execute("UPDATE patients SET full_name = name WHERE full_name IS NULL")
```

### **4. Document Breaking Changes**
```python
def upgrade():
    """
    ⚠️ BREAKING CHANGE:
    - Removes 'name' column from patients table
    - Applications must use 'full_name' instead
    - Backward compatibility: v2.0 - v2.2 (6 months)
    - Deprecated since: v2.0 (2026-01-15)
    - Removal date: v2.3 (2026-06-15)
    """
    op.drop_column('patients', 'name')
```

### **5. Version Naming Convention**
```
Format: <feature>_<sequence>_<description>

Examples:
- validation_queue_001_add_table
- patients_002_add_consent_fields
- lab_results_003_add_reference_ranges
- schema_004_add_audit_trail
```

---

## 📊 **Monitoring & Alerts**

### **Schema Health Checks**

```python
# app/api/endpoints/admin.py
@router.get("/schema/status")
async def get_schema_status(current_user: User = Depends(get_current_superuser)):
    """Show current schema version and pending migrations"""
    
    # Check current version
    current_version = db.execute("SELECT version_num FROM alembic_version").scalar()
    
    # Get schema version
    schema_info = db.execute("""
        SELECT schema_version, applied_at, applied_by, description
        FROM schema_versions 
        ORDER BY applied_at DESC 
        LIMIT 1
    """).first()
    
    # Check for drift
    drift_detected = SchemaValidator().check_drift()
    
    return {
        "alembic_revision": current_version,
        "schema_version": schema_info.schema_version,
        "last_migration": schema_info.applied_at,
        "applied_by": schema_info.applied_by,
        "drift_detected": not drift_detected,
        "health": "healthy" if drift_detected else "drift_detected"
    }
```

---

## 🎯 **Implementation Checklist**

### **USMA-72: Schema Evolution Strategy**
- [x] Document 3-layer architecture
- [x] Define migration patterns (expand, don't break)
- [x] Create schema_versions tracking table
- [x] Define backward compatibility policy (2 versions)
- [ ] Implement schema drift detection
- [ ] Add monitoring dashboard

### **USMA-73: Database Migration Framework**
- [x] Alembic configuration (existing)
- [x] Create validation_queue migration
- [x] Document migration workflow
- [x] Define version naming convention
- [ ] Create pre-migration test script
- [ ] Setup automated migration pipeline

### **USMA-84: Dataset Versioning System**
- [ ] Add version column to metadata_datasets
- [ ] Track schema version per dataset
- [ ] Link datasets to schema versions
- [ ] Implement dataset lineage tracking

---

## 📚 **Related Tasks**

- **USMA-27**: Implement dataset versioning (depends on USMA-73)
- **USMA-76**: MinIO bucket lifecycle (separate concern)
- **USMA-84**: Dataset versioning system (builds on USMA-72/73)

---

**Status:** ✅ Strategy Documented, Framework Implemented  
**Next:** Apply migration to production, implement drift detection
