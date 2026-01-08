# Custom Authentication Migration Guide

## Overview

This document describes the migration from Supabase Auth to a custom JWT-based authentication system. The migration removes dependencies on Supabase's `auth.users` table and implements a fully self-contained authentication system using the `user_profiles` table.

## Key Changes

### Architecture Changes

1. **Removed Supabase Auth Dependencies**
   - No longer using `supabase.auth.sign_up`, `sign_in_with_password`, `refresh_session`, or `get_user`
   - No longer using `auth.admin` APIs for user creation
   - Removed the trigger that created `user_profiles` from `auth.users`

2. **New Authentication Flow**
   - User credentials (email + hashed_password) stored directly in `user_profiles`
   - JWT tokens generated and validated using our own `JWTManager` class
   - Password hashing using bcrypt instead of Supabase's internal hashing

3. **New Modules**
   - `app/core/jwt.py` - JWT token creation and validation
   - `app/core/password.py` - Password hashing with bcrypt
   - `app/core/auth_user.py` - Normalized `AuthenticatedUser` model

### Database Schema Changes

The migration adds a `hashed_password` column to `user_profiles` and removes the foreign key constraint on `auth.users`:

```sql
ALTER TABLE user_profiles ADD COLUMN hashed_password TEXT;
```

## Configuration

Add these environment variables to the `.env` file:

```env
# JWT Configuration
JWT_SECRET_KEY=secret-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
JWT_ISSUER=iksan-ai-interview
JWT_AUDIENCE=iksan-ai-interview-api
```


## Migration Steps

### 1. Database Migration

Run the database migration:
```bash
python scripts/migrate.py up 011_custom_auth_migration
```

### 2. Install Dependencies

Install the new Python packages:
```bash
pip install PyJWT bcrypt
```

Or update from requirements.txt:
```bash
pip install -r requirements.txt
```

## API Changes

### Authentication Endpoints

The API endpoints remain the same, but the implementation has changed:

| Endpoint | Description | Change |
|----------|-------------|--------|
| POST `/auth/register` | Register new user | Now creates user directly in `user_profiles` |
| POST `/auth/login` | User login | Validates against `user_profiles.hashed_password` |
| POST `/auth/refresh` | Refresh token | Uses custom JWT validation |
| POST `/auth/logout` | User logout | Now client-side only (discard tokens) |
| GET `/auth/me` | Get current user | Uses `AuthenticatedUser` model |
| POST `/auth/student-login` | Student login | Uses custom auth, same fake email pattern |

### Token Format

JWT tokens now include:
- `sub`: User UUID
- `email`: User email
- `role_id`: User role ID
- `role_name`: User role name
- `token_type`: "access" or "refresh"
- `exp`: Expiration timestamp
- `iat`: Issued at timestamp
- `iss`: Issuer (configurable)
- `aud`: Audience (configurable)
- `jti`: Unique token ID

### Response Format

Login/register responses maintain the same format but use the new `AuthenticatedUser` object internally.

## Files Modified

### Core Authentication
- `app/core/jwt.py` (new) - JWT token management
- `app/core/password.py` (new) - Password hashing
- `app/core/auth_user.py` (new) - Authenticated user model
- `app/core/security.py` - Updated to use custom JWT validation
- `app/core/config.py` - Added JWT configuration settings

### Services
- `app/services/auth_service.py` - Complete rewrite for custom auth
- `app/services/student_registration_service.py` - Updated to use custom auth
- `app/services/user_service.py` - Updated for AuthenticatedUser compatibility

### API
- `app/api/dependencies.py` - Updated type hints
- `app/api/v1/endpoints/auth.py` - Updated for new auth service

### Database
- `migrations/011_custom_auth_migration.sql` - Add hashed_password column
- `migrations/011_custom_auth_migration.down.sql` - Rollback migration

### Dependencies
- `requirements.txt` - Added PyJWT and bcrypt
