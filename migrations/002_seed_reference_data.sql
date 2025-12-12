-- Migration: 002_seed_reference_data
-- Created: 2025-12-09 00:00:00
-- Description: Seed reference data (roles, schools, majors)

-- This migration populates the reference tables with initial data
-- Uses ON CONFLICT to make the migration idempotent

-- ============================================================================
-- SEED ROLES
-- ============================================================================

INSERT INTO roles (id, role_name)
VALUES 
    (1, 'admin'),
    (2, 'teacher'),
    (3, 'student')
ON CONFLICT (role_name) DO NOTHING;

-- Reset sequence if needed
SELECT setval('roles_id_seq', (SELECT MAX(id) FROM roles));

-- ============================================================================
-- SEED SCHOOLS
-- ============================================================================

INSERT INTO schools (id, school_name)
VALUES 
    (1, '이리공업고등학교'),
    (2, '전북기계공업고등학교')
ON CONFLICT (school_name) DO NOTHING;

-- Reset sequence if needed
SELECT setval('schools_id_seq', (SELECT MAX(id) FROM schools));

-- ============================================================================
-- SEED MAJORS
-- ============================================================================

INSERT INTO majors (id, major_name)
VALUES 
    (1, '전기전자과'),
    (2, '전기제어'),
    (3, '자동화기계'),
    (4, '스마트팩토리'),
    (5, '조리제빵'),
    (6, '기계설계'),
    (7, '소프트웨어과')
ON CONFLICT (major_name) DO NOTHING;

-- Reset sequence if needed
SELECT setval('majors_id_seq', (SELECT MAX(id) FROM majors));
