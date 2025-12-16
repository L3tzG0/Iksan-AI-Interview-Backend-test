# Custom Migration System - Implementation Summary

## Overview

A simple, file-based database migration system for managing schema changes in the Iksan AI Interview Backend project. Migrations are executed manually in Supabase SQL Editor with local tracking in Git.

## Key Features Implemented

- **Interactive Migration Creation** - CLI prompts for migration type and name  
- **Forward & Backward Migrations** - Both `.sql` (upgrade) and `.down.sql` (downgrade) files  
- **File-Based Tracking** - `APPLIED_MIGRATIONS.md` tracks applied migrations  
- **Dry-Run Mode** - Preview SQL before execution  
- **Idempotent Templates** - Generated SQL includes existence checks  
- **Git-Friendly** - Markdown tracking file for easy team collaboration  
- **Transaction Wrapping** - Generated SQL wrapped in BEGIN/COMMIT blocks  

## Project Structure

```
Iksan-AI-Interview-Backend/
├── migrations/                          # NEW: Migration files directory
│   ├── APPLIED_MIGRATIONS.md           # Tracks applied migrations (commit to git)
│   ├── README.md                       # Complete migration guide
│   ├── 001_initial_schema.sql          # Initial database schema (upgrade)
│   ├── 001_initial_schema.down.sql     # Initial schema rollback (downgrade)
│   ├── 002_seed_reference_data.sql     # Reference data seeding (upgrade)
│   └── 002_seed_reference_data.down.sql # Reference data removal (downgrade)
├── scripts/
│   ├── migrate.py                      # NEW: Migration management CLI
│   ├── init_db.py                      # LEGACY: Old database setup script
│   └── reset_db.py                     # Database reset script
├── docs/
│   └── MIGRATION_QUICK_START.md        # NEW: Quick reference guide
└── queries/
    └── initialize_tables.sql            # LEGACY: Original schema file
```

## Files Created

### 1. Migration System Core
- **`scripts/migrate.py`**
  - Full-featured CLI for migration management
  - Commands: create, status, upgrade, downgrade, mark-applied, mark-unapplied, help
  - Interactive prompts for migration creation
  - Dry-run mode for previewing SQL

### 2. Migration Directory
- **`migrations/APPLIED_MIGRATIONS.md`**
  - Markdown table tracking applied migrations
  - Columns: Version, Name, Applied At, Applied By, Notes
  - Git-friendly format for team collaboration

- **`migrations/README.md`**
  - Complete documentation with examples
  - Workflow guides and best practices
  - Template explanations and troubleshooting
  - Team collaboration guidelines

### 3. Initial Migrations
- **`migrations/001_initial_schema.sql`**
  - Complete database schema from `queries/initialize_tables.sql`
  - Tables: roles, schools, majors, user_profiles, teachers, students, etc.
  - Triggers: auto-update timestamps, auth user profile creation
  - Permissions: grants for service_role, authenticated, anon

- **`migrations/001_initial_schema.down.sql`**
  - Rollback script to drop all tables and triggers
  - Properly ordered (reverse dependency order)

- **`migrations/002_seed_reference_data.sql`**
  - Seeds roles (admin, teacher, student)
  - Seeds schools (이리공업고등학교, 전북기계공업고등학교)
  - Seeds majors (7 majors)
  - Idempotent with ON CONFLICT DO NOTHING

- **`migrations/002_seed_reference_data.down.sql`**
  - Removes seeded reference data
  - Resets sequences

### 4. Documentation
- **`docs/MIGRATION_QUICK_START.md`**
  - TL;DR guide for developers
  - Quick command reference
  - Example workflows

## CLI Commands

### Basic Commands

```bash
# Create new migration (interactive)
python scripts/migrate.py create

# Show migration status
python scripts/migrate.py status

# Generate upgrade SQL
python scripts/migrate.py upgrade

# Generate upgrade SQL (dry-run)
python scripts/migrate.py upgrade --dry-run

# Generate downgrade SQL
python scripts/migrate.py downgrade <version>

# Mark migration as applied
python scripts/migrate.py mark-applied <version>

# Mark migration as unapplied
python scripts/migrate.py mark-unapplied <version>

# Show detailed help
python scripts/migrate.py help
```

### Interactive Prompts (create command)

The `create` command offers 6 migration types with pre-built templates:

1. **Create table** - Full table creation with indexes and permissions
2. **Alter table** - Add/modify/drop columns with idempotency
3. **Create index** - Index creation with IF NOT EXISTS
4. **Add constraint** - Constraints with existence checks
5. **Data migration** - Update/insert data operations
6. **Custom** - Blank template for custom SQL

## Developer Workflow

### Standard Workflow

```bash
# 1. Create migration
python scripts/migrate.py create
# [Interactive prompts]

# 2. Edit generated SQL files
# migrations/00X_name.sql (upgrade)
# migrations/00X_name.down.sql (downgrade)

# 3. Preview changes
python scripts/migrate.py upgrade --dry-run

# 4. Generate SQL
python scripts/migrate.py upgrade

# 5. Execute in Supabase SQL Editor
# [Copy SQL and run in Supabase Dashboard]

# 6. Mark as applied
python scripts/migrate.py mark-applied 00X

# 7. Commit tracking file
git add migrations/APPLIED_MIGRATIONS.md
git commit -m "Applied migration 00X: description"
git push
```

### Team Collaboration

```bash
# Developer A creates migration
python scripts/migrate.py create
git add migrations/
git commit -m "Add migration 003: add_user_avatar"
git push

# Developer B pulls and applies
git pull
python scripts/migrate.py status
python scripts/migrate.py upgrade
# [Execute in Supabase]
python scripts/migrate.py mark-applied 003
git add migrations/APPLIED_MIGRATIONS.md
git commit -m "Applied migration 003"
git push
```

## Technical Details

### Tracking Mechanism
- **File-based** using Markdown table format
- **Git-controlled** for team synchronization
- **No database table** required (keeps it simple)
- **Includes metadata**: version, name, timestamp, user, notes

### Version Numbering
- **Sequential 3-digit numbers**: 001, 002, 003...
- **Linear progression** (no branching)
- **Next version auto-calculated** from existing migrations

### SQL Generation
- **Transaction-wrapped**: All migrations wrapped in BEGIN/COMMIT
- **Idempotency hints**: Templates include IF EXISTS checks
- **Combined output**: Multiple pending migrations in single SQL block
- **Rollback comment**: Includes ROLLBACK comment for testing

### Safety Features
- **Dry-run mode**: Preview before execution
- **Manual execution**: No automatic database changes
- **Explicit marking**: Must manually mark migrations as applied
- **Git tracking**: Commit tracking file for audit trail

## Templates Provided

### Create Table Template
```sql
CREATE TABLE IF NOT EXISTS your_table_name (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_table_column ON table_name(column);
GRANT ALL ON table_name TO authenticated, service_role;
```

### Add Column Template
```sql
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'table_name' AND column_name = 'new_column'
    ) THEN
        ALTER TABLE table_name ADD COLUMN new_column TEXT;
    END IF;
END $$;
```

### Create Index Template
```sql
CREATE INDEX IF NOT EXISTS idx_table_column 
ON table_name(column_name);
```

### Data Migration Template
```sql
INSERT INTO table_name (col1, col2)
VALUES ('val1', 'val2')
ON CONFLICT (unique_column) DO NOTHING;
```

## Integration with Existing System

### Compatibility with Legacy Scripts
- **`scripts/init_db.py`** still works for initial setup
- **`queries/initialize_tables.sql`** preserved as reference
- **Migration system** is additive, doesn't break existing workflow

### Migration from Legacy
- Initial schema extracted to `001_initial_schema.sql`
- Reference data extracted to `002_seed_reference_data.sql`
- New projects should use migration system
- Existing setups can continue with legacy or migrate

### README Updates
- Added migration option to "Set Up Database" section
- Updated project structure to show migrations directory
- Links to migration documentation

## Best Practices Implemented

### Idempotency
- Templates use `IF NOT EXISTS` / `IF EXISTS`
- Data migrations use `ON CONFLICT DO NOTHING`
- Encourages safe re-execution

### Version Control
- Tracking file is markdown (readable diffs)
- Migration files are SQL (easy review)
- Commit messages template provided

### Documentation
- Complete README with examples
- Quick start guide for TL;DR
- Help command in CLI
- Comments in generated SQL

### Developer Experience
- Interactive prompts for ease of use
- Dry-run mode prevents mistakes
- Clear status display
- Helpful error messages

## Limitations & Trade-offs

### Manual Execution Required
- **By design**: All SQL executed manually in Supabase Editor
- **Benefit**: Full visibility and control
- **Trade-off**: Not automated (but safer for hosted DB)

### Single Environment Focus
- **Optimized for**: Single development environment
- **Multi-env**: Requires multiple tracking files or DB table
- **Current choice**: Keep it simple for single env

### Linear Versioning
- **No branching**: Sequential version numbers only
- **Merge conflicts**: Developers must coordinate version numbers
- **Resolution**: Rename migration to next available number

### No Automatic Rollback
- **Manual process**: Generate downgrade SQL and execute manually
- **Why**: Safety and visibility
- **Alternative**: Could add auto-rollback in future

### Not Planned (By Design)
- Automatic execution (manual is safer)
- Complex branching (linear is simpler)
- Schema comparison/diffing (unnecessary complexity)
- Multiple environment tracking (single env focus)

## Conclusion

The custom migration system provides:
- Simple, straightforward migration management
- Full developer control over schema changes
- Git-friendly tracking for team collaboration
- Interactive CLI for easy creation
- Dry-run safety for preview before execution
- Idempotent templates for safe operations
- Comprehensive documentation for onboarding

The system balances **simplicity** with **functionality**, avoiding unnecessary complexity while providing all essential migration features for a single-environment, team-based development workflow.

## Next Steps for Developers

1. **Read the Quick Start**: `docs/MIGRATION_QUICK_START.md`
2. **Explore the CLI**: `python scripts/migrate.py help`
3. **Review existing migrations**: Check `migrations/` directory
4. **Try dry-run mode**: `python scripts/migrate.py upgrade --dry-run`
5. **Create a test migration**: `python scripts/migrate.py create`

---

**Implementation Date**: December 9, 2025  
