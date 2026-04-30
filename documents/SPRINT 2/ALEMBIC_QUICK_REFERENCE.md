# Alembic Quick Reference Guide

**Author:** Syarifah Fajriyah  
**Date:** March 31, 2026  
**Sprint:** Sprint 2 Day 1

---

## Common Commands

### Check Migration Status
```bash
# Show current database version
docker exec usm-autoimmune-api bash -c "cd /app && alembic current"

# Show all migrations
docker exec usm-autoimmune-api bash -c "cd /app && alembic history"

# Show with details
docker exec usm-autoimmune-api bash -c "cd /app && alembic history --verbose"
```

### Create New Migration
```bash
# Manual migration (you write the code)
docker exec -it usm-autoimmune-api bash
cd /app
alembic revision -m "Description of change"

# Auto-generate (Alembic detects changes)
alembic revision --autogenerate -m "Description of change"
```

### Apply Migrations
```bash
# Apply all pending migrations
docker exec usm-autoimmune-api bash -c "cd /app && alembic upgrade head"

# Apply specific number of migrations
docker exec usm-autoimmune-api bash -c "cd /app && alembic upgrade +1"

# Apply to specific revision
docker exec usm-autoimmune-api bash -c "cd /app && alembic upgrade abc123def456"
```

### Rollback Migrations
```bash
# Rollback one migration
docker exec usm-autoimmune-api bash -c "cd /app && alembic downgrade -1"

# Rollback to specific revision
docker exec usm-autoimmune-api bash -c "cd /app && alembic downgrade e0006bde1e97"

# Rollback all (⚠️ DANGER: drops all tables)
docker exec usm-autoimmune-api bash -c "cd /app && alembic downgrade base"
```

### Preview Changes (Dry Run)
```bash
# See SQL without running
docker exec usm-autoimmune-api bash -c "cd /app && alembic upgrade head --sql"

docker exec usm-autoimmune-api bash -c "cd /app && alembic downgrade -1 --sql"
```

---

## Migration File Locations

```
/app/alembic/
├── versions/
│   ├── e0006bde1e97_initial_baseline_schema.py  ← Baseline migration
│   ├── abc123def456_add_refresh_tokens.py       ← Future migration
│   └── xyz789_add_token_version.py              ← Future migration
├── env.py          ← Python configuration (imports models)
└── script.py.mako  ← Template for new migrations

/app/alembic.ini    ← Main configuration (database URL)
```

---

## Configuration Files

### alembic.ini (Database Connection)
```ini
# File: /app/alembic.ini
sqlalchemy.url = postgresql://usm_db_admin:Mtai2026!@postgres:5432/usm_autoimmune_registry
script_location = /app/alembic
```

### env.py (Python Imports)
```python
# File: /app/alembic/env.py (lines 20-25)
import sys
sys.path.insert(0, "/")
from app.core.database import Base
import app.models
target_metadata = Base.metadata
```

---

## Workflow Examples

### Sprint 2 Day 2: Add Refresh Tokens Table

```bash
# 1. Enter container
docker exec -it usm-autoimmune-api bash
cd /app

# 2. Create migration
alembic revision -m "Add refresh tokens table"

# 3. Edit migration file
nano alembic/versions/xxxxx_add_refresh_tokens_table.py

# Add in upgrade():
# op.create_table('refresh_tokens',
#     sa.Column('id', sa.Integer(), primary_key=True),
#     sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
#     ...
# )

# 4. Apply migration
alembic upgrade head

# 5. Verify
alembic current

# 6. Exit
exit
```

### Sprint 2 Day 2: Add Token Version Column (Auto-Generate)

```bash
# 1. Edit model first (on Windows in VS Code)
# File: app/models/user.py
# Add: token_version = Column(Integer, default=0)

# 2. Upload to server (git push or sftp)

# 3. Auto-generate migration
docker exec -it usm-autoimmune-api bash
cd /app
alembic revision --autogenerate -m "Add token version to users"

# Alembic detects the new column automatically!
# Review the generated file:
cat alembic/versions/xxxxx_add_token_version_to_users.py

# 4. Apply
alembic upgrade head

# 5. Verify
alembic current
exit
```

### Rolling Back a Bad Migration

```bash
# Check current version
docker exec usm-autoimmune-api bash -c "cd /app && alembic current"
# Output: xyz789 (head), Add token version to users

# Rollback
docker exec usm-autoimmune-api bash -c "cd /app && alembic downgrade -1"

# Verify
docker exec usm-autoimmune-api bash -c "cd /app && alembic current"
# Output: abc123def, Add refresh tokens table

# Fix the migration file, then re-apply
docker exec usm-autoimmune-api bash -c "cd /app && alembic upgrade head"
```

---

## Database Queries

### Check Alembic Version in Database
```sql
-- In pgAdmin:
SELECT * FROM alembic_version;

-- Result:
-- version_num
-- e0006bde1e97
```

### See Migration History
```sql
-- Alembic doesn't store history in database
-- Use: alembic history command instead
```

---

## Troubleshooting Quick Fixes

### Can't Find alembic.ini
```bash
# Always use: cd /app &&
docker exec usm-autoimmune-api bash -c "cd /app && alembic current"
```

### ModuleNotFoundError: No module named 'app'
```bash
# Fix env.py:
docker exec -it usm-autoimmune-api bash
nano /app/alembic/env.py

# Change: sys.path.insert(0, "/app")
# To:     sys.path.insert(0, "/")
```

### Table Already Exists
```bash
# Use stamp for existing tables:
alembic stamp head  # NOT upgrade head
```

### Can't Connect to Database
```bash
# Check alembic.ini has correct host:
cat /app/alembic.ini | grep sqlalchemy.url

# Should be: @postgres:5432 (service name)
# NOT:       @usm-autoimmune-postgres:5432 (container name)
# NOT:       @localhost:5432 (not accessible)
```

---

## Important Notes

⚠️ **Always backup before production migrations**
```bash
# Backup production database before alembic upgrade
docker exec usm-autoimmune-postgres pg_dump -U usm_db_admin usm_autoimmune_registry > backup_$(date +%Y%m%d).sql
```

⚠️ **Test migrations in development first**
```bash
# Dev server: Test migration
alembic upgrade head

# Check app still works
curl http://192.168.196.97:8001/api/v1/health

# If OK, apply to production
# If broken, rollback: alembic downgrade -1
```

⚠️ **Never edit applied migrations**
```bash
# WRONG: Edit old migration file and re-run
# RIGHT: Create new migration to fix the issue
```

✅ **Git commit migrations with code**
```bash
git add alembic/versions/xxxxx_new_feature.py
git add app/models/user.py
git commit -m "Add refresh token support (USMA-117)"
git push
```

---

## Key Revision IDs

| Revision | Description | Date |
|----------|-------------|------|
| `e0006bde1e97` | Initial baseline schema (9 tables) | 2026-03-31 |
| *TBD* | Add refresh tokens table (USMA-117) | 2026-04-01 |
| *TBD* | Add token version to users (USMA-119) | 2026-04-01 |
| *TBD* | Add revoked tokens table (USMA-118) | 2026-04-02 |

---

## Resources

- **Full Documentation**: [DATABASE_MIGRATIONS_ALEMBIC.md](DATABASE_MIGRATIONS_ALEMBIC.md)
- **Official Docs**: https://alembic.sqlalchemy.org/
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/

---

**Last Updated:** March 31, 2026  
**Version:** 1.0
