-- Migration: 005_student_registration_performance
-- Created: 2025-12-12
-- Description: Concurrency-safe numbering and faster case-insensitive lookups

-- Goals
-- 1) Make school_number / major_number assignment safe under high concurrency
--    (remove MAX()+1 race + full scans) by using sequences.
-- 2) Prevent duplicate reference data differing only by case/spacing assumptions
--    via case-insensitive unique indexes.
-- 3) Speed up existing ILIKE lookups (used by the API) via pg_trgm GIN indexes.

-- NOTE: This migration is intended to be run in Supabase SQL Editor.

-- ============================================================================
-- EXTENSIONS
-- ============================================================================

-- Trigram indexes greatly improve ILIKE performance at scale.
CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA extensions;

-- ============================================================================
-- PRECHECKS (fail fast if duplicates would break new uniqueness rules)
-- ============================================================================

DO $$
BEGIN
    -- Schools: case-insensitive duplicates
    IF EXISTS (
        SELECT 1
        FROM public.schools
        GROUP BY lower(school_name)
        HAVING COUNT(*) > 1
    ) THEN
        RAISE EXCEPTION 'Cannot apply migration 005: schools contains case-insensitive duplicates (same name, different case). Deduplicate first.';
    END IF;

    -- Majors: case-insensitive duplicates
    IF EXISTS (
        SELECT 1
        FROM public.majors
        GROUP BY lower(major_name)
        HAVING COUNT(*) > 1
    ) THEN
        RAISE EXCEPTION 'Cannot apply migration 005: majors contains case-insensitive duplicates (same name, different case). Deduplicate first.';
    END IF;

    -- Classes: duplicates by (name, grade) ignoring case
    IF EXISTS (
        SELECT 1
        FROM public.classes
        GROUP BY lower(class_name), grade_level
        HAVING COUNT(*) > 1
    ) THEN
        RAISE EXCEPTION 'Cannot apply migration 005: classes contains case-insensitive duplicates for (class_name, grade_level). Deduplicate first.';
    END IF;
END $$;

-- ============================================================================
-- CASE-INSENSITIVE UNIQUENESS
-- ============================================================================

-- These prevent duplicates like "IKSAN HS" vs "Iksan HS".
-- They also make lookups deterministic (the app currently takes the first match).

CREATE UNIQUE INDEX IF NOT EXISTS uq_schools_school_name_lower
    ON public.schools (lower(school_name));

CREATE UNIQUE INDEX IF NOT EXISTS uq_majors_major_name_lower
    ON public.majors (lower(major_name));

CREATE UNIQUE INDEX IF NOT EXISTS uq_classes_class_name_grade_lower
    ON public.classes (lower(class_name), grade_level);

-- ============================================================================
-- ILIKE PERFORMANCE INDEXES
-- ============================================================================

-- The API uses ILIKE for case-insensitive matching. Trigram GIN indexes
-- make those queries scale much better as reference tables grow.

CREATE INDEX IF NOT EXISTS idx_schools_school_name_trgm
    ON public.schools USING gin (school_name gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_majors_major_name_trgm
    ON public.majors USING gin (major_name gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_classes_class_name_trgm
    ON public.classes USING gin (class_name gin_trgm_ops);

-- ============================================================================
-- CONCURRENCY-SAFE NUMBERING VIA SEQUENCES
-- ============================================================================

-- Schools: 3-digit school_number (001..999)
DO $$
DECLARE
    v_max_school_num int;
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE c.relkind = 'S'
          AND n.nspname = 'public'
          AND c.relname = 'schools_school_number_seq'
    ) THEN
        CREATE SEQUENCE public.schools_school_number_seq;
    END IF;

    SELECT COALESCE(MAX(CAST(school_number AS int)), 0)
      INTO v_max_school_num
      FROM public.schools
     WHERE school_number IS NOT NULL;

    -- Ensure nextval() will produce v_max+1
    PERFORM setval('public.schools_school_number_seq', v_max_school_num, true);
END $$;

-- Majors: 4-digit major_number (0001..9999)
DO $$
DECLARE
    v_max_major_num int;
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE c.relkind = 'S'
          AND n.nspname = 'public'
          AND c.relname = 'majors_major_number_seq'
    ) THEN
        CREATE SEQUENCE public.majors_major_number_seq;
    END IF;

    SELECT COALESCE(MAX(CAST(major_number AS int)), 0)
      INTO v_max_major_num
      FROM public.majors
     WHERE major_number IS NOT NULL;

    PERFORM setval('public.majors_major_number_seq', v_max_major_num, true);
END $$;

-- Replace functions to use sequences (removes MAX()+1 races)

CREATE OR REPLACE FUNCTION public.assign_school_number(p_school_id BIGINT)
RETURNS CHAR(3)
LANGUAGE plpgsql
AS $$
DECLARE
    v_assigned CHAR(3);
    v_next int;
BEGIN
    -- If already assigned, return it.
    SELECT school_number INTO v_assigned
      FROM public.schools
     WHERE id = p_school_id;

    IF v_assigned IS NOT NULL THEN
        RETURN v_assigned;
    END IF;

    -- Generate next value from sequence (unique under concurrency).
    v_next := nextval('public.schools_school_number_seq');
    v_assigned := LPAD(v_next::text, 3, '0');

    -- Assign only if still NULL; if another session won the race, return the stored value.
    UPDATE public.schools
       SET school_number = v_assigned
     WHERE id = p_school_id
       AND school_number IS NULL;

    SELECT school_number INTO v_assigned
      FROM public.schools
     WHERE id = p_school_id;

    IF v_assigned IS NULL THEN
        RAISE EXCEPTION 'Failed to assign school_number for school_id=%', p_school_id;
    END IF;

    RETURN v_assigned;
END;
$$;

CREATE OR REPLACE FUNCTION public.assign_major_number(p_major_id BIGINT)
RETURNS CHAR(4)
LANGUAGE plpgsql
AS $$
DECLARE
    v_assigned CHAR(4);
    v_next int;
BEGIN
    SELECT major_number INTO v_assigned
      FROM public.majors
     WHERE id = p_major_id;

    IF v_assigned IS NOT NULL THEN
        RETURN v_assigned;
    END IF;

    v_next := nextval('public.majors_major_number_seq');
    v_assigned := LPAD(v_next::text, 4, '0');

    UPDATE public.majors
       SET major_number = v_assigned
     WHERE id = p_major_id
       AND major_number IS NULL;

    SELECT major_number INTO v_assigned
      FROM public.majors
     WHERE id = p_major_id;

    IF v_assigned IS NULL THEN
        RAISE EXCEPTION 'Failed to assign major_number for major_id=%', p_major_id;
    END IF;

    RETURN v_assigned;
END;
$$;

-- Ensure execute permissions remain.
GRANT EXECUTE ON FUNCTION public.assign_school_number(BIGINT) TO authenticated, anon, service_role;
GRANT EXECUTE ON FUNCTION public.assign_major_number(BIGINT) TO authenticated, anon, service_role;
