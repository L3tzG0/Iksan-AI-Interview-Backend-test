-- Rollback: 010_add_interview_session_quota
-- Created: 2025-12-30
-- Description: Remove interview_session_quota from students

-- =========================================================================
-- DROP CONSTRAINTS AND DEFAULT
-- =========================================================================
ALTER TABLE students
    DROP CONSTRAINT IF EXISTS students_interview_session_quota_check;

ALTER TABLE students
    ALTER COLUMN interview_session_quota DROP DEFAULT;

-- =========================================================================
-- DROP COLUMN
-- =========================================================================
ALTER TABLE students
    DROP COLUMN IF EXISTS interview_session_quota;
