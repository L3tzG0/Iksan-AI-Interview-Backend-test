-- Migration: 006_student_registration_rpc_optimizations
-- Created: 2025-12-12
-- Description: Reduce round-trips for student registration via RPC helpers

-- Adds RPC functions that:
-- - Resolve existing rows by case-insensitive name
-- - Create rows if missing (with concurrency-safe retry on unique violation)
-- - Ensure school_number / major_number are assigned
--
-- This allows the API to replace multiple PostgREST calls with a single RPC.

-- ============================================================================
-- SCHOOL RESOLVE/CREATE
-- ============================================================================

CREATE OR REPLACE FUNCTION public.resolve_or_create_school(p_school_name TEXT)
RETURNS TABLE (school_id BIGINT, school_number CHAR(3))
LANGUAGE plpgsql
AS $$
DECLARE
    v_school_id BIGINT;
    v_school_number CHAR(3);
BEGIN
    IF p_school_name IS NULL OR length(trim(p_school_name)) = 0 THEN
        RAISE EXCEPTION 'School name cannot be empty.';
    END IF;

    SELECT s.id, s.school_number
      INTO v_school_id, v_school_number
      FROM public.schools s
     WHERE lower(s.school_name) = lower(p_school_name)
     LIMIT 1;

    IF v_school_id IS NULL THEN
        BEGIN
            INSERT INTO public.schools (school_name)
            VALUES (p_school_name)
            RETURNING id, school_number INTO v_school_id, v_school_number;
        EXCEPTION
            WHEN unique_violation THEN
                SELECT s.id, s.school_number
                  INTO v_school_id, v_school_number
                  FROM public.schools s
                 WHERE lower(s.school_name) = lower(p_school_name)
                 LIMIT 1;
        END;
    END IF;

    IF v_school_id IS NULL THEN
        RAISE EXCEPTION 'Failed to resolve or create school for name=%', p_school_name;
    END IF;

    IF v_school_number IS NULL THEN
        v_school_number := public.assign_school_number(v_school_id);
    END IF;

    RETURN QUERY SELECT v_school_id, v_school_number;
END;
$$;

GRANT EXECUTE ON FUNCTION public.resolve_or_create_school(TEXT) TO authenticated, anon, service_role;

-- ============================================================================
-- MAJOR RESOLVE/CREATE
-- ============================================================================

CREATE OR REPLACE FUNCTION public.resolve_or_create_major(p_major_name TEXT)
RETURNS TABLE (major_id BIGINT, major_number CHAR(4))
LANGUAGE plpgsql
AS $$
DECLARE
    v_major_id BIGINT;
    v_major_number CHAR(4);
BEGIN
    IF p_major_name IS NULL OR length(trim(p_major_name)) = 0 THEN
        RAISE EXCEPTION 'Major name cannot be empty.';
    END IF;

    SELECT m.id, m.major_number
      INTO v_major_id, v_major_number
      FROM public.majors m
     WHERE lower(m.major_name) = lower(p_major_name)
     LIMIT 1;

    IF v_major_id IS NULL THEN
        BEGIN
            INSERT INTO public.majors (major_name)
            VALUES (p_major_name)
            RETURNING id, major_number INTO v_major_id, v_major_number;
        EXCEPTION
            WHEN unique_violation THEN
                SELECT m.id, m.major_number
                  INTO v_major_id, v_major_number
                  FROM public.majors m
                 WHERE lower(m.major_name) = lower(p_major_name)
                 LIMIT 1;
        END;
    END IF;

    IF v_major_id IS NULL THEN
        RAISE EXCEPTION 'Failed to resolve or create major for name=%', p_major_name;
    END IF;

    IF v_major_number IS NULL THEN
        v_major_number := public.assign_major_number(v_major_id);
    END IF;

    RETURN QUERY SELECT v_major_id, v_major_number;
END;
$$;

GRANT EXECUTE ON FUNCTION public.resolve_or_create_major(TEXT) TO authenticated, anon, service_role;

-- ============================================================================
-- CLASS RESOLVE/CREATE
-- ============================================================================

CREATE OR REPLACE FUNCTION public.resolve_or_create_class(
    p_class_name TEXT,
    p_grade_level INTEGER
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_class_id BIGINT;
BEGIN
    IF p_class_name IS NULL OR length(trim(p_class_name)) = 0 THEN
        RAISE EXCEPTION 'Class name cannot be empty.';
    END IF;

    IF p_grade_level IS NULL OR p_grade_level NOT IN (1,2,3) THEN
        RAISE EXCEPTION 'grade_level must be 1, 2, or 3.';
    END IF;

    SELECT c.id
      INTO v_class_id
      FROM public.classes c
     WHERE lower(c.class_name) = lower(p_class_name)
       AND c.grade_level = p_grade_level
     LIMIT 1;

    IF v_class_id IS NULL THEN
        BEGIN
            INSERT INTO public.classes (class_name, grade_level)
            VALUES (p_class_name, p_grade_level)
            RETURNING id INTO v_class_id;
        EXCEPTION
            WHEN unique_violation THEN
                SELECT c.id
                  INTO v_class_id
                  FROM public.classes c
                 WHERE lower(c.class_name) = lower(p_class_name)
                   AND c.grade_level = p_grade_level
                 LIMIT 1;
        END;
    END IF;

    IF v_class_id IS NULL THEN
        RAISE EXCEPTION 'Failed to resolve or create class for name=% grade=%', p_class_name, p_grade_level;
    END IF;

    RETURN v_class_id;
END;
$$;

GRANT EXECUTE ON FUNCTION public.resolve_or_create_class(TEXT, INTEGER) TO authenticated, anon, service_role;
