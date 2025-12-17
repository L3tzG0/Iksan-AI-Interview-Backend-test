-- Rollback: remove type column from sessions
ALTER TABLE sessions DROP CONSTRAINT IF EXISTS sessions_type_check;
ALTER TABLE sessions DROP COLUMN IF EXISTS type;
