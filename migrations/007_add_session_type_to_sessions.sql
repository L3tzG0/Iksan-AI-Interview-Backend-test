-- Migration: 007_add_session_type_to_sessions
-- Created: 2025-12-17
-- Description: Add type column to sessions to distinguish job vs university sessions

ALTER TABLE sessions ADD COLUMN IF NOT EXISTS type TEXT;

-- Backfill existing rows to default type
UPDATE sessions SET type = 'job' WHERE type IS NULL;

-- Set default for new rows
ALTER TABLE sessions ALTER COLUMN type SET DEFAULT 'job';

-- Enforce allowed values
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'sessions_type_check'
    ) THEN
        ALTER TABLE sessions
        ADD CONSTRAINT sessions_type_check CHECK (type IN ('job', 'university'));
    END IF;
END$$;

-- Require value
ALTER TABLE sessions ALTER COLUMN type SET NOT NULL;
