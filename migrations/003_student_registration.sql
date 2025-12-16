-- Migration: 004_student_registration
-- Created: 2025-12-10
-- Description: Add student registration support with ID generation

-- This migration adds:
-- 1. school_number column to schools table for student ID generation
-- 2. major_number column to majors table for student ID generation
-- 3. student_number_tracking table to track last student number per school+major combination
-- 4. stored_password column to students table for password display functionality

-- ============================================================================
-- EXTEND SCHOOLS TABLE
-- ============================================================================

-- Add school_number column (3-digit identifier for student ID generation)
ALTER TABLE schools ADD COLUMN IF NOT EXISTS school_number CHAR(3) UNIQUE;

-- ============================================================================
-- EXTEND MAJORS TABLE
-- ============================================================================

-- Add major_number column (4-digit identifier for student ID generation)
ALTER TABLE majors ADD COLUMN IF NOT EXISTS major_number CHAR(4) UNIQUE;

-- ============================================================================
-- CREATE STUDENT NUMBER TRACKING TABLE
-- ============================================================================

-- Table to track the last student number for each school+major combination
-- This enables generating sequential student IDs like: 001000100001, 001000100002, etc.
CREATE TABLE IF NOT EXISTS student_number_tracking (
    id BIGSERIAL PRIMARY KEY,
    school_id BIGINT NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    major_id BIGINT NOT NULL REFERENCES majors(id) ON DELETE CASCADE,
    last_student_number INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(school_id, major_id)
);

-- Index for efficient lookups
CREATE INDEX IF NOT EXISTS idx_student_number_tracking_school_major 
    ON student_number_tracking(school_id, major_id);

-- ============================================================================
-- EXTEND STUDENTS TABLE
-- ============================================================================

-- Add stored_password column to students table for password display functionality
-- This stores the hashed password for admin/teacher retrieval
-- Note: The actual authentication password is stored in auth.users (managed by Supabase)
ALTER TABLE students ADD COLUMN IF NOT EXISTS stored_password TEXT;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Apply updated_at trigger to student_number_tracking
DROP TRIGGER IF EXISTS set_student_number_tracking_updated_at ON student_number_tracking;
CREATE TRIGGER set_student_number_tracking_updated_at
    BEFORE UPDATE ON student_number_tracking
    FOR EACH ROW
    EXECUTE FUNCTION handle_updated_at();

-- ============================================================================
-- PERMISSIONS
-- ============================================================================

-- Grant permissions for the new table
GRANT ALL ON public.student_number_tracking TO authenticated, anon, service_role;
GRANT USAGE, SELECT ON SEQUENCE student_number_tracking_id_seq TO authenticated, anon, service_role, supabase_auth_admin;

-- ============================================================================
-- FUNCTION: Get next student number atomically
-- ============================================================================

-- Function to atomically get and increment the student number for a school+major combination
CREATE OR REPLACE FUNCTION get_next_student_number(p_school_id BIGINT, p_major_id BIGINT)
RETURNS INT
LANGUAGE plpgsql
AS $$
DECLARE
    v_next_number INT;
BEGIN
    -- Insert or update the tracking record and return the new number
    INSERT INTO student_number_tracking (school_id, major_id, last_student_number)
    VALUES (p_school_id, p_major_id, 1)
    ON CONFLICT (school_id, major_id)
    DO UPDATE SET 
        last_student_number = student_number_tracking.last_student_number + 1,
        updated_at = now()
    RETURNING last_student_number INTO v_next_number;
    
    RETURN v_next_number;
END;
$$;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION get_next_student_number(BIGINT, BIGINT) TO authenticated, anon, service_role;

-- ============================================================================
-- FUNCTION: Assign school number
-- ============================================================================

-- Function to assign the next available school number to a school
CREATE OR REPLACE FUNCTION assign_school_number(p_school_id BIGINT)
RETURNS CHAR(3)
LANGUAGE plpgsql
AS $$
DECLARE
    v_current_number CHAR(3);
    v_max_number INT;
    v_new_number CHAR(3);
BEGIN
    -- Check if school already has a number
    SELECT school_number INTO v_current_number
    FROM schools
    WHERE id = p_school_id;
    
    IF v_current_number IS NOT NULL THEN
        RETURN v_current_number;
    END IF;
    
    -- Get the maximum existing number
    SELECT COALESCE(MAX(CAST(school_number AS INT)), 0) INTO v_max_number
    FROM schools
    WHERE school_number IS NOT NULL;
    
    -- Assign next number (padded to 3 digits)
    v_new_number := LPAD((v_max_number + 1)::TEXT, 3, '0');
    
    UPDATE schools
    SET school_number = v_new_number
    WHERE id = p_school_id;
    
    RETURN v_new_number;
END;
$$;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION assign_school_number(BIGINT) TO authenticated, anon, service_role;

-- ============================================================================
-- FUNCTION: Assign major number
-- ============================================================================

-- Function to assign the next available major number to a major
CREATE OR REPLACE FUNCTION assign_major_number(p_major_id BIGINT)
RETURNS CHAR(4)
LANGUAGE plpgsql
AS $$
DECLARE
    v_current_number CHAR(4);
    v_max_number INT;
    v_new_number CHAR(4);
BEGIN
    -- Check if major already has a number
    SELECT major_number INTO v_current_number
    FROM majors
    WHERE id = p_major_id;
    
    IF v_current_number IS NOT NULL THEN
        RETURN v_current_number;
    END IF;
    
    -- Get the maximum existing number
    SELECT COALESCE(MAX(CAST(major_number AS INT)), 0) INTO v_max_number
    FROM majors
    WHERE major_number IS NOT NULL;
    
    -- Assign next number (padded to 4 digits)
    v_new_number := LPAD((v_max_number + 1)::TEXT, 4, '0');
    
    UPDATE majors
    SET major_number = v_new_number
    WHERE id = p_major_id;
    
    RETURN v_new_number;
END;
$$;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION assign_major_number(BIGINT) TO authenticated, anon, service_role;
