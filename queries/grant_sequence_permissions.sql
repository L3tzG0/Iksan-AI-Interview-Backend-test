-- Fix sequence permissions for all tables in the database
-- This resolves "permission denied for sequence" errors
-- Execute this as the postgres superuser or database owner

-- Grant sequence permissions for BIGSERIAL tables
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service_role;

-- Grant table permissions to allow full operations
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT USAGE ON SCHEMA public TO service_role;

-- Apply to specific sequences created by BIGSERIAL columns
GRANT USAGE, SELECT ON SEQUENCE public.roles_id_seq TO authenticated, anon, service_role;
GRANT USAGE, SELECT ON SEQUENCE public.schools_id_seq TO authenticated, anon, service_role;
GRANT USAGE, SELECT ON SEQUENCE public.majors_id_seq TO authenticated, anon, service_role;
GRANT USAGE, SELECT ON SEQUENCE public.teachers_id_seq TO authenticated, anon, service_role;
GRANT USAGE, SELECT ON SEQUENCE public.classes_id_seq TO authenticated, anon, service_role;
GRANT USAGE, SELECT ON SEQUENCE public.students_id_seq TO authenticated, anon, service_role;
GRANT USAGE, SELECT ON SEQUENCE public.sessions_id_seq TO authenticated, anon, service_role;
GRANT USAGE, SELECT ON SEQUENCE public.documents_id_seq TO authenticated, anon, service_role;
GRANT USAGE, SELECT ON SEQUENCE public.scores_id_seq TO authenticated, anon, service_role;
GRANT USAGE, SELECT ON SEQUENCE public.summaries_id_seq TO authenticated, anon, service_role;
GRANT USAGE, SELECT ON SEQUENCE public.detailed_feedbacks_id_seq TO authenticated, anon, service_role;
GRANT USAGE, SELECT ON SEQUENCE public.next_steps_id_seq TO authenticated, anon, service_role;

-- Ensure service_role has all necessary permissions on tables
GRANT ALL ON public.roles TO service_role;
GRANT ALL ON public.schools TO service_role;
GRANT ALL ON public.majors TO service_role;
GRANT ALL ON public.user_profiles TO service_role;
GRANT ALL ON public.teachers TO service_role;
GRANT ALL ON public.classes TO service_role;
GRANT ALL ON public.students TO service_role;
GRANT ALL ON public.sessions TO service_role;
GRANT ALL ON public.documents TO service_role;
GRANT ALL ON public.scores TO service_role;
GRANT ALL ON public.summaries TO service_role;
GRANT ALL ON public.detailed_feedbacks TO service_role;
GRANT ALL ON public.next_steps TO service_role;
