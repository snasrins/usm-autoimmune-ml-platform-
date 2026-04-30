-- ============================================
-- SHOW ALL USERS FOR SIT TESTING
-- ============================================

-- Show all existing users
SELECT id, username, email, role, is_active, created_at 
FROM users 
ORDER BY id;

-- ============================================
-- CREATE VIEWER USER IF NOT EXISTS
-- ============================================

-- Check if viewer1 already exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM users WHERE username = 'viewer1') THEN
        -- Create viewer user
        INSERT INTO users (username, email, full_name, role, hashed_password, is_active, created_at, updated_at)
        VALUES (
            'viewer1',
            'viewer1@usm.my',
            'Viewer User 1',
            'viewer',
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyB9veFxPYbO',  -- Password: test123
            true,
            NOW(),
            NOW()
        );
        RAISE NOTICE 'Created viewer user: viewer1 (password: test123)';
    ELSE
        RAISE NOTICE 'User viewer1 already exists';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM users WHERE username = 'researcher1') THEN
        -- Create researcher user
        INSERT INTO users (username, email, full_name, role, hashed_password, is_active, created_at, updated_at)
        VALUES (
            'researcher1',
            'researcher1@usm.my',
            'Researcher User 1',
            'researcher',
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyB9veFxPYbO',  -- Password: test123
            true,
            NOW(),
            NOW()
        );
        RAISE NOTICE 'Created researcher user: researcher1 (password: test123)';
    ELSE
        RAISE NOTICE 'User researcher1 already exists';
    END IF;
END $$;

-- Show all users after creation
SELECT 
    id, 
    username, 
    email, 
    role, 
    is_active,
    created_at
FROM users 
ORDER BY role, id;

-- ============================================
-- SUMMARY FOR SIT TESTING
-- ============================================
SELECT 
    role,
    COUNT(*) as user_count,
    STRING_AGG(username, ', ' ORDER BY username) as usernames
FROM users
WHERE is_active = true
GROUP BY role
ORDER BY 
    CASE role
        WHEN 'admin' THEN 1
        WHEN 'researcher' THEN 2
        WHEN 'viewer' THEN 3
    END;
