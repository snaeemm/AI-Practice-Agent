-- Add authentication fields to rfp_users table
-- Reports/RFPs are shared across all users
-- Sessions are independent per user

ALTER TABLE rfp_users
ADD COLUMN IF NOT EXISTS password_hash TEXT NOT NULL DEFAULT '',
ADD COLUMN IF NOT EXISTS full_name TEXT,
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true,
ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN DEFAULT true;

CREATE INDEX IF NOT EXISTS idx_rfp_users_is_active ON rfp_users(is_active);

COMMENT ON COLUMN rfp_users.password_hash IS 'Bcrypt hashed password';
COMMENT ON COLUMN rfp_users.must_change_password IS 'Force password change on first login';
COMMENT ON TABLE rfp_users IS 'User accounts with authentication. Each user has independent sessions but shares access to all RFPs/reports';
