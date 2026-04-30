-- ============================================
-- Database Migration: Security & Compliance Features
-- Sprint 3 - Production Readiness
-- ============================================

-- 1. API Key Management Table
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    key_hash VARCHAR(64) UNIQUE NOT NULL,
    key_prefix VARCHAR(12) NOT NULL,
    created_by INTEGER NOT NULL REFERENCES users(id),
    role VARCHAR(20) DEFAULT 'viewer',
    scopes TEXT,
    rate_limit INTEGER DEFAULT 1000,
    is_active BOOLEAN DEFAULT TRUE,
    is_revoked BOOLEAN DEFAULT FALSE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    usage_count INTEGER DEFAULT 0,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    revoked_at TIMESTAMP WITH TIME ZONE,
    revoked_by INTEGER REFERENCES users(id),
    revocation_reason TEXT
);

CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_prefix ON api_keys(key_prefix);
CREATE INDEX IF NOT EXISTS idx_api_keys_created_by ON api_keys(created_by);

-- 2. Audit Log Table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    username VARCHAR(100),
    user_role VARCHAR(20),
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    endpoint VARCHAR(200),
    http_method VARCHAR(10),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(100),
    description TEXT,
    request_payload JSONB,
    response_status INTEGER,
    response_time_ms INTEGER,
    changes JSONB,
    data_accessed JSONB,
    is_sensitive BOOLEAN DEFAULT FALSE,
    is_suspicious BOOLEAN DEFAULT FALSE,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT
);

-- Audit Log Indexes
CREATE INDEX IF NOT EXISTS idx_audit_user_timestamp ON audit_logs(user_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_action_timestamp ON audit_logs(action, timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_ip_timestamp ON audit_logs(ip_address, timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp DESC);

-- 3. Data Access Log Table (PDPA/GDPR Compliance)
CREATE TABLE IF NOT EXISTS data_access_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    username VARCHAR(100) NOT NULL,
    user_role VARCHAR(20),
    patient_id INTEGER REFERENCES patients(id),
    patient_anonymous_id VARCHAR(50),
    fields_accessed JSONB,
    access_purpose VARCHAR(100),
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    endpoint VARCHAR(200),
    justification TEXT,
    consent_verified BOOLEAN DEFAULT FALSE,
    ethics_clearance_id VARCHAR(50)
);

-- Data Access Log Indexes
CREATE INDEX IF NOT EXISTS idx_data_access_patient_time ON data_access_logs(patient_id, accessed_at);
CREATE INDEX IF NOT EXISTS idx_data_access_user_time ON data_access_logs(user_id, accessed_at);
CREATE INDEX IF NOT EXISTS idx_data_access_accessed_at ON data_access_logs(accessed_at DESC);

-- ============================================
-- Summary and Validation
-- ============================================

-- Count new tables
SELECT 
    tablename,
    schemaname
FROM pg_tables 
WHERE tablename IN ('api_keys', 'audit_logs', 'data_access_logs')
ORDER BY tablename;

-- Show indexes
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename IN ('api_keys', 'audit_logs', 'data_access_logs')
ORDER BY tablename, indexname;

-- Grant permissions (if needed)
GRANT SELECT, INSERT, UPDATE, DELETE ON api_keys TO usm_db_admin;
GRANT SELECT, INSERT ON audit_logs TO usm_db_admin;
GRANT SELECT, INSERT ON data_access_logs TO usm_db_admin;

GRANT USAGE, SELECT ON SEQUENCE api_keys_id_seq TO usm_db_admin;
GRANT USAGE, SELECT ON SEQUENCE audit_logs_id_seq TO usm_db_admin;
GRANT USAGE, SELECT ON SEQUENCE data_access_logs_id_seq TO usm_db_admin;

-- ============================================
-- Verification Queries
-- ============================================

-- Verify tables exist
SELECT 
    table_name,
    (SELECT count(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
  AND table_name IN ('api_keys', 'audit_logs', 'data_access_logs')
ORDER BY table_name;

-- Show sample structure
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name IN ('api_keys', 'audit_logs', 'data_access_logs')
ORDER BY table_name, ordinal_position;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '======================================';
    RAISE NOTICE 'Security & Compliance Migration Complete!';
    RAISE NOTICE '======================================';
    RAISE NOTICE 'Created tables:';
    RAISE NOTICE '  • api_keys (API key management)';
    RAISE NOTICE '  • audit_logs (comprehensive audit trail)';
    RAISE NOTICE '  • data_access_logs (PDPA/GDPR compliance)';
    RAISE NOTICE '';
    RAISE NOTICE 'Security features enabled:';
    RAISE NOTICE '  ✅ API key management';
    RAISE NOTICE '  ✅ Rate limiting';
    RAISE NOTICE '  ✅ Audit logging';
    RAISE NOTICE '  ✅ Data access tracking';
    RAISE NOTICE '======================================';
END $$;
