"""add_rpc_functions

Revision ID: c8f5a2b9d1e3
Revises: 4bd5344f0305
Create Date: 2026-01-08 15:30:00.000000

Description: Add PostgreSQL stored procedures (RPC functions) for:
- Student registration operations (resolve_or_create_school, resolve_or_create_major, resolve_or_create_class)
- Number assignment operations (assign_school_number, assign_major_number)
- Email domain validation (is_email_domain_allowed)

These functions were originally defined in:
- 005_student_registration_performance.sql (sequences and assign_*_number)
- 006_student_registration_rpc_optimizations.sql (resolve_or_create_*)
- 008_email_domain_restrictions.sql (is_email_domain_allowed)
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'c8f5a2b9d1e3'
down_revision: Union[str, None] = '4bd5344f0305'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create sequences and RPC functions for student registration."""
    conn = op.get_bind()
    
    # =========================================================================
    # SEQUENCES for school/major number assignment
    # =========================================================================
    
    # Create schools_school_number_seq if not exists
    conn.execute(text("""
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

            IF v_max_school_num < 1 THEN
                PERFORM setval('public.schools_school_number_seq', 1, false);
            ELSE
                PERFORM setval('public.schools_school_number_seq', v_max_school_num, true);
            END IF;
        END $$;
    """))
    
    # Create majors_major_number_seq if not exists
    conn.execute(text("""
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

            IF v_max_major_num < 1 THEN
                PERFORM setval('public.majors_major_number_seq', 1, false);
            ELSE
                PERFORM setval('public.majors_major_number_seq', v_max_major_num, true);
            END IF;
        END $$;
    """))
    
    # =========================================================================
    # FUNCTION: assign_school_number
    # Assigns a unique 3-digit number to a school
    # =========================================================================
    
    conn.execute(text("""
        CREATE OR REPLACE FUNCTION public.assign_school_number(p_school_id BIGINT)
        RETURNS CHAR(3)
        LANGUAGE plpgsql
        AS $$
        DECLARE
            v_assigned CHAR(3);
            v_next int;
        BEGIN
            SELECT school_number INTO v_assigned
              FROM public.schools
             WHERE id = p_school_id;

            IF v_assigned IS NOT NULL THEN
                RETURN v_assigned;
            END IF;

            v_next := nextval('public.schools_school_number_seq');
            v_assigned := LPAD(v_next::text, 3, '0');

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
    """))
    
    # =========================================================================
    # FUNCTION: assign_major_number
    # Assigns a unique 4-digit number to a major
    # =========================================================================
    
    conn.execute(text("""
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
    """))
    
    # =========================================================================
    # FUNCTION: resolve_or_create_school
    # Atomically resolves existing school or creates new one
    # =========================================================================
    
    conn.execute(text("""
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
                    RETURNING id, schools.school_number INTO v_school_id, v_school_number;
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
    """))
    
    # =========================================================================
    # FUNCTION: resolve_or_create_major
    # Atomically resolves existing major or creates new one
    # =========================================================================
    
    conn.execute(text("""
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
                    RETURNING id, majors.major_number INTO v_major_id, v_major_number;
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
    """))
    
    # =========================================================================
    # FUNCTION: resolve_or_create_class
    # Atomically resolves existing class or creates new one
    # =========================================================================
    
    conn.execute(text("""
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
    """))
    
    # =========================================================================
    # FUNCTION: is_email_domain_allowed
    # Checks if an email domain is in the allowed list
    # =========================================================================
    
    conn.execute(text("""
        CREATE OR REPLACE FUNCTION public.is_email_domain_allowed(email TEXT)
        RETURNS BOOLEAN AS $$
        DECLARE
            email_domain TEXT;
            is_allowed BOOLEAN;
        BEGIN
            email_domain := lower(split_part(email, '@', 2));
            
            SELECT EXISTS(
                SELECT 1 
                FROM allowed_email_domains 
                WHERE domain = email_domain 
                AND is_active = true
            ) INTO is_allowed;
            
            RETURN is_allowed;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """))


def downgrade() -> None:
    """Drop all RPC functions and sequences."""
    conn = op.get_bind()
    
    # Drop functions
    conn.execute(text("DROP FUNCTION IF EXISTS public.is_email_domain_allowed(TEXT);"))
    conn.execute(text("DROP FUNCTION IF EXISTS public.resolve_or_create_class(TEXT, INTEGER);"))
    conn.execute(text("DROP FUNCTION IF EXISTS public.resolve_or_create_major(TEXT);"))
    conn.execute(text("DROP FUNCTION IF EXISTS public.resolve_or_create_school(TEXT);"))
    conn.execute(text("DROP FUNCTION IF EXISTS public.assign_major_number(BIGINT);"))
    conn.execute(text("DROP FUNCTION IF EXISTS public.assign_school_number(BIGINT);"))
    
    # Drop sequences
    conn.execute(text("DROP SEQUENCE IF EXISTS public.majors_major_number_seq;"))
    conn.execute(text("DROP SEQUENCE IF EXISTS public.schools_school_number_seq;"))
