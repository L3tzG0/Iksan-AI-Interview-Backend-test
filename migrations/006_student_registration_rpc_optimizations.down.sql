-- Migration Downgrade: 006_student_registration_rpc_optimizations
-- Created: 2025-12-12
-- Description: Remove student registration RPC helper functions

DROP FUNCTION IF EXISTS public.resolve_or_create_class(TEXT, INTEGER);
DROP FUNCTION IF EXISTS public.resolve_or_create_major(TEXT);
DROP FUNCTION IF EXISTS public.resolve_or_create_school(TEXT);
