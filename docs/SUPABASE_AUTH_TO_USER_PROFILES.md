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

---

## Step-by-Step Migration Instructions

### Prerequisites

- ✅ Backup your database before proceeding
- ✅ Ensure you have Supabase project access
- ✅ Have your `.env` file configured with `SUPABASE_URL` and `SUPABASE_KEY`

### Step 1: Run SQL Migration

Go to your Supabase Dashboard → **SQL Editor** and execute the migration file:

```bash
migrations/001_user_profiles_setup.sql
```

**What this does:**
1. Drops old `public.users` table (⚠️ deletes existing data)
2. Creates new `public.user_profiles` table with UUID primary key
3. Updates `students` and `teachers` tables to use UUID foreign keys
4. Creates trigger function `handle_new_user()` to auto-sync profiles
5. Sets up Row Level Security (RLS) policies
6. Adds performance indexes

**⚠️ IMPORTANT**: If you have existing production data, modify the migration to migrate data instead of dropping tables.

### Step 2: Update Application Dependencies

The code changes are already applied. Verify by checking:

```bash
# Models updated
app/models/user.py         # User → UserProfile (UUID id)
app/models/student.py      # user_id changed to UUID
app/models/teacher.py      # user_id changed to UUID

# Schemas updated
app/schemas/user.py        # User* → UserProfile* (UUID support)
app/schemas/student.py     # user_id changed to UUID
app/schemas/teacher.py     # user_id changed to UUID

# Services updated
app/services/user_service.py  # UserService → UserProfileService

# Endpoints updated
app/api/v1/endpoints/auth.py   # Updated to use profiles
app/api/v1/endpoints/users.py  # Updated for UUID and profiles
```

### Step 3: Test the Migration

#### Test 1: Register a New User

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123!",
    "full_name": "Test User",
    "role_id": 1
  }'
```

**Expected Result:**
- User created in `auth.users`
- Profile automatically created in `public.user_profiles` (via trigger)
- Response contains UUID for user id

#### Test 2: Login

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123!"
  }'
```

**Expected Result:**
- JWT access token returned
- Refresh token returned

#### Test 3: Get Current User

```bash
curl http://127.0.0.1:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Expected Result:**
- User data from both `auth.users` and `public.user_profiles`
- UUID for user id

#### Test 4: Verify Database Trigger

Check Supabase Dashboard → **Table Editor** → `user_profiles`

After registration, you should see a new row with:
- `id` matching the UUID from `auth.users`
- `email`, `full_name`, `role_id` populated from registration

---

## Data Model Changes

### Old Schema (users table)

```sql
CREATE TABLE public.users (
    id INTEGER PRIMARY KEY,           -- ❌ Integer ID
    email TEXT,
    password_hash TEXT,               -- ❌ Password stored in app
    full_name TEXT,
    role_id INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### New Schema (user_profiles table)

```sql
CREATE TABLE public.user_profiles (
    id UUID PRIMARY KEY               -- ✅ UUID (references auth.users)
        REFERENCES auth.users(id) 
        ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    role_id INTEGER REFERENCES public.roles(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
-- ✅ No password_hash (handled by Supabase Auth)
```

### Trigger Function

```sql
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
    INSERT INTO public.user_profiles (id, email, full_name, role_id)
    VALUES (
        NEW.id,
        NEW.email,
        NEW.raw_user_meta_data->>'full_name',
        (NEW.raw_user_meta_data->>'role_id')::integer
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();
```

---

## API Changes

### Before vs After

| Endpoint | Before | After |
|----------|--------|-------|
| `POST /api/v1/auth/register` | ✅ Same interface | ✅ Same interface |
| `POST /api/v1/auth/login` | ✅ Same interface | ✅ Same interface |
| `GET /api/v1/auth/me` | Returns from auth.users only | Returns from auth.users + user_profiles |
| `GET /api/v1/users` | Returns from public.users | Returns from public.user_profiles |
| `GET /api/v1/users/{id}` | Accepts integer id | ✅ Now accepts UUID |
| `PUT /api/v1/users/{id}` | Accepts integer id | ✅ Now accepts UUID |

### Response Schema Changes

**User Response (Before):**
```json
{
  "id": 123,              // Integer
  "email": "user@example.com",
  "full_name": "John Doe",
  "role_id": 1,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

**User Response (After):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",  // UUID
  "email": "user@example.com",
  "full_name": "John Doe",
  "role_id": 1,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

---

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

---

## Rollback Plan

If you need to rollback:

1. **Stop the application**
2. **Restore database from backup**
3. **Revert code changes:**
   ```bash
   git revert HEAD  # If committed
   # Or manually restore previous versions of:
   # - app/models/user.py
   # - app/schemas/user.py
   # - app/services/user_service.py
   # - app/api/v1/endpoints/auth.py
   # - app/api/v1/endpoints/users.py
   ```
4. **Restart application**

---

## Next Steps After Migration

### 1. Update Frontend/Mobile Clients

If you have frontend clients, update them to:
- Handle UUID user IDs instead of integers
- No changes needed for auth endpoints (same interface)

### 2. Consider Additional Features

Now that you're using Supabase Auth, you can easily add:
- 🔐 Magic link authentication
- 📱 Social login (Google, GitHub, etc.)
- 🔑 Multi-factor authentication (MFA)
- ✉️ Email verification
- 🔄 Password reset flows

### 3. Enhance Profile Data

You can extend `user_profiles` with additional fields:
```sql
ALTER TABLE public.user_profiles
ADD COLUMN avatar_url TEXT,
ADD COLUMN phone_number TEXT,
ADD COLUMN date_of_birth DATE,
ADD COLUMN bio TEXT;
```

### 4. Set Up RLS Policies

Review and customize Row Level Security policies:
- Who can read profiles?
- Who can update profiles?
- Admin access patterns?

---

## Summary

✅ **Migration Complete!**

You now have:
- Secure authentication via Supabase Auth
- Extended user profiles in your application database
- Automatic synchronization between auth and profile data
- UUID-based foreign keys throughout the system
- Clean separation of concerns
- Foundation for advanced auth features

**Key Points:**
- ✅ Passwords are managed by Supabase (never stored in your app)
- ✅ Profile data is automatically created when users register
- ✅ Foreign keys use UUIDs (matching Supabase Auth)
- ✅ RLS policies protect user data
- ✅ No breaking changes to auth endpoints

**Questions or Issues?**
- Check Supabase Dashboard → Authentication → Users
- Check Supabase Dashboard → Table Editor → user_profiles
- Review trigger function in SQL Editor
- Check application logs for errors

---

## References

- [Supabase: Managing User Data](https://supabase.com/docs/guides/auth/managing-user-data)
- [Supabase: Auth Hooks](https://supabase.com/docs/guides/auth/auth-hooks)
- [Supabase: Row Level Security](https://supabase.com/docs/guides/auth/row-level-security)
- [PostgreSQL: Triggers](https://www.postgresql.org/docs/current/triggers.html)
