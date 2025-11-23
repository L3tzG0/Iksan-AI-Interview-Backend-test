# Migration Guide: User Profiles Implementation

## Overview

This migration implements the **Supabase recommended pattern** for managing user data by separating authentication (handled by `auth.users`) from profile data (stored in `public.user_profiles`).

### What Changed?

**Before:**
- Redundant user data in both `auth.users` (Supabase Auth) and `public.users` (app database)
- `public.users` table with INTEGER id and password_hash
- No synchronization between the two systems
- Foreign key mismatches (UUID vs INTEGER)

**After:**
- Single source of truth for authentication: `auth.users` (Supabase Auth)
- Extended profile data in: `public.user_profiles` (app database)
- Automatic synchronization via database trigger
- UUID foreign keys throughout the system
- No password management in application code (handled by Supabase)

---

## Benefits of This Approach

✅ **Security**: Passwords managed by Supabase Auth with industry best practices  
✅ **Simplicity**: No manual synchronization needed between auth and profile data  
✅ **Scalability**: Can store extensive user profile data without affecting auth  
✅ **Best Practice**: Following official Supabase documentation patterns  
✅ **Maintainability**: Clear separation of concerns (auth vs business data)  
✅ **Future-proof**: Easy to add social auth, magic links, MFA, etc.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Registration Flow                    │
└─────────────────────────────────────────────────────────────┘

Client
  │
  │ POST /api/v1/auth/register
  │ { email, password, full_name, role_id }
  │
  ▼
FastAPI Auth Endpoint
  │
  │ supabase.auth.sign_up()
  │
  ▼
Supabase Auth Service
  │
  │ Creates user in auth.users
  │ Stores metadata: { full_name, role_id }
  │
  ▼
Database Trigger (on_auth_user_created)
  │
  │ Automatically executes handle_new_user()
  │
  ▼
public.user_profiles
  │
  │ INSERT new profile
  │ id = auth.users.id (UUID)
  │ Extracts: email, full_name, role_id
  │
  ▼
Success Response ✓
```


## Common Issues & Solutions

### Issue 1: Trigger Not Firing

**Symptom**: User created in `auth.users` but no profile in `user_profiles`

**Solution**:
1. Check if trigger exists:
   ```sql
   SELECT * FROM pg_trigger WHERE tgname = 'on_auth_user_created';
   ```

2. Check trigger function permissions:
   ```sql
   GRANT USAGE ON SCHEMA public TO supabase_auth_admin;
   GRANT ALL ON public.user_profiles TO supabase_auth_admin;
   ```

### Issue 2: Foreign Key Violations

**Symptom**: Cannot create student/teacher records

**Solution**:
1. Ensure user profile exists first
2. Use UUID (not integer) for user_id
3. Check foreign key constraints are properly set

### Issue 3: RLS Policy Blocking Access

**Symptom**: Cannot query user_profiles

**Solution**:
```sql
-- Temporarily disable RLS for debugging
ALTER TABLE public.user_profiles DISABLE ROW LEVEL SECURITY;

-- Check data
SELECT * FROM public.user_profiles;

-- Re-enable with correct policy
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
```


## References

- [Supabase: Managing User Data](https://supabase.com/docs/guides/auth/managing-user-data)
- [Supabase: Auth Hooks](https://supabase.com/docs/guides/auth/auth-hooks)
- [Supabase: Row Level Security](https://supabase.com/docs/guides/auth/row-level-security)
- [PostgreSQL: Triggers](https://www.postgresql.org/docs/current/triggers.html)
