-- Update User Roles for RBAC System
-- Run this SQL script on the database to update existing users

-- Update existing users to use new role system
-- Old roles: 'user', 'doctor', 'admin'
-- New roles: 'admin', 'researcher', 'viewer'

-- Convert 'user' -> 'researcher' (most common role)
UPDATE users 
SET role = 'researcher' 
WHERE role = 'user' OR role IS NULL;

-- Convert 'doctor' -> 'researcher' (doctors are researchers)
UPDATE users 
SET role = 'researcher' 
WHERE role = 'doctor';

-- Keep 'admin' as 'admin'
UPDATE users 
SET role = 'admin' 
WHERE role = 'admin' OR is_superuser = true;

-- Verify results
SELECT role, COUNT(*) as count 
FROM users 
GROUP BY role 
ORDER BY role;

-- Optional: Set first user as admin if no admin exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM users WHERE role = 'admin') THEN
        UPDATE users
        SET role = 'admin'
        WHERE id = (SELECT MIN(id) FROM users);    
        RAISE NOTICE 'Set user ID % as admin', (SELECT MIN(id) FROM users);
    END IF;
END $$;
