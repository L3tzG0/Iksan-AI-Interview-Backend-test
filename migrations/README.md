# Database Migrations Guide

This directory contains database migrations for the Iksan AI Interview Backend project.

## Overview

Our migration system is a **simple, file-based approach** where:
- Migrations are versioned SQL files (001, 002, 003...)
- Each migration has an **upgrade** (`.sql`) and **downgrade** (`.down.sql`) file
- Migrations are executed **manually** in Supabase SQL Editor
- Applied migrations are tracked in `APPLIED_MIGRATIONS.md`
- The system provides **dry-run mode** to preview changes before execution

## Directory Structure

```
migrations/
├── APPLIED_MIGRATIONS.md              # Tracks which migrations are applied
├── README.md                          # This file
├── 001_initial_schema.sql             # Upgrade: Initial database schema
├── 001_initial_schema.down.sql        # Downgrade: Rollback initial schema
├── 002_seed_reference_data.sql        # Upgrade: Seed roles, schools, majors
├── 002_seed_reference_data.down.sql   # Downgrade: Remove reference data
└── 00X_your_migration.sql             # Future migrations...
```

## Migration CLI Tool

The `scripts/migrate.py` script provides commands to manage migrations:

```bash
python scripts/migrate.py <command> [options]
```

### Available Commands

| Command | Description |
|---------|-------------|
| `create` | Create a new migration (interactive prompts) |
| `status` | Show which migrations are applied/pending |
| `upgrade` | Generate SQL for all pending migrations |
| `upgrade --dry-run` | Preview upgrade SQL without executing |
| `downgrade <version>` | Generate SQL to rollback to specific version |
| `downgrade <version> --dry-run` | Preview downgrade SQL |
| `mark-applied <version>` | Mark migration as applied after manual execution |
| `mark-unapplied <version>` | Mark migration as unapplied after rollback |
| `help` | Show detailed help message |

## Complete Workflow

### 1️⃣ Create a New Migration

```bash
python scripts/migrate.py create
```

**Interactive prompts will ask:**
- **Type of migration**: Table, column, index, constraint, data, or custom
- **Migration name**: Use snake_case (e.g., `add_user_avatar`)

**Generated files:**
```
migrations/003_add_user_avatar.sql        # Upgrade SQL
migrations/003_add_user_avatar.down.sql   # Downgrade SQL
```

### 2️⃣ Edit the Migration Files

Open the generated `.sql` files and write your SQL:

**Example: `003_add_user_avatar.sql`**
```sql
-- Migration: 003_add_user_avatar
-- Description: Add avatar_url column to user_profiles

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_profiles' 
        AND column_name = 'avatar_url'
    ) THEN
        ALTER TABLE user_profiles 
        ADD COLUMN avatar_url TEXT;
    END IF;
END $$;
```

**Example: `003_add_user_avatar.down.sql`**
```sql
-- Migration Downgrade: 003_add_user_avatar
-- Description: Remove avatar_url column

ALTER TABLE user_profiles DROP COLUMN IF EXISTS avatar_url;
```

### 3️⃣ Preview Changes (Dry Run)

```bash
python scripts/migrate.py upgrade --dry-run
```

This shows you the **exact SQL** that would be generated without making changes.

### 4️⃣ Generate Upgrade SQL

```bash
python scripts/migrate.py upgrade
```

**Output:**
```sql
BEGIN;

-- ==================== Migration 003: add_user_avatar ====================
-- Migration: 003_add_user_avatar
-- Description: Add avatar_url column to user_profiles

DO $$
BEGIN
    IF NOT EXISTS (...) THEN
        ALTER TABLE user_profiles ADD COLUMN avatar_url TEXT;
    END IF;
END $$;

COMMIT;
-- ROLLBACK; -- Uncomment to test without committing
```

### 5️⃣ Execute in Supabase

1. **Copy the generated SQL**
2. Go to **Supabase Dashboard** → **SQL Editor**
3. **Paste** the SQL
4. **Run** the query
5. Verify success (no errors)

### 6️⃣ Mark Migration as Applied

```bash
python scripts/migrate.py mark-applied 003
```

**Output:**
```
✅ Marked migration 003 (add_user_avatar) as applied
   Applied at: 2025-12-09 14:30:00
   Applied by: developer@example.com

💡 Don't forget to commit APPLIED_MIGRATIONS.md:
   git add migrations/APPLIED_MIGRATIONS.md
   git commit -m "Applied migration 003: add_user_avatar"
```

### 7️⃣ Commit the Tracking File

```bash
git add migrations/APPLIED_MIGRATIONS.md
git commit -m "Applied migration 003: add_user_avatar"
git push
```

This ensures **team members** know which migrations have been applied.

## Check Migration Status

At any time, check which migrations are pending:

```bash
python scripts/migrate.py status
```

**Example output:**
```
📊 Migration Status
======================================================================

✅ Applied: 2
⏳ Pending: 1
📁 Total:   3

======================================================================
Applied Migrations:
======================================================================
  ✅ 001 - initial_schema
     Applied: 2025-12-09 10:00:00 by developer@example.com
  ✅ 002 - seed_reference_data
     Applied: 2025-12-09 10:05:00 by developer@example.com

======================================================================
Pending Migrations:
======================================================================
  ⏳ 003 - add_user_avatar

💡 Run: python scripts/migrate.py upgrade
```

## Rolling Back Migrations

### Downgrade to a Specific Version

If you need to rollback migration 003 and return to version 002:

```bash
# Preview the downgrade SQL
python scripts/migrate.py downgrade 002 --dry-run

# Generate the downgrade SQL
python scripts/migrate.py downgrade 002
```

**Output:**
```sql
BEGIN;

-- ==================== Rollback 003: add_user_avatar ====================
ALTER TABLE user_profiles DROP COLUMN IF EXISTS avatar_url;

COMMIT;
```

### Execute Rollback

1. **Copy the SQL**
2. **Execute in Supabase SQL Editor**
3. **Mark as unapplied:**

```bash
python scripts/migrate.py mark-unapplied 003
```

4. **Commit the change:**

```bash
git add migrations/APPLIED_MIGRATIONS.md
git commit -m "Rolled back migration 003"
```

## Best Practices

### ✅ DO

- **Write idempotent migrations** using `IF NOT EXISTS` / `IF EXISTS`
- **Test migrations with `--dry-run`** before executing
- **Always create both upgrade AND downgrade** migrations
- **Commit `APPLIED_MIGRATIONS.md`** after each migration
- **Use descriptive migration names** in snake_case
- **Keep migrations small and focused** (one logical change per migration)
- **Test rollback procedures** in development

### ❌ DON'T

- **Don't edit `APPLIED_MIGRATIONS.md` manually** - use `mark-applied` command
- **Don't skip version numbers** - use sequential numbering (001, 002, 003...)
- **Don't modify existing migration files** after they've been applied
- **Don't apply migrations out of order** - always apply in sequence
- **Don't forget to commit tracking file** after marking migrations

## Migration Templates

The `create` command provides templates for common operations:

### 1. Create Table
```sql
CREATE TABLE IF NOT EXISTS your_table_name (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

GRANT ALL ON your_table_name TO authenticated, service_role;
```

### 2. Add Column
```sql
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'table_name' 
        AND column_name = 'new_column'
    ) THEN
        ALTER TABLE table_name ADD COLUMN new_column TEXT;
    END IF;
END $$;
```

### 3. Create Index
```sql
CREATE INDEX IF NOT EXISTS idx_table_column 
ON table_name(column_name);
```

### 4. Add Constraint
```sql
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'constraint_name'
    ) THEN
        ALTER TABLE table_name 
        ADD CONSTRAINT constraint_name CHECK (condition);
    END IF;
END $$;
```

### 5. Data Migration
```sql
UPDATE table_name
SET column_name = new_value
WHERE condition;

-- Or insert with idempotency
INSERT INTO table_name (col1, col2)
VALUES ('val1', 'val2')
ON CONFLICT (unique_column) DO NOTHING;
```

## Team Collaboration

### For Multiple Developers

1. **Pull latest migrations before creating new ones:**
   ```bash
   git pull origin main
   python scripts/migrate.py status
   ```

2. **Apply pending migrations:**
   ```bash
   python scripts/migrate.py upgrade
   # Execute in Supabase SQL Editor
   python scripts/migrate.py mark-applied <version>
   git add migrations/APPLIED_MIGRATIONS.md
   git commit -m "Applied migration <version>"
   ```

3. **Create new migration:**
   ```bash
   python scripts/migrate.py create
   # Edit migration files
   git add migrations/
   git commit -m "Add migration: <description>"
   git push
   ```

4. **Notify team members** to apply the new migration

### Merge Conflict Resolution

If two developers create migrations at the same time:

1. **Rename conflicting migration** to next available version
2. **Update `APPLIED_MIGRATIONS.md`** manually if needed
3. **Commit the resolution**

## Troubleshooting

### Migration Failed in Supabase

1. **Check error message** in Supabase SQL Editor
2. **Fix the migration file**
3. **Rollback** if partially applied:
   ```bash
   # Manually rollback in SQL Editor or use downgrade SQL
   python scripts/migrate.py downgrade <previous_version>
   ```
4. **Re-run corrected migration**

### Tracking File Out of Sync

If `APPLIED_MIGRATIONS.md` doesn't match database state:

1. **Check database directly** (query information_schema)
2. **Manually edit tracking file** (only in this case!)
3. **Document the correction** in commit message

### Dry Run Shows Wrong SQL

Ensure you've **saved all changes** to migration files before running dry-run.

## Examples

### Example 1: Add a New Column

```bash
# Create migration
python scripts/migrate.py create
# Select: 2 (Alter table)
# Name: add_phone_to_teachers

# Edit migrations/003_add_phone_to_teachers.sql
# Edit migrations/003_add_phone_to_teachers.down.sql

# Preview
python scripts/migrate.py upgrade --dry-run

# Apply
python scripts/migrate.py upgrade
# Execute in Supabase

# Mark as applied
python scripts/migrate.py mark-applied 003

# Commit
git add migrations/
git commit -m "Add phone column to teachers table"
```

### Example 2: Create Index for Performance

```bash
python scripts/migrate.py create
# Select: 3 (Create index)
# Name: add_index_sessions_status

# Edit the files, preview, apply, mark, commit
```

### Example 3: Rollback Last Migration

```bash
# Check status
python scripts/migrate.py status

# Generate rollback SQL
python scripts/migrate.py downgrade 002

# Execute in Supabase SQL Editor

# Mark as unapplied
python scripts/migrate.py mark-unapplied 003

# Commit
git add migrations/APPLIED_MIGRATIONS.md
git commit -m "Rolled back migration 003"
```

## FAQ

**Q: Can I run migrations automatically on app startup?**  
A: No, this system requires manual execution in Supabase SQL Editor for safety and visibility.

**Q: What if I need to modify an applied migration?**  
A: Create a new migration to make the change. Don't edit existing applied migrations.

**Q: Can I apply multiple pending migrations at once?**  
A: Yes! `python scripts/migrate.py upgrade` generates SQL for ALL pending migrations.

**Q: How do I handle production migrations?**  
A: Same process, but **test in staging first** and have a rollback plan ready.

**Q: Can I reuse version numbers?**  
A: No, always use the next sequential number. Never reuse or skip numbers.

## Support

For issues or questions:
1. Check this README
2. Run `python scripts/migrate.py help`
3. Ask team lead or senior developer

---

**Remember:** Migrations are permanent changes to your database. Always:
- Use `--dry-run` before executing
- Test in development first
- Have a rollback plan
- Commit tracking file after changes
