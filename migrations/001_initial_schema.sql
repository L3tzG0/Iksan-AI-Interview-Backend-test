-- Migration: 001_initial_schema
-- Created: 2025-12-09 00:00:00
-- Description: Initial database schema with all tables, triggers, and permissions

-- This migration creates the complete database schema for the Iksan AI Interview system
-- Including: reference tables, user profiles, teachers, students, sessions, and feedback tables

-- ============================================================================
-- REFERENCE TABLES
-- ============================================================================

-- Roles table (admin, teacher, student)
CREATE TABLE IF NOT EXISTS roles (
    id BIGSERIAL PRIMARY KEY,
    role_name TEXT NOT NULL UNIQUE
);

-- Schools table
CREATE TABLE IF NOT EXISTS schools (
    id BIGSERIAL PRIMARY KEY,
    school_name TEXT NOT NULL UNIQUE
);

-- Majors table
CREATE TABLE IF NOT EXISTS majors (
    id BIGSERIAL PRIMARY KEY,
    major_name TEXT NOT NULL UNIQUE
);

-- ============================================================================
-- USER MANAGEMENT TABLES
-- ============================================================================

-- User Profiles (extends auth.users from Supabase Auth)
-- Note: auth.users table is managed by Supabase and contains authentication data
-- This table stores additional profile information
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    role_id BIGINT REFERENCES roles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Teachers table (optional: teachers are users)
CREATE TABLE IF NOT EXISTS teachers (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID UNIQUE REFERENCES user_profiles(id) ON DELETE CASCADE,
    school_id BIGINT REFERENCES schools(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Classes table
CREATE TABLE IF NOT EXISTS classes (
    id BIGSERIAL PRIMARY KEY,
    class_name TEXT NOT NULL,
    grade_level INTEGER NOT NULL CHECK (grade_level IN (1, 2, 3))
);

-- Students table
CREATE TABLE IF NOT EXISTS students (
    id BIGSERIAL PRIMARY KEY,
    student_id TEXT NOT NULL UNIQUE,
    user_id UUID UNIQUE REFERENCES user_profiles(id) ON DELETE CASCADE,
    school_id BIGINT NOT NULL REFERENCES schools(id) ON DELETE RESTRICT,
    major_id BIGINT NOT NULL REFERENCES majors(id) ON DELETE RESTRICT,
    current_class_id BIGINT NOT NULL REFERENCES classes(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- SESSION AND INTERVIEW TABLES
-- ============================================================================

-- Sessions table (interview sessions)
CREATE TABLE IF NOT EXISTS sessions (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    completed_at TIMESTAMPTZ,
    total_score NUMERIC(3,1) CHECK (total_score >= 0 AND total_score <= 10),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Documents table (uploaded documents for sessions)
CREATE TABLE IF NOT EXISTS documents (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    cleaned_text TEXT
);

-- Summaries table (session summary feedback)
CREATE TABLE IF NOT EXISTS summaries (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL UNIQUE REFERENCES sessions(id) ON DELETE CASCADE,
    strength_text TEXT,
    areas_for_growth_text TEXT
);

-- Detailed feedbacks table (per-question feedback)
CREATE TABLE IF NOT EXISTS detailed_feedbacks (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    question_order INT,
    question_text TEXT,
    answer_text TEXT,
    evaluation_text TEXT,
    is_correct BOOLEAN DEFAULT FALSE,
    content_relevance_score NUMERIC(3,1) CHECK (content_relevance_score >= 0 AND content_relevance_score <= 10),
    structure_score NUMERIC(3,1) CHECK (structure_score >= 0 AND structure_score <= 10),
    fluency_score NUMERIC(3,1) CHECK (fluency_score >= 0 AND fluency_score <= 10),
    confidence_score NUMERIC(3,1) CHECK (confidence_score >= 0 AND confidence_score <= 10),
    overall_score NUMERIC(3,1) CHECK (overall_score >= 0 AND overall_score <= 10)
);

-- Next steps table (recommended actions after interview)
CREATE TABLE IF NOT EXISTS next_steps (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    next_step_order INT,
    title TEXT NOT NULL,
    description_text TEXT
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_sessions_student_id ON sessions(student_id);
CREATE INDEX IF NOT EXISTS idx_documents_session_id ON documents(session_id);
CREATE INDEX IF NOT EXISTS idx_detailed_feedbacks_session_id ON detailed_feedbacks(session_id);
CREATE INDEX IF NOT EXISTS idx_detailed_feedbacks_session_question_order ON detailed_feedbacks(session_id, question_order);
CREATE INDEX IF NOT EXISTS idx_next_steps_session_id ON next_steps(session_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email);
CREATE INDEX IF NOT EXISTS idx_user_profiles_role_id ON user_profiles(role_id);
CREATE INDEX IF NOT EXISTS idx_students_user_id ON students(user_id);
CREATE INDEX IF NOT EXISTS idx_students_student_id ON students(student_id);
CREATE INDEX IF NOT EXISTS idx_students_school_id ON students(school_id);
CREATE INDEX IF NOT EXISTS idx_students_major_id ON students(major_id);
CREATE INDEX IF NOT EXISTS idx_students_class_id ON students(current_class_id);
CREATE INDEX IF NOT EXISTS idx_teachers_user_id ON teachers(user_id);
CREATE INDEX IF NOT EXISTS idx_teachers_school_id ON teachers(school_id);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Trigger function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION handle_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

-- Apply updated_at triggers
DROP TRIGGER IF EXISTS set_user_profiles_updated_at ON user_profiles;
CREATE TRIGGER set_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION handle_updated_at();

DROP TRIGGER IF EXISTS set_students_updated_at ON students;
CREATE TRIGGER set_students_updated_at
    BEFORE UPDATE ON students
    FOR EACH ROW
    EXECUTE FUNCTION handle_updated_at();

DROP TRIGGER IF EXISTS set_teachers_updated_at ON teachers;
CREATE TRIGGER set_teachers_updated_at
    BEFORE UPDATE ON teachers
    FOR EACH ROW
    EXECUTE FUNCTION handle_updated_at();

-- ============================================================================
-- AUTH TRIGGER: Auto-create user profile on registration
-- ============================================================================

-- Trigger function to auto-create user profile when auth user is created
-- Also creates role-specific records for teachers (student registration is blocked)
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_role_id bigint;
    v_role_name text;
    v_school_id bigint;
BEGIN
    -- Extract role_id from metadata
    v_role_id := CASE 
        WHEN NEW.raw_user_meta_data->>'role_id' IS NOT NULL 
        THEN (NEW.raw_user_meta_data->>'role_id')::bigint
        ELSE NULL
    END;
    
    -- Extract school_id from metadata (for teachers)
    v_school_id := CASE 
        WHEN NEW.raw_user_meta_data->>'school_id' IS NOT NULL 
        THEN (NEW.raw_user_meta_data->>'school_id')::bigint
        ELSE NULL
    END;
    
    -- Validate role exists and get role_name (roles table is source of truth)
    IF v_role_id IS NOT NULL THEN
        SELECT role_name INTO v_role_name FROM public.roles WHERE id = v_role_id;
        
        IF v_role_name IS NULL THEN
            RAISE EXCEPTION 'Role with id % does not exist. Please seed roles table first.', v_role_id;
        END IF;
    END IF;
    
    -- Validate school exists if provided
    IF v_school_id IS NOT NULL THEN
        IF NOT EXISTS (SELECT 1 FROM public.schools WHERE id = v_school_id) THEN
            RAISE EXCEPTION 'School with id % does not exist.', v_school_id;
        END IF;
    END IF;
    
    -- Insert user profile
    INSERT INTO public.user_profiles (id, email, full_name, role_id)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(
            NEW.raw_user_meta_data->>'full_name',
            NEW.raw_user_meta_data->>'fullName',
            ''
        ),
        v_role_id
    );
    
    -- Create role-specific record based on role_name (source of truth)
    IF v_role_name = 'student' THEN
        -- Student registration is blocked
        RAISE EXCEPTION 'Student registration is not allowed. Students cannot register through this system.';
        
    ELSIF v_role_name = 'teacher' THEN
        INSERT INTO public.teachers (user_id, school_id)
        VALUES (NEW.id, v_school_id);
    END IF;
    -- Admin role doesn't require a separate record
    
    RETURN NEW;
EXCEPTION
    WHEN OTHERS THEN
        -- Log the error and re-raise to fail the auth.users insert
        RAISE LOG 'Error creating user profile for %: %', NEW.email, SQLERRM;
        RAISE;
END;
$$;

-- Drop and recreate trigger on auth.users
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION handle_new_user();

-- ============================================================================
-- PERMISSIONS
-- ============================================================================

-- Grant permissions to supabase_auth_admin (needed for trigger execution)
GRANT USAGE ON SCHEMA public TO supabase_auth_admin;
GRANT ALL ON public.user_profiles TO supabase_auth_admin;
GRANT ALL ON public.students TO supabase_auth_admin;
GRANT ALL ON public.teachers TO supabase_auth_admin;

-- Grant sequence permissions for user_profiles (needed for auto-generated fields)
GRANT USAGE, SELECT ON SEQUENCE students_id_seq TO supabase_auth_admin;
GRANT USAGE, SELECT ON SEQUENCE teachers_id_seq TO supabase_auth_admin;

-- Grant permissions to service_role and other roles
GRANT ALL ON public.roles TO authenticated, anon, service_role;
GRANT ALL ON public.schools TO authenticated, anon, service_role;
GRANT ALL ON public.majors TO authenticated, anon, service_role;
GRANT ALL ON public.user_profiles TO authenticated, anon, service_role;
GRANT ALL ON public.teachers TO authenticated, anon, service_role;
GRANT ALL ON public.classes TO authenticated, anon, service_role;
GRANT ALL ON public.students TO authenticated, anon, service_role;
GRANT ALL ON public.sessions TO authenticated, anon, service_role;
GRANT ALL ON public.documents TO authenticated, anon, service_role;
GRANT ALL ON public.summaries TO authenticated, anon, service_role;
GRANT ALL ON public.detailed_feedbacks TO authenticated, anon, service_role;
GRANT ALL ON public.next_steps TO authenticated, anon, service_role;

-- Grant sequence permissions for BIGSERIAL tables
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated, anon, service_role, supabase_auth_admin;

-- Grant table and schema permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated, anon, service_role;
GRANT USAGE ON SCHEMA public TO authenticated, anon, service_role;
