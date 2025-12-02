-- Roles, Schools, Majors
CREATE TABLE roles (
  id                BIGSERIAL PRIMARY KEY,
  role_name         TEXT NOT NULL UNIQUE
);

CREATE TABLE schools (
  id                BIGSERIAL PRIMARY KEY,
  school_name       TEXT NOT NULL UNIQUE
);

CREATE TABLE majors (
  id                BIGSERIAL PRIMARY KEY,
  major_name        TEXT NOT NULL UNIQUE
);

-- User Profiles (extends auth.users from Supabase Auth)
-- Note: auth.users table is managed by Supabase and contains authentication data
-- This table stores additional profile information
CREATE TABLE user_profiles (
  id                UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name         TEXT NOT NULL,
  email             TEXT NOT NULL UNIQUE,
  role_id           BIGINT REFERENCES roles(id) ON DELETE SET NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -- Enable Row Level Security
-- ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- -- RLS Policies for user_profiles
-- CREATE POLICY "Users can view own profile"
--     ON user_profiles FOR SELECT
--     USING (auth.uid() = id);

-- CREATE POLICY "Users can update own profile"
--     ON user_profiles FOR UPDATE
--     USING (auth.uid() = id);

-- CREATE POLICY "Service role can insert profiles"
--     ON user_profiles FOR INSERT
--     WITH CHECK (true);

-- Optional: teachers are users
CREATE TABLE teachers (
  id                BIGSERIAL PRIMARY KEY,
  user_id           UUID UNIQUE REFERENCES user_profiles(id) ON DELETE CASCADE,
  school_id         BIGINT REFERENCES schools(id) ON DELETE SET NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE classes (
  id                    BIGSERIAL PRIMARY KEY,
  class_name            TEXT NOT NULL,
  grade_level           TEXT,
  homeroom_teacher_id   BIGINT REFERENCES teachers(id) ON DELETE SET NULL
);

CREATE TABLE students (
  id                    BIGSERIAL PRIMARY KEY,
  student_id            TEXT NOT NULL UNIQUE,
  user_id               UUID UNIQUE REFERENCES user_profiles(id) ON DELETE CASCADE,
  school_id             BIGINT NOT NULL REFERENCES schools(id) ON DELETE RESTRICT,
  major_id              BIGINT NOT NULL REFERENCES majors(id) ON DELETE RESTRICT,
  current_class_id      BIGINT NOT NULL REFERENCES classes(id) ON DELETE RESTRICT,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -- Enable RLS for students
-- ALTER TABLE students ENABLE ROW LEVEL SECURITY;

-- CREATE POLICY "Students can view own data"
--     ON students FOR SELECT
--     USING (auth.uid() = user_id);

-- -- Enable RLS for teachers
-- ALTER TABLE teachers ENABLE ROW LEVEL SECURITY;

-- CREATE POLICY "Teachers can view own data"
--     ON teachers FOR SELECT
--     USING (auth.uid() = user_id);

-- Sessions and related artifacts
CREATE TABLE sessions (
  id                    BIGSERIAL PRIMARY KEY,
  student_id            BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  status                TEXT NOT NULL,
  completed_at          TIMESTAMPTZ,
  total_score           NUMERIC(3,1) CHECK (total_score >= 0 AND total_score <= 10),
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_sessions_student_id ON sessions(student_id);

CREATE TABLE documents (
  id                    BIGSERIAL PRIMARY KEY,
  session_id            BIGINT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  cleaned_text              TEXT
);

CREATE INDEX idx_documents_session_id ON documents(session_id);

CREATE TABLE summaries (
  id                    BIGSERIAL PRIMARY KEY,
  session_id            BIGINT NOT NULL UNIQUE REFERENCES sessions(id) ON DELETE CASCADE,
  strength_text         TEXT,
  areas_for_growth_text TEXT
);

CREATE TABLE detailed_feedbacks (
  id                    BIGSERIAL PRIMARY KEY,
  session_id            BIGINT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  question_order        INT,
  question_text         TEXT,
  answer_text           TEXT,
  evaluation_text       TEXT,
  is_correct            BOOLEAN DEFAULT FALSE,
  content_relevance_score NUMERIC(3,1) CHECK (content_relevance_score >= 0 AND content_relevance_score <= 10),
  structure_score       NUMERIC(3,1) CHECK (structure_score >= 0 AND structure_score <= 10),
  fluency_score         NUMERIC(3,1) CHECK (fluency_score >= 0 AND fluency_score <= 10),
  confidence_score      NUMERIC(3,1) CHECK (confidence_score >= 0 AND confidence_score <= 10),
  overall_score         NUMERIC(3,1) CHECK (overall_score >= 0 AND overall_score <= 10)
);

CREATE INDEX idx_detailed_feedbacks_session_id ON detailed_feedbacks(session_id);
CREATE INDEX idx_detailed_feedbacks_session_question_order ON detailed_feedbacks(session_id, question_order);

CREATE TABLE next_steps (
  id                    BIGSERIAL PRIMARY KEY,
  session_id            BIGINT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  next_step_order       INT,
  title                 TEXT NOT NULL,
  description_text      TEXT
);

CREATE INDEX idx_next_steps_session_id ON next_steps(session_id);

-- Indexes for performance
CREATE INDEX idx_user_profiles_email ON user_profiles(email);
CREATE INDEX idx_user_profiles_role_id ON user_profiles(role_id);
CREATE INDEX idx_students_user_id ON students(user_id);
CREATE INDEX idx_students_student_id ON students(student_id);
CREATE INDEX idx_students_school_id ON students(school_id);
CREATE INDEX idx_students_major_id ON students(major_id);
CREATE INDEX idx_students_class_id ON students(current_class_id);
CREATE INDEX idx_teachers_user_id ON teachers(user_id);
CREATE INDEX idx_teachers_school_id ON teachers(school_id);

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
CREATE TRIGGER set_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION handle_updated_at();

CREATE TRIGGER set_students_updated_at
    BEFORE UPDATE ON students
    FOR EACH ROW
    EXECUTE FUNCTION handle_updated_at();

CREATE TRIGGER set_teachers_updated_at
    BEFORE UPDATE ON teachers
    FOR EACH ROW
    EXECUTE FUNCTION handle_updated_at();

-- Trigger function to auto-create user profile when auth user is created
-- Also creates role-specific records (students/teachers) based on role_name
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
    v_student_id text;
    v_major_id bigint;
    v_class_id bigint;
BEGIN
    -- Extract role_id from metadata
    v_role_id := CASE 
        WHEN NEW.raw_user_meta_data->>'role_id' IS NOT NULL 
        THEN (NEW.raw_user_meta_data->>'role_id')::bigint
        ELSE NULL
    END;
    
    -- Extract school_id from metadata (for teachers and students)
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
        -- Extract student-specific fields from metadata
        v_student_id := NEW.raw_user_meta_data->>'student_id';
        v_major_id := CASE 
            WHEN NEW.raw_user_meta_data->>'major_id' IS NOT NULL 
            THEN (NEW.raw_user_meta_data->>'major_id')::bigint
            ELSE NULL
        END;
        v_class_id := CASE 
            WHEN NEW.raw_user_meta_data->>'class_id' IS NOT NULL 
            THEN (NEW.raw_user_meta_data->>'class_id')::bigint
            ELSE NULL
        END;
        
        -- Validate required fields for student
        IF v_student_id IS NULL THEN
            RAISE EXCEPTION 'student_id is required for student registration.';
        END IF;
        IF v_school_id IS NULL THEN
            RAISE EXCEPTION 'school_id is required for student registration.';
        END IF;
        IF v_major_id IS NULL THEN
            RAISE EXCEPTION 'major_id is required for student registration.';
        END IF;
        IF v_class_id IS NULL THEN
            RAISE EXCEPTION 'class_id is required for student registration.';
        END IF;
        
        -- Validate major exists
        IF NOT EXISTS (SELECT 1 FROM public.majors WHERE id = v_major_id) THEN
            RAISE EXCEPTION 'Major with id % does not exist.', v_major_id;
        END IF;
        
        -- Validate class exists
        IF NOT EXISTS (SELECT 1 FROM public.classes WHERE id = v_class_id) THEN
            RAISE EXCEPTION 'Class with id % does not exist.', v_class_id;
        END IF;
        
        INSERT INTO public.students (user_id, student_id, school_id, major_id, current_class_id)
        VALUES (NEW.id, v_student_id, v_school_id, v_major_id, v_class_id);
        
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

-- Drop trigger if exists and recreate
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

-- Create trigger on auth.users
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION handle_new_user();

-- Grant permissions to supabase_auth_admin (needed for trigger execution)
GRANT USAGE ON SCHEMA public TO supabase_auth_admin;
GRANT ALL ON public.user_profiles TO supabase_auth_admin;
GRANT ALL ON public.students TO supabase_auth_admin;
GRANT ALL ON public.teachers TO supabase_auth_admin;

-- Grant sequence permissions for user_profiles (needed for auto-generated fields)
GRANT USAGE, SELECT ON SEQUENCE students_id_seq TO supabase_auth_admin;
GRANT USAGE, SELECT ON SEQUENCE teachers_id_seq TO supabase_auth_admin;

-- Grant sequence permissions to service_role and other roles for BIGSERIAL columns
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service_role, authenticated, anon;

-- Ensure service_role has all necessary permissions on tables
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
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated, anon, service_role;

-- Apply to specific sequences created by BIGSERIAL columns
GRANT USAGE, SELECT ON SEQUENCE public.roles_id_seq TO authenticated, anon, service_role;
GRANT USAGE, SELECT ON SEQUENCE public.schools_id_seq TO authenticated, anon, service_role;
GRANT USAGE, SELECT ON SEQUENCE public.majors_id_seq TO authenticated, anon, service_role;
GRANT USAGE, SELECT ON SEQUENCE public.teachers_id_seq TO authenticated, anon, service_role;
GRANT USAGE, SELECT ON SEQUENCE public.classes_id_seq TO authenticated, anon, service_role;
GRANT USAGE, SELECT ON SEQUENCE public.students_id_seq TO authenticated, anon, service_role;
GRANT USAGE, SELECT ON SEQUENCE public.sessions_id_seq TO authenticated, anon, service_role;
GRANT USAGE, SELECT ON SEQUENCE public.documents_id_seq TO authenticated, anon, service_role;
GRANT USAGE, SELECT ON SEQUENCE public.summaries_id_seq TO authenticated, anon, service_role;
GRANT USAGE, SELECT ON SEQUENCE public.detailed_feedbacks_id_seq TO authenticated, anon, service_role;
GRANT USAGE, SELECT ON SEQUENCE public.next_steps_id_seq TO authenticated, anon, service_role;

-- Grant table permissions to allow full operations
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated, anon, service_role;
GRANT USAGE ON SCHEMA public TO authenticated, anon, service_role;