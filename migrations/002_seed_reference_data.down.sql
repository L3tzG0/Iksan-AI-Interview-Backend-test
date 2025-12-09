-- Migration Downgrade: 002_seed_reference_data
-- Created: 2025-12-09 00:00:00
-- Description: Rollback for Seed Reference Data

-- WARNING: This will delete reference data!
-- Only use this if you need to completely reset reference data.
-- Consider the impact on foreign key constraints before running.

-- ============================================================================
-- DELETE REFERENCE DATA
-- ============================================================================

-- Delete majors (must be done before students due to foreign key)
DELETE FROM majors WHERE id IN (1, 2, 3, 4, 5, 6, 7);

-- Delete schools (must be done before students/teachers due to foreign key)
DELETE FROM schools WHERE id IN (1, 2);

-- Delete roles (must be done before user_profiles due to foreign key)
DELETE FROM roles WHERE id IN (1, 2, 3);

-- Reset sequences
SELECT setval('roles_id_seq', 1, false);
SELECT setval('schools_id_seq', 1, false);
SELECT setval('majors_id_seq', 1, false);
