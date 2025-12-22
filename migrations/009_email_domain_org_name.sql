-- Migration: 009_email_domain_org_name
-- Created: 2025-12-22
-- Description: Rename description column to organization_name on allowed_email_domains and update helper functions

-- =========================================================================
-- NOTES
-- =========================================================================
-- This migration:
-- 1) Renames allowed_email_domains.description -> organization_name
-- 2) Updates helper functions to use organization_name
-- 3) Refreshes column comments

-- =========================================================================
-- DROP/REPLACE FUNCTIONS THAT REFERENCE THE COLUMN
-- =========================================================================
DROP FUNCTION IF EXISTS add_allowed_domain(TEXT, TEXT);
DROP FUNCTION IF EXISTS get_active_domains();

-- =========================================================================
-- RENAME COLUMN
-- =========================================================================
ALTER TABLE allowed_email_domains
    RENAME COLUMN description TO organization_name;

-- =========================================================================
-- RECREATE FUNCTIONS WITH NEW COLUMN NAME
-- =========================================================================

CREATE OR REPLACE FUNCTION add_allowed_domain(
    p_domain TEXT,
    p_organization_name TEXT DEFAULT NULL
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
    INSERT INTO allowed_email_domains (domain, organization_name, added_by)
    VALUES (lower(p_domain), p_organization_name, v_user_id)
    RETURNING id INTO v_domain_id;

    RETURN v_domain_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION get_active_domains()
RETURNS TABLE (
    id BIGINT,
    domain TEXT,
    organization_name TEXT,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        aed.id,
        aed.domain,
        aed.organization_name,
        aed.created_at
    FROM allowed_email_domains aed
    WHERE aed.is_active = true
    ORDER BY aed.domain;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;


GRANT ALL ON public.allowed_email_domains TO authenticated, anon, service_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated, anon, service_role, supabase_auth_admin;

-- =========================================================================
-- UPDATE COMMENTS
-- =========================================================================
COMMENT ON COLUMN allowed_email_domains.organization_name IS 
'Organization name associated with the allowed domain (e.g., school or company).';
