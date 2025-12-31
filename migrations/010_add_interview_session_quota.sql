-- Migration: 010_add_interview_session_quota
-- Created: 2025-12-30
-- Description: Add interview_session_quota to students with default of 2 and non-negative check

-- =========================================================================
-- ADD COLUMN
-- =========================================================================
ALTER TABLE students
    ADD COLUMN IF NOT EXISTS interview_session_quota INTEGER;

-- =========================================================================
-- BACKFILL EXISTING ROWS
-- =========================================================================
UPDATE students
SET interview_session_quota = 2
WHERE interview_session_quota IS NULL;

-- =========================================================================
-- SET DEFAULT AND CONSTRAINTS
-- =========================================================================
ALTER TABLE students
    ALTER COLUMN interview_session_quota SET DEFAULT 2,
    ALTER COLUMN interview_session_quota SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'students_interview_session_quota_check'
    ) THEN
        ALTER TABLE students
        ADD CONSTRAINT students_interview_session_quota_check
        CHECK (interview_session_quota >= 0);
    END IF;
END$$;

-- =========================================================================
-- COMMENTS
-- =========================================================================
COMMENT ON COLUMN students.interview_session_quota IS 'Remaining interview sessions a student can initiate (non-negative).';
