-- Migration: 003_refactor_classes_table (ROLLBACK)
-- Created: 2025-12-09
-- Description: Rollback the classes table refactoring

-- This migration rolls back the changes from 003_refactor_classes_table.sql
-- Warning: This will lose data in class_name and grade_level columns

-- ============================================================================
-- ROLLBACK CLASSES TABLE CHANGES
-- ============================================================================

-- Remove CHECK constraint
ALTER TABLE classes DROP CONSTRAINT IF EXISTS classes_grade_level_check;

-- Drop new columns
ALTER TABLE classes DROP COLUMN IF EXISTS class_name;
ALTER TABLE classes DROP COLUMN IF EXISTS grade_level;

-- Restore old columns
ALTER TABLE classes ADD COLUMN class_year INTEGER NOT NULL DEFAULT 1;
ALTER TABLE classes ADD COLUMN homeroom_teacher_id BIGINT REFERENCES teachers(id) ON DELETE SET NULL;

-- Remove default after restoration
ALTER TABLE classes ALTER COLUMN class_year DROP DEFAULT;

-- Note: The old class_year and homeroom_teacher_id values cannot be recovered
-- Additional data migration may be required if rollback is necessary
