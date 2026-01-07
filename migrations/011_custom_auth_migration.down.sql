-- Migration: 011_custom_auth_migration (DOWN)
-- Rollback from custom auth to Supabase Auth

-- ============================================================================
-- STEP 1: Remove hashed_password column
-- ============================================================================

ALTER TABLE user_profiles
DROP COLUMN IF EXISTS hashed_password;

-- ============================================================================
-- STEP 2: Re-add the foreign key constraint on auth.users
-- ============================================================================

-- Note: This will only work if the auth.users table exists and has matching IDs
-- This is a destructive rollback - may fail if auth.users doesn't exist
DO $$ 
BEGIN
    ALTER TABLE user_profiles
    ADD CONSTRAINT user_profiles_id_fkey 
    FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE;
EXCEPTION
    WHEN OTHERS THEN
        RAISE WARNING 'Could not re-add foreign key constraint. auth.users may not exist or have matching IDs.';
END $$;

-- ============================================================================
-- STEP 3: Re-create the trigger function
-- ============================================================================

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
    v_role_id := CASE 
        WHEN NEW.raw_user_meta_data->>'role_id' IS NOT NULL 
        THEN (NEW.raw_user_meta_data->>'role_id')::bigint
        ELSE NULL
    END;
    
    v_school_id := CASE 
        WHEN NEW.raw_user_meta_data->>'school_id' IS NOT NULL 
        THEN (NEW.raw_user_meta_data->>'school_id')::bigint
        ELSE NULL
    END;
    
    IF v_role_id IS NOT NULL THEN
        SELECT role_name INTO v_role_name FROM public.roles WHERE id = v_role_id;
        IF v_role_name IS NULL THEN
            RAISE EXCEPTION 'Role with id % does not exist.', v_role_id;
        END IF;
    END IF;
    
    IF v_school_id IS NOT NULL THEN
        IF NOT EXISTS (SELECT 1 FROM public.schools WHERE id = v_school_id) THEN
            RAISE EXCEPTION 'School with id % does not exist.', v_school_id;
        END IF;
    END IF;
    
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
    
    IF v_role_name = 'teacher' THEN
        INSERT INTO public.teachers (user_id, school_id)
        VALUES (NEW.id, v_school_id);
    END IF;
    
    RETURN NEW;
EXCEPTION
    WHEN OTHERS THEN
        RAISE LOG 'Error creating user profile for %: %', NEW.email, SQLERRM;
        RAISE;
END;
$$;

-- ============================================================================
-- STEP 4: Re-create the trigger on auth.users
-- ============================================================================

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION handle_new_user();

-- ============================================================================
-- STEP 5: Re-grant permissions to supabase_auth_admin
-- ============================================================================

GRANT USAGE ON SCHEMA public TO supabase_auth_admin;
GRANT ALL ON public.user_profiles TO supabase_auth_admin;
GRANT ALL ON public.students TO supabase_auth_admin;
GRANT ALL ON public.teachers TO supabase_auth_admin;
