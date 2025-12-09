-- Migration Downgrade: 001_initial_schema
-- Created: 2025-12-09 00:00:00
-- Description: Rollback for Initial Schema

-- WARNING: This will delete ALL tables and data!
-- Only use this in development environments.

-- ============================================================================
-- DROP TRIGGERS FIRST
-- ============================================================================

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP TRIGGER IF EXISTS set_user_profiles_updated_at ON user_profiles;
DROP TRIGGER IF EXISTS set_students_updated_at ON students;
DROP TRIGGER IF EXISTS set_teachers_updated_at ON teachers;

-- ============================================================================
-- DROP FUNCTIONS
-- ============================================================================

DROP FUNCTION IF EXISTS handle_new_user();
DROP FUNCTION IF EXISTS handle_updated_at();

-- ============================================================================
-- DROP TABLES (in reverse order of dependencies)
-- ============================================================================

-- Drop dependent tables first
DROP TABLE IF EXISTS next_steps CASCADE;
DROP TABLE IF EXISTS detailed_feedbacks CASCADE;
DROP TABLE IF EXISTS summaries CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;

-- Drop user-related tables
DROP TABLE IF EXISTS students CASCADE;
DROP TABLE IF EXISTS classes CASCADE;
DROP TABLE IF EXISTS teachers CASCADE;
DROP TABLE IF EXISTS user_profiles CASCADE;

-- Drop reference tables
DROP TABLE IF EXISTS majors CASCADE;
DROP TABLE IF EXISTS schools CASCADE;
DROP TABLE IF EXISTS roles CASCADE;

-- Note: auth.users table is managed by Supabase and should not be dropped
