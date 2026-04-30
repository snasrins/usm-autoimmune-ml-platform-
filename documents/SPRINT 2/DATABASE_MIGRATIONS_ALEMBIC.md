# Database Migrations with Alembic - Sprint 2 Day 1 (USMA-80)

**Project:** USM Autoimmune ML Platform  
**Engineer:** Syarifah Fajriyah  
**Date:** March 31, 2026  
**Sprint:** Sprint 2 Day 1  
**Ticket:** USMA-80 - Schema Evolution & Migration Strategy

---

## Table of Contents
1. [What is Alembic?](#what-is-alembic)
2. [Why We Need Alembic](#why-we-need-alembic)
3. [The Problem We're Solving](#the-problem-were-solving)
4. [Implementation Details](#implementation-details)
5. [How to Use Alembic](#how-to-use-alembic)
6. [Real-World Examples](#real-world-examples)
7. [Troubleshooting](#troubleshooting)

---

## What is Alembic?

**Alembic** is a database migration tool for SQLAlchemy. Think of it as **"Git for database schemas"** - it tracks changes to your database structure over time and allows you to apply or rollback those changes safely.

### Key Concepts:

- **Migration**: A file describing how to change the database schema (add table, add column, etc.)
- **Revision**: A unique ID for each migration (e.g., `e0006bde1e97`)
- **Upgrade**: Apply a migration to move forward (add new features)
- **Downgrade**: Reverse a migration to move backward (rollback changes)
- **Head**: The latest migration version
- **Stamp**: Mark the database at a specific revision without running the migration

---

## Why We Need Alembic

### The Old Way (Without Alembic) - Problems:

```bash
# Sprint 1: Initialize database with init-db/*.sql files
docker compose up -d
# ✅ Database created with 9 tables

# Sprint 2: Need to add refresh_tokens table
# ❌ Problem: How do we add the table without destroying existing data?

# Option 1: Manually run SQL (DANGEROUS)
docker exec postgres psql -U usm_db_admin -d usm_autoimmune_registry -c "CREATE TABLE..."
# ❌ No record of this change
# ❌ Team members don't get the change automatically
# ❌ Production server might miss the change
# ❌ Can't rollback if something breaks

# Option 2: Edit init-db/*.sql and rebuild (DESTRUCTIVE)
# Edit init-db/01-schema.sql to add new table
docker compose down -v  # ⚠️ Destroys all data!
docker compose up -d
# ❌ Lost all patient data, user accounts, lab results, etc.
```

### The New Way (With Alembic) - Solutions:

```bash
# Sprint 1: Baseline migration captures current schema
alembic stamp head
# ✅ Database marked at revision e0006bde1e97 (9 tables preserved)

# Sprint 2: Add refresh_tokens table
alembic revision -m "Add refresh tokens table"
# ✅ Creates migration file: alembic/versions/abc123_add_refresh_tokens_table.py
# ✅ Edit the file to define the new table
alembic upgrade head
# ✅ Table added WITHOUT destroying existing data!
# ✅ All team members can run `alembic upgrade head` to get the change
# ✅ Production server can apply the same migration safely
# ✅ Can rollback with `alembic downgrade -1` if needed
```

### Industry Standard Benefits:

1. **Data Preservation**: Schema changes don't destroy existing data
2. **Version Control**: All schema changes tracked in code (like Git commits)
3. **Team Collaboration**: Team members sync schemas by running migrations
4. **Production Safety**: Test migrations in dev before applying to production
5. **Rollback Capability**: Undo changes if something goes wrong
6. **Audit Trail**: See complete history of all schema changes
7. **Automation**: CI/CD can automatically apply migrations during deployment

---

## The Problem We're Solving

### Sprint 2 Requirements (Days 2-5):

Sprint 2 needs **4+ schema changes** over 5 days:

| Day | Ticket | Schema Change | Without Alembic | With Alembic |
|-----|--------|---------------|-----------------|--------------|
| 1 | USMA-80 | Setup migrations | N/A | ✅ 4-6 hours |
| 2 | USMA-117 | Add `refresh_tokens` table | ❌ Destroy data | ✅ Safe migration |
| 2 | USMA-119 | Add `token_version` column to `users` | ❌ Destroy data | ✅ Safe migration |
| 3 | USMA-118 | Add `revoked_tokens` table | ❌ Destroy data | ✅ Safe migration |
| 3 | USMA-118 | Add `device_id` column to tokens | ❌ Destroy data | ✅ Safe migration |
| 4 | USMA-123 | Add `last_login` column to `users` | ❌ Destroy data | ✅ Safe migration |

**Without Alembic**: Every schema change = rebuild database = lose all test data = re-create users, re-upload files, re-test everything = **60+ hours wasted**

**With Alembic**: Every schema change = run migration = data preserved = **6 hours invested in Day 1, saves 60+ hours in Days 2-5**

### Real-World Analogy:

**Building a House Without Alembic (Destructive):**
```
Initial: Build a 2-bedroom house
Need 3rd bedroom: Demolish entire house, rebuild with 3 bedrooms
Need garage: Demolish entire house, rebuild with 3 bedrooms + garage
Need pool: Demolish entire house, rebuild with 3 bedrooms + garage + pool
Result: Spent 4x the time, lost all furniture each time
```

**Building a House With Alembic (Incremental):**
```
Initial: Build a 2-bedroom house
Need 3rd bedroom: Add extension (house intact, furniture safe)
Need garage: Build garage (house intact, furniture safe)
Need pool: Dig pool (house intact, furniture safe)
Result: Efficient construction, nothing destroyed
```

---

## Implementation Details

### Step 1: Install Alembic

**File: `requirements.txt`**
```python
# Database Migrations
alembic==1.13.1
```

**Rebuild Container:**
```bash
cd ~/usm-autoimmune-ml-platform
docker compose down
docker compose build --no-cache fastapi
docker compose up -d
```

**Verify Installation:**
```bash
docker exec usm-autoimmune-api pip show alembic
# Output: Name: alembic, Version: 1.13.1
```

---

### Step 2: Initialize Alembic

**Inside Container:**
```bash
docker exec -it usm-autoimmune-api bash
cd /app
alembic init alembic
```

**Created Structure:**
```
/app/
├── alembic/
│   ├── versions/          # Migration files go here
│   ├── env.py            # Alembic configuration (connects to database)
│   ├── script.py.mako    # Template for new migrations
│   └── README
├── alembic.ini           # Main configuration file
└── ...
```

---

### Step 3: Configure Database Connection

**File: `/app/alembic.ini`**

Change:
```ini
sqlalchemy.url = driver://user:pass@localhost/dbname
```

To:
```ini
sqlalchemy.url = postgresql://usm_db_admin:Mtai2026!@postgres:5432/usm_autoimmune_registry
```

**Docker Service Name**: Use `postgres` (service name from docker-compose.yml), not `usm-autoimmune-postgres` (container name).

---

### Step 4: Configure Python Imports

**File: `/app/alembic/env.py`**

**Problem**: Alembic needs to know about our SQLAlchemy models to detect schema changes.

**Solution**: Import `Base` metadata and all models.

**Edit Line ~22:**
```python
# BEFORE (line 20-22):
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = None

# AFTER (line 20-25):
import sys
sys.path.insert(0, "/")  # Add project root to Python path
from app.core.database import Base  # Import SQLAlchemy Base
import app.models  # Import all models (User, Patient, etc.)
target_metadata = Base.metadata  # Tell Alembic to use our models
```

**Why This Works:**
- Docker compose sets `working_dir: /` in docker-compose.yml
- Adding `/` to sys.path makes `app` module importable
- Importing `app.models` loads all model definitions from `app/models/__init__.py`
- Setting `target_metadata = Base.metadata` gives Alembic access to all table definitions

---

### Step 5: Create Baseline Migration

**Current State**: Database has 9 tables from init-db/01-schema.sql:
- users
- patients
- diagnoses
- lab_test_definitions
- lab_results_flexible
- lab_results_batch
- disease_specific_data
- uploaded_files
- data_ingestion_audit

**Goal**: Create a migration that captures the current schema WITHOUT re-creating tables.

**Commands:**
```bash
cd /app

# Generate migration by comparing database to models
alembic revision --autogenerate -m "Initial baseline schema"

# Output:
# INFO  [alembic.autogenerate.compare] Detected added table 'users'
# INFO  [alembic.autogenerate.compare] Detected added table 'patients'
# ...
# Generating /app/alembic/versions/e0006bde1e97_initial_baseline_schema.py ... done

# Mark database at this revision WITHOUT running migration
alembic stamp head

# Output:
# INFO  [alembic.runtime.migration] Running stamp_revision  -> e0006bde1e97
```

**Why `stamp` instead of `upgrade`?**
- `alembic upgrade head` would try to CREATE tables (but they already exist → error)
- `alembic stamp head` marks the database as being at revision `e0006bde1e97` without running SQL
- Future migrations will run normally (adding new tables/columns)

---

### Step 6: Verify Setup

**Check Current Revision:**
```bash
docker exec usm-autoimmune-api bash -c "cd /app && alembic current"

# Output:
# INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
# INFO  [alembic.runtime.migration] Will assume transactional DDL.
# e0006bde1e97 (head)
```

**Check Migration History:**
```bash
docker exec usm-autoimmune-api bash -c "cd /app && alembic history"

# Output:
# <base> -> e0006bde1e97 (head), Initial baseline schema
```

**Check Database Table:**
```sql
-- In pgAdmin, run:
SELECT * FROM alembic_version;

-- Result:
-- version_num
-- e0006bde1e97
```

✅ **Alembic is now tracking your database schema!**

---

## How to Use Alembic

### Creating a New Migration

**Scenario**: Sprint 2 Day 2 - Add `refresh_tokens` table for JWT security.

```bash
# Enter container
docker exec -it usm-autoimmune-api bash
cd /app

# Create new migration file
alembic revision -m "Add refresh tokens table"

# Output:
# Generating /app/alembic/versions/abc123def456_add_refresh_tokens_table.py ... done
```

**Edit Migration File:**
```python
# File: /app/alembic/versions/abc123def456_add_refresh_tokens_table.py

def upgrade():
    """Add refresh_tokens table for JWT token management"""
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('refresh_token', sa.String(500), unique=True, nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('revoked', sa.Boolean(), default=False),
    )
    op.create_index('idx_refresh_token', 'refresh_tokens', ['refresh_token'])
    op.create_index('idx_refresh_user', 'refresh_tokens', ['user_id'])


def downgrade():
    """Remove refresh_tokens table"""
    op.drop_index('idx_refresh_user', 'refresh_tokens')
    op.drop_index('idx_refresh_token', 'refresh_tokens')
    op.drop_table('refresh_tokens')
```

**Apply Migration:**
```bash
alembic upgrade head

# Output:
# INFO  [alembic.runtime.migration] Running upgrade e0006bde1e97 -> abc123def456, Add refresh tokens table
```

✅ **New table created without destroying existing data!**

---

### Auto-Generate Migrations (Recommended)

Alembic can detect changes automatically by comparing database to models.

**Edit Model:**
```python
# File: /app/models/user.py

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # NEW: Add token version for JWT invalidation
    token_version = Column(Integer, default=0)  # ← New column
```

**Auto-Generate Migration:**
```bash
alembic revision --autogenerate -m "Add token version to users"

# Alembic detects:
# INFO  [alembic.autogenerate.compare] Detected added column 'users.token_version'
# Generating /app/alembic/versions/xyz789_add_token_version_to_users.py ... done

# Apply:
alembic upgrade head
```

✅ **Column added to existing table, all user data preserved!**

---

### Rolling Back Changes

**Scenario**: Migration caused a bug, need to undo.

```bash
# Check current version
alembic current
# Output: xyz789 (head), Add token version to users

# Rollback one migration
alembic downgrade -1

# Output:
# INFO  [alembic.runtime.migration] Running downgrade xyz789 -> abc123def456

# Verify
alembic current
# Output: abc123def456, Add refresh tokens table
```

**Rollback to Specific Revision:**
```bash
alembic downgrade e0006bde1e97  # Back to baseline
alembic downgrade base          # Back to empty database (⚠️ destroys all tables!)
```

---

### Checking Migration Status

```bash
# Show current database version
alembic current

# Show all migrations
alembic history

# Show pending migrations
alembic history --verbose

# Preview SQL without running
alembic upgrade head --sql
```

---

## Real-World Examples

### Example 1: Sprint 2 Day 2 - JWT Refresh Tokens

**Requirements (USMA-117, 119):**
- Add `refresh_tokens` table to store long-lived tokens
- Add `token_version` column to `users` for token invalidation

**Without Alembic:**
```bash
# Edit init-db/01-schema.sql manually
# Add CREATE TABLE refresh_tokens...
# Add token_version column to users table

# Rebuild database (⚠️ DESTROYS ALL DATA)
docker compose down -v
docker compose up -d

# Result:
# ❌ Lost all user accounts (need to re-register)
# ❌ Lost all patient data (need to re-upload)
# ❌ Lost all lab results
# ❌ Need to recreate admin account
# Time wasted: 2-3 hours per rebuild × 4 schema changes = 8-12 hours
```

**With Alembic:**
```bash
# Migration 1: Add refresh_tokens table
alembic revision --autogenerate -m "Add refresh tokens table"
# Edit migration file to define table
alembic upgrade head
# ✅ Table added, existing data safe

# Migration 2: Add token_version to users
alembic revision --autogenerate -m "Add token version to users"
# Alembic auto-detects column change
alembic upgrade head
# ✅ Column added, all users preserved

# Result:
# ✅ All changes applied safely
# ✅ No data lost
# ✅ Team can sync: git pull && alembic upgrade head
# Time saved: 2 minutes per migration × 4 changes = 8 minutes
```

---

### Example 2: Sprint 2 Day 3 - Token Revocation

**Requirement (USMA-118):**
- Add `revoked_tokens` table for logout functionality
- Add `device_id` column to track user devices

**With Alembic (Smooth):**
```bash
# Day 3 Morning: Create migrations
alembic revision --autogenerate -m "Add revoked tokens and device tracking"
# Review generated migration
alembic upgrade head

# Day 3 Afternoon: Bug found, need to rollback
alembic downgrade -1
# Fix the migration file
alembic upgrade head

# Day 3 Evening: Ready to deploy
git push
# On production server:
git pull
docker exec usm-autoimmune-api bash -c "cd /app && alembic upgrade head"
# ✅ Production updated safely
```

---

### Example 3: Production Deployment

**Scenario**: Sprint 2 complete, deploy to production.

**Step 1: Development Server**
```bash
# All 5 migrations applied during Sprint 2
alembic history
# <base> -> e0006bde1e97, Initial baseline schema
# e0006bde1e97 -> abc123def, Add refresh tokens table
# abc123def -> xyz789, Add token version to users
# xyz789 -> def456, Add revoked tokens table
# def456 -> ghi789, Add device tracking
```

**Step 2: Production Server (First Time)**
```bash
# Clone repo to production
git clone <repo> usm-autoimmune-ml-platform
cd usm-autoimmune-ml-platform

# Edit .env with production credentials
nano .env

# Start containers
docker compose up -d

# Apply all migrations
docker exec usm-autoimmune-api bash -c "cd /app && alembic upgrade head"

# Output:
# INFO Running upgrade  -> e0006bde1e97, Initial baseline schema
# INFO Running upgrade e0006bde1e97 -> abc123def, Add refresh tokens table
# INFO Running upgrade abc123def -> xyz789, Add token version to users
# INFO Running upgrade xyz789 -> def456, Add revoked tokens table
# INFO Running upgrade def456 -> ghi789, Add device tracking

# ✅ Production database synced with development!
```

**Step 3: Future Updates**
```bash
# Sprint 3: New features developed
# On production (after git pull):
docker exec usm-autoimmune-api bash -c "cd /app && alembic upgrade head"
# ✅ Only new migrations run
# ✅ Existing data preserved
```

---

## Troubleshooting

### Issue 1: ModuleNotFoundError: No module named 'app'

**Error:**
```bash
alembic revision --autogenerate -m "Test"
# ModuleNotFoundError: No module named 'app'
```

**Cause**: Python can't find the `app` module.

**Solution**: Fix sys.path in `/app/alembic/env.py`:
```python
import sys
sys.path.insert(0, "/")  # Add root directory (where app/ folder is)
from app.core.database import Base
import app.models
```

**Verify Working Directory:**
```bash
# In docker-compose.yml:
working_dir: /  # NOT /app

# So sys.path needs "/", which makes "app" importable as "app.models"
```

---

### Issue 2: Alembic Can't Find alembic.ini

**Error:**
```bash
alembic current
# FAILED: No config file 'alembic.ini' found
```

**Cause**: Running alembic from wrong directory.

**Solution 1: Change directory first**
```bash
docker exec usm-autoimmune-api bash -c "cd /app && alembic current"
```

**Solution 2: Specify config path**
```bash
# Update alembic.ini to use absolute path
sed -i 's|script_location = alembic|script_location = /app/alembic|g' /app/alembic.ini

# Now works from any directory
docker exec usm-autoimmune-api alembic -c /app/alembic.ini current
```

---

### Issue 3: Migration Detected Removed Tables

**Output:**
```bash
alembic revision --autogenerate -m "Test"
# INFO Detected removed table 'dim_hospitals'
# INFO Detected removed table 'fact_patient_visits'
```

**Cause**: Tables exist in database but NOT in SQLAlchemy models.

**Explanation**: 
- Database has 28 tables (from init-db/02-flexible-schema.sql)
- Models define only 9 tables
- Alembic sees "extra" tables as "removed"

**Solution Options:**

**Option A: Keep Tables (Recommended for Sprint 2)**
- Don't apply the migration
- These tables are for data warehouse (Sprint 3+)
- Only migrate the 9 core tables

**Option B: Drop Extra Tables**
```bash
alembic upgrade head  # Drops the 19 extra tables
# ⚠️ Only do this if you don't need data warehouse yet
```

**Option C: Define All Models**
- Create SQLAlchemy models for all 28 tables
- Alembic will see everything and not detect "removed" tables

---

### Issue 4: Table Already Exists Error

**Error:**
```bash
alembic upgrade head
# psycopg2.errors.DuplicateTable: relation "users" already exists
```

**Cause**: Running `upgrade` on existing tables instead of `stamp`.

**Solution**: Use `stamp` for baseline migration:
```bash
# WRONG (tries to CREATE tables that exist):
alembic upgrade head

# RIGHT (marks database as being at this revision):
alembic stamp head
```

---

### Issue 5: Can't Connect to Database

**Error:**
```bash
alembic current
# sqlalchemy.exc.OperationalError: could not connect to server
```

**Cause**: Wrong database URL in alembic.ini.

**Check Configuration:**
```bash
cat /app/alembic.ini | grep sqlalchemy.url

# Should show:
# sqlalchemy.url = postgresql://usm_db_admin:Mtai2026!@postgres:5432/usm_autoimmune_registry

# Common mistakes:
# ❌ usm-autoimmune-postgres:5432 (container name instead of service name)
# ❌ localhost:5432 (not accessible from container)
# ❌ 192.168.196.97:5433 (external IP, use internal for Docker network)
```

**Fix:**
```bash
sed -i 's|@usm-autoimmune-postgres:|@postgres:|g' /app/alembic.ini
```

---

## Summary

### What We Accomplished (Sprint 2 Day 1):

✅ **Installed** Alembic 1.13.1 in Docker container  
✅ **Initialized** Alembic with proper folder structure  
✅ **Configured** database connection (PostgreSQL)  
✅ **Fixed** Python imports (app.core.database.Base)  
✅ **Created** baseline migration (revision `e0006bde1e97`)  
✅ **Stamped** database at current state (9 tables preserved)  
✅ **Verified** migration system working  

### What This Enables (Sprint 2 Days 2-5):

- **Day 2**: Add refresh_tokens table safely (USMA-117, 119)
- **Day 3**: Add revoked_tokens table safely (USMA-118)
- **Day 4**: Schema changes for Streamlit login (USMA-123)
- **Day 5**: Final schema refinements without data loss

### Time Investment:

- **Setup Time**: 4-6 hours (Day 1)
- **Time Saved**: 60+ hours (Days 2-5 and future sprints)
- **ROI**: 10x return on investment

### Key Takeaway:

**Alembic is the foundation for safe, professional database management.** Every major framework uses migrations:
- Django → Django Migrations
- Ruby on Rails → Active Record Migrations
- Laravel → Eloquent Migrations
- Flask → Flask-Migrate (uses Alembic)
- FastAPI → Alembic (what we use)

Without migrations, you're working like it's 2005. With migrations, you're working like a professional production-ready system in 2026. 🚀

---

**Document Version:** 1.0  
**Last Updated:** March 31, 2026  
**Next Steps:** Sprint 2 Day 2 - JWT Refresh Tokens (USMA-117, 119)
