-- Migration: 004_student_registration (DOWN)
-- Created: 2025-12-10
-- Description: Rollback student registration support

-- ============================================================================
-- DROP FUNCTIONS
-- ============================================================================

DROP FUNCTION IF EXISTS assign_major_number(BIGINT);
DROP FUNCTION IF EXISTS assign_school_number(BIGINT);
DROP FUNCTION IF EXISTS get_next_student_number(BIGINT, BIGINT);

-- ============================================================================
-- DROP TRIGGER
-- ============================================================================

DROP TRIGGER IF EXISTS set_student_number_tracking_updated_at ON student_number_tracking;

-- ============================================================================
-- DROP STUDENT NUMBER TRACKING TABLE
-- ============================================================================

DROP TABLE IF EXISTS student_number_tracking;

-- ============================================================================
-- REMOVE COLUMNS FROM STUDENTS TABLE
-- ============================================================================

ALTER TABLE students DROP COLUMN IF EXISTS stored_password;

-- ============================================================================
-- REMOVE COLUMNS FROM MAJORS TABLE
-- ============================================================================

ALTER TABLE majors DROP COLUMN IF EXISTS major_number;

-- ============================================================================
-- REMOVE COLUMNS FROM SCHOOLS TABLE
-- ============================================================================

ALTER TABLE schools DROP COLUMN IF EXISTS school_number;
