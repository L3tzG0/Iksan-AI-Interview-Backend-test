-- ============================================================================
-- SEED REFERENCE DATA (Roles, Schools, Majors)
-- Run this BEFORE any user registration to ensure foreign key constraints work
-- ============================================================================

-- 1. Insert Roles
INSERT INTO roles (id, role_name) VALUES 
(1, 'admin'),
(2, 'teacher'),
(3, 'student')
ON CONFLICT (role_name) DO NOTHING;

-- 2. Insert Schools
INSERT INTO schools (id, school_name) VALUES 
(1, '이리공업고등학교'),
(2, '전북기계공업고등학교')
ON CONFLICT (school_name) DO NOTHING;

-- 3. Insert Majors
INSERT INTO majors (id, major_name) VALUES 
(1, '전기전자과'),
(2, '전기제어'),
(3, '자동화기계'),
(4, '스마트팩토리'),
(5, '조리제빵'),
(6, '기계설계'),
(7, '소프트웨어과')
ON CONFLICT (major_name) DO NOTHING;

-- Verify seeded data
SELECT 'Roles seeded:' as info, COUNT(*) as count FROM roles;
SELECT 'Schools seeded:' as info, COUNT(*) as count FROM schools;
SELECT 'Majors seeded:' as info, COUNT(*) as count FROM majors;
