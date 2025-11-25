# User Profiles Implementation


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
Success Response 
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
3. Ensure reference tables have data such as `roles`
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
