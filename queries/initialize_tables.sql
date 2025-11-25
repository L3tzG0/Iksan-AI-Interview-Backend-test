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

-- Enable Row Level Security
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- RLS Policies for user_profiles
CREATE POLICY "Users can view own profile"
    ON user_profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON user_profiles FOR UPDATE
    USING (auth.uid() = id);

CREATE POLICY "Service role can insert profiles"
    ON user_profiles FOR INSERT
    WITH CHECK (true);

-- Optional: teachers are users
CREATE TABLE teachers (
  id                BIGSERIAL PRIMARY KEY,
  user_id           UUID UNIQUE REFERENCES user_profiles(id) ON DELETE CASCADE,
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
  user_id               UUID UNIQUE REFERENCES user_profiles(id) ON DELETE CASCADE,
  school_id             BIGINT REFERENCES schools(id) ON DELETE SET NULL,
  major_id              BIGINT REFERENCES majors(id) ON DELETE SET NULL,
  current_class_id      BIGINT REFERENCES classes(id) ON DELETE SET NULL,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Enable RLS for students
ALTER TABLE students ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Students can view own data"
    ON students FOR SELECT
    USING (auth.uid() = user_id);

-- Enable RLS for teachers
ALTER TABLE teachers ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Teachers can view own data"
    ON teachers FOR SELECT
    USING (auth.uid() = user_id);

-- Sessions and related artifacts
CREATE TABLE sessions (
  id                    BIGSERIAL PRIMARY KEY,
  student_id            BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  status                TEXT NOT NULL,
  completed_at          TIMESTAMPTZ,
  total_score           NUMERIC(6,2) CHECK (total_score >= 0),
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_sessions_student_id ON sessions(student_id);

CREATE TABLE documents (
  id                    BIGSERIAL PRIMARY KEY,
  session_id            BIGINT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  cleaned_text              TEXT
);

CREATE INDEX idx_documents_session_id ON documents(session_id);

CREATE TABLE scores (
  id                          BIGSERIAL PRIMARY KEY,
  session_id                  BIGINT NOT NULL UNIQUE REFERENCES sessions(id) ON DELETE CASCADE,
  content_relevance_score     NUMERIC(5,2) CHECK (content_relevance_score >= 0),
  structure_score             NUMERIC(5,2) CHECK (structure_score >= 0),
  fluency_score               NUMERIC(5,2) CHECK (fluency_score >= 0),
  confidence_score            NUMERIC(5,2) CHECK (confidence_score >= 0),
  overall_score               NUMERIC(6,2) CHECK (overall_score >= 0)
);

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
  score                 NUMERIC(5,2) CHECK (score >= 0),
  transcript            TEXT
);

CREATE INDEX idx_detailed_feedbacks_session_id ON detailed_feedbacks(session_id);
CREATE INDEX idx_detailed_feedbacks_session_question_order ON detailed_feedbacks(session_id, question_order);

CREATE TABLE next_steps (
  id                    BIGSERIAL PRIMARY KEY,
  session_id            BIGINT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  title                 TEXT NOT NULL,
  description_text      TEXT
);

CREATE INDEX idx_next_steps_session_id ON next_steps(session_id);

-- Indexes for performance
CREATE INDEX idx_user_profiles_email ON user_profiles(email);
CREATE INDEX idx_user_profiles_role_id ON user_profiles(role_id);
CREATE INDEX idx_students_user_id ON students(user_id);
CREATE INDEX idx_students_school_id ON students(school_id);
CREATE INDEX idx_students_major_id ON students(major_id);
CREATE INDEX idx_students_class_id ON students(current_class_id);
CREATE INDEX idx_teachers_user_id ON teachers(user_id);

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
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_role_id bigint;
    v_role_exists boolean;
BEGIN
    -- Extract role_id from metadata
    v_role_id := CASE 
        WHEN NEW.raw_user_meta_data->>'role_id' IS NOT NULL 
        THEN (NEW.raw_user_meta_data->>'role_id')::bigint
        ELSE NULL
    END;
    
    -- Validate role exists if role_id is provided
    IF v_role_id IS NOT NULL THEN
        SELECT EXISTS(SELECT 1 FROM public.roles WHERE id = v_role_id) INTO v_role_exists;
        
        IF NOT v_role_exists THEN
            RAISE EXCEPTION 'Role with id % does not exist. Please seed roles table first.', v_role_id;
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
GRANT USAGE, SELECT ON SEQUENCE user_profiles_id_seq TO supabase_auth_admin;
GRANT USAGE, SELECT ON SEQUENCE students_id_seq TO supabase_auth_admin;
GRANT USAGE, SELECT ON SEQUENCE teachers_id_seq TO supabase_auth_admin;

-- Grant sequence permissions to service_role and other roles for BIGSERIAL columns
-- This fixes "permission denied for sequence" errors
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service_role, authenticated, anon;

-- Grant table permissions to service_role (used by backend with SUPABASE_KEY)
GRANT ALL ON public.roles TO service_role;
GRANT ALL ON public.schools TO service_role;
GRANT ALL ON public.majors TO service_role;
GRANT ALL ON public.user_profiles TO service_role;
GRANT ALL ON public.teachers TO service_role;
GRANT ALL ON public.classes TO service_role;
GRANT ALL ON public.students TO service_role;
GRANT ALL ON public.sessions TO service_role;
GRANT ALL ON public.documents TO service_role;
GRANT ALL ON public.scores TO service_role;
GRANT ALL ON public.summaries TO service_role;
GRANT ALL ON public.detailed_feedbacks TO service_role;
GRANT ALL ON public.next_steps TO service_role;