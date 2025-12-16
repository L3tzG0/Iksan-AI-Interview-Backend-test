# Database Migration Quick Start

This is a **TL;DR** guide for the migration system. For complete documentation, see [migrations/README.md](../migrations/README.md).

## What is this?

A simple file-based migration system where you:
1. Generate SQL files using a Python script
2. Copy SQL to Supabase SQL Editor and execute manually
3. Mark migrations as applied
4. Commit the tracking file to Git

## Quick Commands

```bash
# Create new migration (interactive)
python scripts/migrate.py create

# Check status
python scripts/migrate.py status

# Preview SQL (dry run)
python scripts/migrate.py upgrade --dry-run

# Generate upgrade SQL
python scripts/migrate.py upgrade

# Mark as applied after executing in Supabase
python scripts/migrate.py mark-applied <version>

# Rollback to version
python scripts/migrate.py downgrade <version>
python scripts/migrate.py mark-unapplied <version>
```

## Typical Workflow

### 1. Create Migration
```bash
$ python scripts/migrate.py create
```
- Choose migration type (table, column, index, etc.)
- Enter migration name in snake_case
- Edit generated `.sql` and `.down.sql` files

### 2. Preview Changes
```bash
$ python scripts/migrate.py upgrade --dry-run
```

### 3. Apply Migration
```bash
# Generate SQL
$ python scripts/migrate.py upgrade

# Copy output to Supabase Dashboard → SQL Editor → Run

# Mark as applied
$ python scripts/migrate.py mark-applied 003

# Commit
$ git add migrations/APPLIED_MIGRATIONS.md
$ git commit -m "Applied migration 003: add_user_avatar"
```

## Rules

✅ **DO:**
- Always use `--dry-run` before executing
- Commit `APPLIED_MIGRATIONS.md` after each migration
- Write idempotent SQL (use `IF EXISTS`/`IF NOT EXISTS`)
- Create both upgrade and downgrade SQL

❌ **DON'T:**
- Edit `APPLIED_MIGRATIONS.md` manually
- Skip version numbers
- Modify applied migrations
- Apply migrations out of order

## Example: Add a Column

```bash
# 1. Create
python scripts/migrate.py create
# Type: 2 (Alter table)
# Name: add_phone_to_teachers

# 2. Edit migrations/003_add_phone_to_teachers.sql
# 3. Edit migrations/003_add_phone_to_teachers.down.sql

# 4. Test
python scripts/migrate.py upgrade --dry-run

# 5. Apply
python scripts/migrate.py upgrade
# Execute in Supabase SQL Editor

# 6. Mark
python scripts/migrate.py mark-applied 003

# 7. Commit
git add migrations/
git commit -m "Add phone column to teachers"
```

## Files

- `migrations/APPLIED_MIGRATIONS.md` - Tracks which migrations are applied (commit to git)
- `migrations/00X_name.sql` - Upgrade SQL
- `migrations/00X_name.down.sql` - Downgrade SQL
- `scripts/migrate.py` - CLI tool

## Help

```bash
python scripts/migrate.py help
```

For complete documentation: [migrations/README.md](../migrations/README.md)
