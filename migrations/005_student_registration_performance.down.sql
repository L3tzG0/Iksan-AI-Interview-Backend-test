-- Migration Downgrade: 005_student_registration_performance
-- Created: 2025-12-12
-- Description: Roll back concurrency-safe numbering and lookup indexes

-- WARNING: This downgrade restores the previous MAX()+1 numbering functions,
-- which are not safe under high concurrency.

-- ============================================================================
-- DROP PERFORMANCE / UNIQUENESS INDEXES
-- ============================================================================

DROP INDEX IF EXISTS public.idx_classes_class_name_trgm;
DROP INDEX IF EXISTS public.idx_majors_major_name_trgm;
DROP INDEX IF EXISTS public.idx_schools_school_name_trgm;

DROP INDEX IF EXISTS public.uq_classes_class_name_grade_lower;
DROP INDEX IF EXISTS public.uq_majors_major_name_lower;
DROP INDEX IF EXISTS public.uq_schools_school_name_lower;

-- ============================================================================
-- DROP SEQUENCES
-- ============================================================================

DROP SEQUENCE IF EXISTS public.majors_major_number_seq;
DROP SEQUENCE IF EXISTS public.schools_school_number_seq;

-- ============================================================================
-- RESTORE ORIGINAL FUNCTIONS (MAX()+1 approach from migration 003)
-- ============================================================================

CREATE OR REPLACE FUNCTION public.assign_school_number(p_school_id BIGINT)
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
    FROM public.schools
    WHERE id = p_school_id;

    IF v_current_number IS NOT NULL THEN
        RETURN v_current_number;
    END IF;

    -- Get the maximum existing number
    SELECT COALESCE(MAX(CAST(school_number AS INT)), 0) INTO v_max_number
    FROM public.schools
    WHERE school_number IS NOT NULL;

    -- Assign next number (padded to 3 digits)
    v_new_number := LPAD((v_max_number + 1)::TEXT, 3, '0');

    UPDATE public.schools
    SET school_number = v_new_number
    WHERE id = p_school_id;

    RETURN v_new_number;
END;
$$;

CREATE OR REPLACE FUNCTION public.assign_major_number(p_major_id BIGINT)
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
    FROM public.majors
    WHERE id = p_major_id;

    IF v_current_number IS NOT NULL THEN
        RETURN v_current_number;
    END IF;

    -- Get the maximum existing number
    SELECT COALESCE(MAX(CAST(major_number AS INT)), 0) INTO v_max_number
    FROM public.majors
    WHERE major_number IS NOT NULL;

    -- Assign next number (padded to 4 digits)
    v_new_number := LPAD((v_max_number + 1)::TEXT, 4, '0');

    UPDATE public.majors
    SET major_number = v_new_number
    WHERE id = p_major_id;

    RETURN v_new_number;
END;
$$;

GRANT EXECUTE ON FUNCTION public.assign_school_number(BIGINT) TO authenticated, anon, service_role;
GRANT EXECUTE ON FUNCTION public.assign_major_number(BIGINT) TO authenticated, anon, service_role;
