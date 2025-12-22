-- Rollback: 009_email_domain_org_name
-- Created: 2025-12-22
-- Description: Revert organization_name column back to description and restore helper functions

-- =========================================================================
-- DROP FUNCTIONS USING NEW COLUMN NAME
-- =========================================================================
DROP FUNCTION IF EXISTS add_allowed_domain(TEXT, TEXT);
DROP FUNCTION IF EXISTS get_active_domains();

-- =========================================================================
-- RENAME COLUMN BACK
-- =========================================================================
ALTER TABLE allowed_email_domains
    RENAME COLUMN organization_name TO description;

-- =========================================================================
-- RECREATE ORIGINAL FUNCTIONS
-- =========================================================================
CREATE OR REPLACE FUNCTION add_allowed_domain(
    p_domain TEXT,
    p_description TEXT DEFAULT NULL
)
RETURNS BIGINT AS $$
DECLARE
    v_domain_id BIGINT;
    v_user_id UUID;
BEGIN
    v_user_id := auth.uid();

    IF p_domain !~ '^[a-z0-9.-]+\.[a-z]{2,}$' THEN
        RAISE EXCEPTION 'Invalid domain format: %. Domain must be lowercase and follow standard format (e.g., example.com)', p_domain;
    END IF;

    INSERT INTO allowed_email_domains (domain, description, added_by)
    VALUES (lower(p_domain), p_description, v_user_id)
    RETURNING id INTO v_domain_id;

    RETURN v_domain_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

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

-- =========================================================================
-- RESTORE COMMENTS
-- =========================================================================
COMMENT ON COLUMN allowed_email_domains.description IS 
'Email domain description (e.g., organization or usage notes).';
