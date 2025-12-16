-- ============================================================================
-- Rollback Migration: Restore original student auth trigger
-- ============================================================================
-- This rollback restores the original behavior that blocks ALL student
-- account creation (including admin-created ones).
-- ============================================================================

-- Restore the original trigger function
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
