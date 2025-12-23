-- Migration Rollback: 008_email_domain_restrictions
-- Created: 2024-12-22
-- Description: Rollback email domain restrictions

-- This rollback removes:
-- 1. Auth hook function
-- 2. Helper functions
-- 3. RLS policies
-- 4. allowed_email_domains table
-- 5. All associated objects

-- ============================================================================
-- DROP HELPER FUNCTIONS
-- ============================================================================

DROP FUNCTION IF EXISTS get_active_domains() CASCADE;
DROP FUNCTION IF EXISTS activate_allowed_domain(TEXT) CASCADE;
DROP FUNCTION IF EXISTS deactivate_allowed_domain(TEXT) CASCADE;
DROP FUNCTION IF EXISTS add_allowed_domain(TEXT, TEXT) CASCADE;

-- ============================================================================
-- DROP AUTH HOOK FUNCTION
-- ============================================================================

DROP FUNCTION IF EXISTS public.before_user_created_hook(jsonb) CASCADE;
DROP FUNCTION IF EXISTS is_email_domain_allowed(TEXT) CASCADE;

-- ============================================================================
-- DROP TABLE AND RELATED OBJECTS
-- ============================================================================

-- Drop trigger first
DROP TRIGGER IF EXISTS update_allowed_email_domains_timestamp ON allowed_email_domains;

-- Drop trigger function
DROP FUNCTION IF EXISTS update_allowed_email_domains_updated_at() CASCADE;

-- Drop policies (will be dropped with table, but explicit for clarity)
DROP POLICY IF EXISTS "Admins can delete domains" ON allowed_email_domains;
DROP POLICY IF EXISTS "Admins can update domains" ON allowed_email_domains;
DROP POLICY IF EXISTS "Admins can insert domains" ON allowed_email_domains;
DROP POLICY IF EXISTS "Anyone can view active domains" ON allowed_email_domains;

-- Drop the main table
DROP TABLE IF EXISTS allowed_email_domains CASCADE;

-- ============================================================================
-- REVOKE PERMISSIONS
-- ============================================================================

-- Revoke schema usage from supabase_auth_admin
-- Note: Only revoke if not needed by other functions
-- REVOKE USAGE ON SCHEMA public FROM supabase_auth_admin;

-- ============================================================================
-- POST-ROLLBACK INSTRUCTIONS
-- ============================================================================

-- After running this rollback, you need to:
-- 1. Go to Supabase Dashboard > Authentication > Hooks
-- 2. Disable the "Before User Created" hook
-- 3. Save the configuration
--
-- This will completely remove email domain restrictions and allow
-- registration from any email domain.

-- ============================================================================
-- ROLLBACK COMPLETE
-- ============================================================================
