# Student Account Generation System Flow

## Overview
The system auto-generates student accounts with a 12-digit student ID and secure password. Only teachers and admins can create student accounts (no email required for students).

---

## Student ID Structure (12 digits)
```
[3-digit school][4-digit major][5-digit student number]
```
**Examples:**
- `001000100001` - 1st school, 1st major, 1st student in that school+major combo
- `001000100002` - Same school/major, 2nd student
- `002000200001` - 2nd school, 2nd major, 1st student

---

## Complete Flow

### 1. API Request Validation
**Endpoint:** `POST /api/v1/students/create`

**Authorization Check:**
- Verifies JWT token
- Checks user's `role_id` in `user_profiles` table
- Only allows `role_id = 1` (admin) or `role_id = 2` (teacher)
- Teachers must use their own school; admins can specify any school

**Required Input:**
- `full_name` - Student's name
- `major_name` - Major name (creates if doesn't exist)
- **School:** `school_name` (admin must provide, teacher's school auto-used)
- **Class:** Either `class_id` OR (`class_name` + `grade_level`)

---

### 2. School Resolution (`_resolve_or_create_school`)
- Sanitizes school name (trim whitespace, normalize spaces)
- Searches existing schools (case-insensitive match)
- **If found:** Uses existing school, assigns `school_number` if missing
- **If not found:** Creates new school, assigns next `school_number` (001, 002, etc.)
- Uses database function `assign_school_number()` for atomic increment

---

### 3. Major Resolution (`_resolve_or_create_major`)
- Sanitizes major name
- Searches existing majors (case-insensitive)
- **If found:** Uses existing major, assigns `major_number` if missing
- **If not found:** Creates new major, assigns next `major_number` (0001, 0002, etc.)
- Uses database function `assign_major_number()` for atomic increment

---

### 4. Class Resolution (`_resolve_or_create_class`)
**Option A - Using `class_id`:**
- Validates class exists in database

**Option B - Using `class_name` + `grade_level`:**
- Searches for existing class with same name and grade (case-insensitive)
- **If found:** Reuses existing class
- **If not found:** Creates new class
- **Note:** Classes are NOT scoped to schools (business requirement)

---

### 5. Student ID Generation (`_generate_student_id`)
- Calls `get_next_student_number(school_id, major_id)` database function
- Tracks the last student number per school+major combination
- Atomically increments and returns next number (00001, 00002, etc.)
- Concatenates: `school_number (3) + major_number (4) + student_number (5)`
- **Result:** 12-digit unique student ID (e.g., `001000100001`)

---

### 6. Password Generation (`_generate_secure_password`)
- Generates 12-character random password
- **Requirements met:**
  - At least 1 uppercase letter
  - At least 1 lowercase letter
  - At least 1 digit
  - At least 1 special character (`!@#$%^&*`)
- Shuffles characters for randomness
- Hashes password using SHA-256 for storage in `students.stored_password`

---

### 7. Supabase Auth User Creation (`_create_auth_user`)
**Username Login Workaround:**
- Supabase Auth requires email, but students use student ID
- Creates fake email: `{student_id}@students.internal`
  - Example: `001000100001@students.internal`
- Calls `supabase.auth.admin.create_user()` with:
  - Email: fake email
  - Password: generated password
  - `email_confirm: True` (skips verification)
  - User metadata: `full_name`, `role_id: 3`, `student_id`, `is_student: True`
- Returns `user_id` (UUID)

**Database Trigger:** Automatically creates `user_profiles` record when auth user is created

---

### 8. Student Record Creation (`_create_student_record`)
Inserts into `students` table:
```python
{
    "user_id": UUID,
    "student_id": "001000100001",
    "school_id": int,
    "major_id": int,
    "current_class_id": int,
    "stored_password": hashed_password  # For display/recovery
}
```

---

### 9. Response
Returns `StudentAccountResponse`:
```json
{
    "id": 123,
    "user_id": "uuid...",
    "full_name": "John Doe",
    "student_id": "001000100001",
    "current_class_id": 5,
    "password": "xK9#mP2$vL4!"
}
```

---

## Error Handling & Rollback
- If student record creation fails after auth user creation, the auth user is deleted (cleanup)
- For bulk creation, all students are rolled back if any single creation fails (atomic operation)

---

## Student Login Process (`authenticate_student`)
1. Student provides `student_id` + `password`
2. System converts to fake email: `{student_id}@students.internal`
3. Calls Supabase `sign_in_with_password()` with fake email
4. Returns JWT tokens (access + refresh)

---

## Key Database Functions
- `assign_school_number(p_school_id)` - Atomic school number assignment
- `assign_major_number(p_major_id)` - Atomic major number assignment
- `get_next_student_number(p_school_id, p_major_id)` - Atomic student number increment

These ensure no duplicate IDs even with concurrent requests.
