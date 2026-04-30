# Snapshot & Backup Strategy Analysis
**Sprint 2 - Technical Decision Document**  
**Date:** April 5, 2026  
**Decision:** DEFER to Sprint 3

---

## 🤔 The Question

**Should we implement snapshot/backup functionality now, or move it to the next phase?**

---

## 📊 Current State Assessment

### What We Already Have (Built-in Protection)

#### 1. **Database Backups (PostgreSQL)**
- **Automated daily backups** via Docker volume persistence
- **WAL (Write-Ahead Logging)** enabled for point-in-time recovery
- **Retention:** 7 days of transaction logs

#### 2. **MinIO Object Versioning**
- **Every file version preserved** automatically
- **Deleted files recoverable** within lifecycle policy period
- **Example:** 
  - Upload `sle_registry.csv` → Version 1
  - Modify and re-upload → Version 2 created, Version 1 preserved
  - Delete file → Both versions still exist for 365 days

#### 3. **Dataset Version Control (Just Implemented)**
- **Semantic versioning** tracks dataset evolution
- **Parent-child relationships** preserve lineage
- **Immutable history** - old versions never deleted (only marked deprecated)
- **Audit trail** - who created/modified what and when

#### 4. **Application-Level Redundancy**
- **Dataset metadata** stored in PostgreSQL
- **File data** stored in MinIO
- **Separation of concerns** - corruption in one doesn't affect the other

---

## 🎯 What "Snapshot/Backup" Would Add

### Option 1: Database Snapshots
**What:** Periodic full database dumps for disaster recovery

**We Already Have:**
- ✅ Docker volume backups (automated)
- ✅ PostgreSQL WAL for point-in-time recovery
- ✅ Database schema under version control (Alembic migrations)

**What's Missing:**
- ❌ Off-site backup replication
- ❌ Automated restore testing
- ❌ Geo-redundancy (second datacenter)

**Effort:** **Medium** (2-3 days)
- Configure pg_dump scheduled tasks
- Set up S3/Google Cloud Storage bucket for backup storage
- Create restore procedure documentation
- Implement backup verification scripts

---

### Option 2: MinIO Bucket Replication
**What:** Real-time sync to second MinIO instance or S3

**We Already Have:**
- ✅ Object versioning (protects against accidental deletion)
- ✅ Lifecycle policies (automatic cleanup)
- ✅ Single-site redundancy (RAID on server)

**What's Missing:**
- ❌ Off-site backup (if server fails completely)
- ❌ Real-time replication to second location
- ❌ Disaster recovery site

**Effort:** **High** (5-7 days)
- Set up second MinIO instance or AWS S3 bucket
- Configure bucket replication policies
- Test failover procedures
- Monitor replication lag

---

### Option 3: Application-Level Snapshots
**What:** Export entire datasets (metadata + files) to archive format

**We Already Have:**
- ✅ Dataset versioning (preserves history)
- ✅ JSONB metadata (flexible storage)
- ✅ RESTful API (can build export endpoint)

**What's Missing:**
- ❌ One-click "export dataset v1.2.3" feature
- ❌ Compressed archive format (.tar.gz with metadata)
- ❌ Import/restore from archive

**Effort:** **Low-Medium** (3-4 days)
- Create `/datasets/{id}/export` endpoint
- Package files + metadata into tar.gz
- Create `/datasets/import` endpoint for restore
- UI for download/upload archives

---

## ⚖️ Cost-Benefit Analysis

### If We Implement Now (Pros)

✅ **Complete disaster recovery** capability
- Can recover from total server failure
- Peace of mind for production data

✅ **Compliance enhancement**
- Some regulations require off-site backups
- Demonstrates data protection maturity

✅ **Dataset portability**
- Easy to share datasets with collaborators
- Can migrate to different infrastructure

### If We Implement Now (Cons)

❌ **Scope creep**
- Just completed 3 major features (USMA-84, 27, 76)
- Team fatigue likely (need time to stabilize)

❌ **Low immediate value**
- Current protections adequate for development phase
- No production users yet (no data to lose)

❌ **Delayed validation**
- Should first validate current versioning system works
- May discover snapshot requirements change based on usage

❌ **Resource intensive**
- 5-14 days of development time
- Additional infrastructure costs (backup storage)
- Ongoing maintenance burden

---

## 🧠 Technical Considerations

### Current Risk Level: **LOW**

**Why current protection is sufficient:**

1. **Database:**
   - Daily automated backups
   - 7-day retention
   - WAL for point-in-time recovery
   - Risk: Total server failure + corrupt backup (extremely rare)

2. **Object Storage:**
   - Versioning prevents accidental deletion
   - Lifecycle policies preserve data for 365-730 days
   - RAID protects against disk failure
   - Risk: Server fire/theft (physical disaster)

3. **Dataset Metadata:**
   - Immutable version history
   - Parent-child lineage preserved
   - Risk: Malicious deletion (prevented by authentication)

**Realistic Disaster Scenarios:**

| Scenario | Current Protection | Recovery Time | Data Loss Risk |
|----------|-------------------|---------------|----------------|
| Accidental file deletion | MinIO versioning | ~5 min | None |
| Accidental dataset deletion | Version history | ~10 min | None |
| Database corruption | WAL + daily backup | ~30 min | < 24 hours |
| Server hardware failure | Docker volumes | ~2 hours | None (if volumes intact) |
| Server fire/theft | ❌ **No off-site backup** | ❌ **Days-weeks** | ❌ **Total loss** |

**Analysis:** Only catastrophic physical disaster is unprotected

---

### Infrastructure Maturity Assessment

**Current Phase:** **Development/Early Production**
- ~150 datasets in system
- 5-10 active users
- No revenue-critical operations
- Regulatory compliance not fully required yet

**When to prioritize snapshots:** **Production Scale**
- > 1,000 datasets
- > 50 active users
- Revenue/research dependent on platform
- Full regulatory audit required

**Conclusion:** Not urgent for current phase

---

## 💡 Recommendation: DEFER to Sprint 3

### Reasoning

1. **Validate Current System First**
   - Need 2-4 weeks of real usage
   - May discover versioning issues to fix
   - User feedback may change requirements

2. **Feature Fatigue**
   - Just completed 3 major features
   - Need time for testing and stabilization
   - Documentation still being written

3. **Low Immediate Risk**
   - Current protections adequate for dev phase
   - No production-critical data yet
   - Physical disaster extremely unlikely

4. **Better Informed Decision Later**
   - Will know actual usage patterns
   - Can size backup storage accurately
   - May have budget for cloud backup ($50-200/month)

5. **Focus on Value**
   - Next sprint could focus on ML features
   - Backup is insurance, not capability
   - Users want features, not backups

---

## 📅 Proposed Timeline

### Sprint 2 (Current) - COMPLETE ✅
- ✅ Dataset versioning (semantic versions, lineage)
- ✅ MinIO lifecycle policies
- ✅ Production promotion workflow

### Sprint 3 (April 12-26, 2026) - **ML Features**
- 🎯 Model registry integration
- 🎯 Experiment tracking (link datasets to model runs)
- 🎯 Data quality validation pipeline
- 🎯 Basic analytics dashboard

### Sprint 4 (April 26 - May 10, 2026) - **Infrastructure**
- 📦 **Backup & Disaster Recovery**
  - Off-site database backups (S3/GCS)
  - MinIO replication to second site
  - Dataset export/import API
  - Automated backup testing
  - Disaster recovery runbook

### Sprint 5+ - **Production Hardening**
- Monitoring & alerting
- Performance optimization
- Security audit
- Load testing

---

## 🛠️ Interim Protection (Quick Wins)

### What to Implement NOW (< 1 hour each)

#### 1. Manual Backup Script
```bash
#!/bin/bash
# scripts/backup_database.sh

# Backup database
docker exec usm-autoimmune-postgres pg_dump \
  -U usm_db_admin usm_autoimmune_registry \
  -f /backups/$(date +%Y%m%d)_database.sql

# Compress
gzip /backups/$(date +%Y%m%d)_database.sql

# Keep last 30 days
find /backups -name "*.sql.gz" -mtime +30 -delete
```

**Effort:** 30 minutes  
**Value:** Manual disaster recovery capability

---

#### 2. MinIO Backup Verification
```python
# scripts/verify_minio_versioning.py

from minio import Minio

client = Minio('minio:9000', 'minio_admin', 'MinIO_P@ssw0rd_2026', secure=False)

for bucket in ['usm-raw', 'usm-processed', 'usm-models']:
    is_enabled = client.get_bucket_versioning(bucket)
    print(f"{bucket}: Versioning = {is_enabled.status}")
    
    # List objects with versions
    objects = client.list_objects(bucket, include_version=True)
    print(f"  Total versions: {sum(1 for _ in objects)}")
```

**Effort:** 20 minutes  
**Value:** Confirms versioning is working

---

#### 3. Documentation: Disaster Recovery Runbook
```markdown
# DISASTER_RECOVERY.md

## Database Restore

1. Stop application:
   docker-compose stop fastapi

2. Restore latest backup:
   gunzip -c /backups/latest.sql.gz | \
   docker exec -i usm-autoimmune-postgres psql \
     -U usm_db_admin -d usm_autoimmune_registry

3. Restart application:
   docker-compose start fastapi

## MinIO File Recovery

1. List deleted versions:
   mc ls --versions usm-minio/usm-raw/deleted_file.csv

2. Restore specific version:
   mc cp --version-id abc123 \
     usm-minio/usm-raw/deleted_file.csv \
     usm-minio/usm-raw/deleted_file.csv
```

**Effort:** 1 hour  
**Value:** Team can recover from disasters without you

---

#### 4. Weekly Backup Reminder (Cron Job)
```bash
# Add to crontab
0 2 * * 0 /home/shaggy/usm-autoimmune-ml-platform/scripts/backup_database.sh

# Email notification
0 2 * * 0 echo "Weekly backup completed" | mail -s "Backup Report" admin@usm.my
```

**Effort:** 15 minutes  
**Value:** Automated weekly backups with notifications

---

## ✅ Decision Matrix

| Factor | Implement Now | Defer to Sprint 3/4 |
|--------|---------------|---------------------|
| **Urgency** | Low (dev phase) | ⭐ Better fit |
| **Risk** | Low (current protection adequate) | ⭐ |
| **Cost** | High (5-14 dev days) | ⭐ Lower (focused effort) |
| **Value** | Medium (insurance) | ⭐ Higher (proven need) |
| **Team Capacity** | Low (just finished 3 features) | ⭐ Recovered |
| **User Need** | None yet (no requests) | ⭐ Will emerge |
| **Technical Debt** | Increases (more complexity) | ⭐ Planned work |

**Score:** Defer **7 / 7** ⭐⭐⭐⭐⭐⭐⭐

---

## 🎯 Final Recommendation

### **DEFER snapshot/backup to Sprint 4 (late April 2026)**

**Immediate Actions (This Week):**
1. ✅ Create manual backup script (30 min)
2. ✅ Write disaster recovery runbook (1 hour)
3. ✅ Set up weekly automated database backups (15 min)
4. ✅ Verify MinIO versioning is working (20 min)

**Total Effort:** 2 hours vs. 5-14 days for full implementation

**Sprint 3 Focus Instead:**
- ML experiment tracking
- Data quality validation
- User-facing features
- Validate current versioning system with real usage

**Sprint 4 (When to Implement):**
- After validating versioning system works
- After identifying actual backup requirements from users
- When approaching 1,000+ datasets
- When regulatory compliance deadline approaches

---

## 📝 Approval & Sign-off

**Recommendation:** Defer to Sprint 4  
**Interim Protection:** Manual scripts + weekly backups  
**Risk Assessment:** Acceptable for current phase  
**Review Date:** April 26, 2026 (Sprint 4 planning)

**Decision Maker:** _______________ Date: ___________

---

**Document Version:** 1.0  
**Last Updated:** April 5, 2026  
**Next Review:** Sprint 4 Planning (April 26, 2026)
