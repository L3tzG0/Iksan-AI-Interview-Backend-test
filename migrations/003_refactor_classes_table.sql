-- Migration: 003_refactor_classes_table
-- Created: 2025-12-09
-- Description: Refactor classes table structure

-- This migration refactors the classes table:
-- - Removes class_year column (replaced with grade_level)
-- - Removes homeroom_teacher_id column (relationship not needed)
-- - Adds class_name TEXT column for descriptive class names
-- - Adds grade_level INTEGER column with CHECK constraint (1, 2, or 3)

-- ============================================================================
-- ALTER CLASSES TABLE
-- ============================================================================

-- Drop the old columns
ALTER TABLE classes DROP COLUMN IF EXISTS class_year;
ALTER TABLE classes DROP COLUMN IF EXISTS homeroom_teacher_id;

-- Add new columns
ALTER TABLE classes ADD COLUMN class_name TEXT NOT NULL DEFAULT 'Unnamed Class';
ALTER TABLE classes ADD COLUMN grade_level INTEGER NOT NULL DEFAULT 1;

-- Add CHECK constraint for grade_level
ALTER TABLE classes ADD CONSTRAINT classes_grade_level_check 
    CHECK (grade_level IN (1, 2, 3));

-- Remove the default values after migration (optional, keeps schema clean)
ALTER TABLE classes ALTER COLUMN class_name DROP DEFAULT;
ALTER TABLE classes ALTER COLUMN grade_level DROP DEFAULT;

-- Note: Existing classes will need to have their class_name updated manually
-- as the default 'Unnamed Class' is just a placeholder for the migration
