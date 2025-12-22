-- Migration: 008_email_domain_restrictions
-- Created: 2024-12-22
-- Description: Add email domain restrictions for user registration

-- This migration adds:
-- 1. allowed_email_domains table to store permitted email domains
-- 2. Auth hook function to validate email domains before user creation
-- 3. Seed data with initial allowed domains
-- 4. RLS policies for domain management
-- 5. Helper functions for domain management

-- ============================================================================
-- CREATE ALLOWED EMAIL DOMAINS TABLE
-- ============================================================================

-- Table to store allowed email domains for registration
CREATE TABLE IF NOT EXISTS allowed_email_domains (
    id BIGSERIAL PRIMARY KEY,
    domain TEXT NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    added_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    -- Ensure domain is lowercase and properly formatted
    CONSTRAINT domain_format CHECK (domain ~ '^[a-z0-9.-]+\.[a-z]{2,}$')
);

-- Create indexes for efficient lookups
CREATE INDEX IF NOT EXISTS idx_allowed_email_domains_domain 
    ON allowed_email_domains(domain);

CREATE INDEX IF NOT EXISTS idx_allowed_email_domains_active 
    ON allowed_email_domains(is_active) WHERE is_active = true;

-- Add updated_at trigger
CREATE OR REPLACE FUNCTION update_allowed_email_domains_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_allowed_email_domains_timestamp
    BEFORE UPDATE ON allowed_email_domains
    FOR EACH ROW
    EXECUTE FUNCTION update_allowed_email_domains_updated_at();

-- ============================================================================
-- SEED INITIAL ALLOWED DOMAINS
-- ============================================================================

-- Insert the internal student domain
INSERT INTO allowed_email_domains (domain, description, is_active)
VALUES 
    ('students.internal', 'Internal domain for student accounts', true)
ON CONFLICT (domain) DO NOTHING;

-- Add any other domains your organization uses
-- Example: Uncomment and modify as needed
-- INSERT INTO allowed_email_domains (domain, description, is_active)
-- VALUES 
--     ('yourcompany.com', 'Main company domain', true),
--     ('partner.org', 'Partner organization', true)
-- ON CONFLICT (domain) DO NOTHING;

-- ============================================================================
-- CREATE EMAIL DOMAIN VALIDATION FUNCTION
-- ============================================================================

-- Function to check if an email domain is allowed
CREATE OR REPLACE FUNCTION is_email_domain_allowed(email TEXT)
RETURNS BOOLEAN AS $$
DECLARE
    email_domain TEXT;
    is_allowed BOOLEAN;
BEGIN
    -- Extract domain from email (everything after @)
    email_domain := lower(split_part(email, '@', 2));
    
    -- Check if domain exists and is active
    SELECT EXISTS(
        SELECT 1 
        FROM allowed_email_domains 
        WHERE domain = email_domain 
        AND is_active = true
    ) INTO is_allowed;
    
    RETURN is_allowed;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- CREATE BEFORE USER CREATED AUTH HOOK
-- ============================================================================

-- Auth hook function that runs before a user is created
-- This validates the email domain and blocks registration if not allowed
CREATE OR REPLACE FUNCTION public.before_user_created_hook(event jsonb)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    user_email TEXT;
    email_domain TEXT;
    is_allowed BOOLEAN;
BEGIN
    -- Extract email from the event
    user_email := event->'user'->>'email';
    
    -- If no email (e.g., phone signup), allow it
    IF user_email IS NULL OR user_email = '' THEN
        RETURN event;
    END IF;
    
    -- Extract domain from email (everything after @)
    email_domain := lower(split_part(user_email, '@', 2));
    
    -- Check if domain is allowed using our validation function
    SELECT is_email_domain_allowed(user_email) INTO is_allowed;
    
    -- Block registration if domain is not allowed
    IF NOT is_allowed THEN
        RAISE EXCEPTION 'Registration is restricted to approved email domains. The domain "%" is not authorized for registration.', email_domain
            USING HINT = 'Please contact your administrator to request access or use an approved email domain.';
    END IF;
    
    -- Log successful validation (optional - can be removed in production)
    RAISE NOTICE 'Email domain validation passed for: % (domain: %)', user_email, email_domain;
    
    -- Return the event unchanged to allow user creation
    RETURN event;
END;
$$;

-- ============================================================================
-- GRANT PERMISSIONS FOR AUTH HOOK
-- ============================================================================

-- Grant execute permission to supabase_auth_admin (required for auth hooks)
GRANT EXECUTE ON FUNCTION public.before_user_created_hook TO supabase_auth_admin;

-- Grant usage on schema to supabase_auth_admin
GRANT USAGE ON SCHEMA public TO supabase_auth_admin;

-- Grant select permission on allowed_email_domains table
GRANT SELECT ON allowed_email_domains TO supabase_auth_admin;

-- Revoke permissions from other roles for security
REVOKE EXECUTE ON FUNCTION public.before_user_created_hook FROM authenticated, anon, public;

-- ============================================================================
-- ENABLE ROW LEVEL SECURITY
-- ============================================================================

-- Enable RLS on allowed_email_domains table
ALTER TABLE allowed_email_domains ENABLE ROW LEVEL SECURITY;

-- Policy: Anyone can view active domains (for client-side validation hints)
CREATE POLICY "Anyone can view active domains"
    ON allowed_email_domains
    FOR SELECT
    USING (is_active = true);

-- Policy: Only authenticated admins can insert domains
-- Note: You'll need to define admin users appropriately
-- Option 1: Check if user has admin role
CREATE POLICY "Admins can insert domains"
    ON allowed_email_domains
    FOR INSERT
    TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM users u
            WHERE u.id = auth.uid()
            AND u.role_id = 1  -- Assuming role_id 1 is admin
        )
    );

-- Policy: Only authenticated admins can update domains
CREATE POLICY "Admins can update domains"
    ON allowed_email_domains
    FOR UPDATE
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM users u
            WHERE u.id = auth.uid()
            AND u.role_id = 1  -- Assuming role_id 1 is admin
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM users u
            WHERE u.id = auth.uid()
            AND u.role_id = 1
        )
    );

-- Policy: Only authenticated admins can delete domains
CREATE POLICY "Admins can delete domains"
    ON allowed_email_domains
    FOR DELETE
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM users u
            WHERE u.id = auth.uid()
            AND u.role_id = 1
        )
    );

-- ============================================================================
-- HELPER FUNCTIONS FOR DOMAIN MANAGEMENT
-- ============================================================================

-- Function to safely add a new allowed domain
CREATE OR REPLACE FUNCTION add_allowed_domain(
    p_domain TEXT,
    p_description TEXT DEFAULT NULL
)
RETURNS BIGINT AS $$
DECLARE
    v_domain_id BIGINT;
    v_user_id UUID;
BEGIN
    -- Get current user ID
    v_user_id := auth.uid();
    
    -- Validate domain format
    IF p_domain !~ '^[a-z0-9.-]+\.[a-z]{2,}$' THEN
        RAISE EXCEPTION 'Invalid domain format: %. Domain must be lowercase and follow standard format (e.g., example.com)', p_domain;
    END IF;
    
    -- Insert domain
    INSERT INTO allowed_email_domains (domain, description, added_by)
    VALUES (lower(p_domain), p_description, v_user_id)
    RETURNING id INTO v_domain_id;
    
    RETURN v_domain_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to deactivate a domain (soft delete)
CREATE OR REPLACE FUNCTION deactivate_allowed_domain(p_domain TEXT)
RETURNS BOOLEAN AS $$
DECLARE
    v_updated BOOLEAN;
BEGIN
    UPDATE allowed_email_domains
    SET is_active = false
    WHERE domain = lower(p_domain)
    AND is_active = true;
    
    GET DIAGNOSTICS v_updated = ROW_COUNT;
    
    RETURN v_updated > 0;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to reactivate a domain
CREATE OR REPLACE FUNCTION activate_allowed_domain(p_domain TEXT)
RETURNS BOOLEAN AS $$
DECLARE
    v_updated BOOLEAN;
BEGIN
    UPDATE allowed_email_domains
    SET is_active = true
    WHERE domain = lower(p_domain)
    AND is_active = false;
    
    GET DIAGNOSTICS v_updated = ROW_COUNT;
    
    RETURN v_updated > 0;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get all active domains (useful for API endpoints)
CREATE OR REPLACE FUNCTION get_active_domains()
RETURNS TABLE (
    id BIGINT,
    domain TEXT,
    description TEXT,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        aed.id,
        aed.domain,
        aed.description,
        aed.created_at
    FROM allowed_email_domains aed
    WHERE aed.is_active = true
    ORDER BY aed.domain;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE allowed_email_domains IS 
'Stores email domains that are permitted for user registration. Integrated with Supabase Auth hooks for automatic validation.';

COMMENT ON COLUMN allowed_email_domains.domain IS 
'Email domain (e.g., "example.com"). Must be lowercase and follow standard domain format.';

COMMENT ON COLUMN allowed_email_domains.is_active IS 
'Whether the domain is currently active. Inactive domains are blocked from registration.';

COMMENT ON FUNCTION before_user_created_hook IS 
'Supabase Auth hook that validates email domain before user creation. Blocks registration if domain is not in allowed list.';

COMMENT ON FUNCTION is_email_domain_allowed IS 
'Checks if an email domain is in the allowed list and active.';

COMMENT ON FUNCTION add_allowed_domain IS 
'Safely adds a new allowed domain with validation. Returns the new domain ID.';

COMMENT ON FUNCTION deactivate_allowed_domain IS 
'Deactivates (soft deletes) a domain. Returns true if successful.';

COMMENT ON FUNCTION activate_allowed_domain IS 
'Reactivates a previously deactivated domain. Returns true if successful.';

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- To complete the setup, you need to:
-- 1. Run this migration in Supabase SQL Editor
-- 2. Go to Supabase Dashboard > Authentication > Hooks
-- 3. Enable "Before User Created" hook
-- 4. Select "Postgres Function" type
-- 5. Choose "public.before_user_created_hook" from the dropdown
-- 6. Save the configuration
--
-- After this, any user signup attempt will be validated against the
-- allowed_email_domains table. Only emails from allowed domains will
-- be permitted to register.
