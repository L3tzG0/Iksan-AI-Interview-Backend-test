#!/usr/bin/env python3
"""
Database Migration Management System for Iksan AI Interview Backend

A simple, straightforward migration system that generates SQL files for manual execution
in Supabase SQL Editor. Supports forward (upgrade) and backward (downgrade) migrations
with file-based tracking.

Usage:
    python scripts/migrate.py create               # Interactive migration creation
    python scripts/migrate.py status               # Show migration status
    python scripts/migrate.py upgrade              # Generate upgrade SQL (all pending)
    python scripts/migrate.py upgrade --dry-run    # Preview upgrade SQL
    python scripts/migrate.py downgrade <version>  # Generate downgrade SQL to version
    python scripts/migrate.py mark-applied <version>    # Mark migration as applied
    python scripts/migrate.py mark-unapplied <version>  # Mark migration as unapplied
    python scripts/migrate.py help                 # Show detailed help
"""

import os
import sys
import argparse
import re
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional
import subprocess

# Fix encoding for Windows terminals
if sys.platform == 'win32':
    # Set UTF-8 encoding for stdout/stderr
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class MigrationSystem:
    """Manages database migrations with file-based tracking."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.migrations_dir = self.project_root / "migrations"
        self.tracking_file = self.migrations_dir / "APPLIED_MIGRATIONS.md"
        
        # Ensure migrations directory exists
        self.migrations_dir.mkdir(exist_ok=True)
        
        # Initialize tracking file if it doesn't exist
        if not self.tracking_file.exists():
            self._init_tracking_file()
    
    def _init_tracking_file(self):
        """Initialize the migration tracking markdown file."""
        content = """# Applied Migrations

This file tracks which database migrations have been successfully applied.

**DO NOT EDIT MANUALLY** - Use `python scripts/migrate.py mark-applied <version>` instead.

## Migration History

<!-- Format: | Version | Name | Applied At | Applied By | Notes |
     Example: | 001 | initial_schema | 2025-12-09 10:30:00 | developer@email.com | Initial database setup |
-->

| Version | Name | Applied At | Applied By | Notes |
|---------|------|------------|------------|-------|
"""
        self.tracking_file.write_text(content, encoding='utf-8')
    
    def _get_git_user(self) -> str:
        """Get git user email or fallback to system user."""
        try:
            result = subprocess.run(
                ['git', 'config', 'user.email'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return os.getenv('USERNAME', 'unknown')
    
    def _parse_tracking_file(self) -> List[dict]:
        """Parse the tracking file and return list of applied migrations."""
        applied = []
        content = self.tracking_file.read_text(encoding='utf-8')
        
        # Find the table rows (after the header)
        in_table = False
        for line in content.split('\n'):
            if line.startswith('| Version |'):
                in_table = True
                continue
            if in_table and line.startswith('|') and not line.startswith('|---'):
                parts = [p.strip() for p in line.split('|')[1:-1]]
                if len(parts) >= 4 and parts[0] and parts[0].isdigit():
                    applied.append({
                        'version': parts[0],
                        'name': parts[1],
                        'applied_at': parts[2],
                        'applied_by': parts[3],
                        'notes': parts[4] if len(parts) > 4 else ''
                    })
        
        return applied
    
    def _get_all_migrations(self) -> List[Tuple[str, str]]:
        """Get all migration files (version, name) sorted by version."""
        migrations = []
        
        for file in self.migrations_dir.glob('*.sql'):
            # Skip down migrations
            if file.stem.endswith('.down'):
                continue
            
            # Parse filename: 001_migration_name.sql
            match = re.match(r'^(\d{3})_(.+)$', file.stem)
            if match:
                version = match.group(1)
                name = match.group(2)
                migrations.append((version, name))
        
        return sorted(migrations, key=lambda x: x[0])
    
    def _get_pending_migrations(self) -> List[Tuple[str, str]]:
        """Get migrations that haven't been applied yet."""
        applied = {m['version'] for m in self._parse_tracking_file()}
        all_migrations = self._get_all_migrations()
        return [(v, n) for v, n in all_migrations if v not in applied]
    
    def _read_migration_file(self, version: str, name: str, direction: str = 'up') -> str:
        """Read migration file content."""
        suffix = '.down.sql' if direction == 'down' else '.sql'
        filename = f"{version}_{name}{suffix}"
        filepath = self.migrations_dir / filename
        
        if not filepath.exists():
            return f"-- ERROR: Migration file not found: {filename}\n"
        
        return filepath.read_text(encoding='utf-8')
    
    def create_migration(self):
        """Interactive migration creation."""
        print("\n" + "="*70)
        print("📝 Create New Migration")
        print("="*70)
        
        # Get next version number
        all_migrations = self._get_all_migrations()
        if all_migrations:
            last_version = int(all_migrations[-1][0])
            next_version = f"{last_version + 1:03d}"
        else:
            next_version = "001"
        
        print(f"\nNext version: {next_version}")
        
        # Interactive prompts
        print("\nWhat type of migration is this?")
        print("  1. Create table")
        print("  2. Alter table (add/modify/drop column)")
        print("  3. Create index")
        print("  4. Add constraint")
        print("  5. Data migration")
        print("  6. Custom (write your own)")
        
        choice = input("\nSelect option (1-6): ").strip()
        
        # Get migration name
        print("\nEnter migration name (use snake_case):")
        print("Examples: add_user_avatar, create_notifications_table, add_index_on_email")
        name = input("Name: ").strip().lower().replace(' ', '_').replace('-', '_')
        
        if not name:
            print("❌ Migration name cannot be empty")
            return
        
        # Generate template based on choice
        upgrade_template = self._get_template(choice, next_version, name)
        downgrade_template = self._get_downgrade_template(choice, next_version, name)
        
        # Create files
        upgrade_file = self.migrations_dir / f"{next_version}_{name}.sql"
        downgrade_file = self.migrations_dir / f"{next_version}_{name}.down.sql"
        
        upgrade_file.write_text(upgrade_template, encoding='utf-8')
        downgrade_file.write_text(downgrade_template, encoding='utf-8')
        
        print(f"\n✅ Created migration files:")
        print(f"   📄 {upgrade_file.name}")
        print(f"   📄 {downgrade_file.name}")
        print(f"\n💡 Next steps:")
        print(f"   1. Edit the migration files with your SQL")
        print(f"   2. Run: python scripts/migrate.py upgrade --dry-run")
        print(f"   3. Copy SQL to Supabase SQL Editor and execute")
        print(f"   4. Run: python scripts/migrate.py mark-applied {next_version}")
    
    def _get_template(self, choice: str, version: str, name: str) -> str:
        """Generate migration template based on type."""
        header = f"""-- Migration: {version}_{name}
-- Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- Description: {name.replace('_', ' ').title()}

-- This migration will be executed within a transaction in Supabase SQL Editor
-- Ensure all statements are idempotent where possible

"""
        
        templates = {
            '1': header + """-- Create table with idempotency
CREATE TABLE IF NOT EXISTS your_table_name (
    id BIGSERIAL PRIMARY KEY,
    -- Add your columns here
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_your_table_name_column ON your_table_name(column_name);

-- Add constraints if needed
-- ALTER TABLE your_table_name ADD CONSTRAINT constraint_name CHECK (condition);

-- Grant permissions
GRANT ALL ON your_table_name TO authenticated, service_role;
GRANT USAGE, SELECT ON SEQUENCE your_table_name_id_seq TO authenticated, service_role;
""",
            '2': header + """-- Add column with idempotency check
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'your_table_name' 
        AND column_name = 'new_column_name'
    ) THEN
        ALTER TABLE your_table_name 
        ADD COLUMN new_column_name TEXT;
    END IF;
END $$;

-- Or modify existing column
-- ALTER TABLE your_table_name ALTER COLUMN column_name TYPE new_type;

-- Or drop column (careful!)
-- ALTER TABLE your_table_name DROP COLUMN IF EXISTS old_column_name;
""",
            '3': header + """-- Create index with idempotency
CREATE INDEX IF NOT EXISTS idx_table_column ON table_name(column_name);

-- Or create unique index
-- CREATE UNIQUE INDEX IF NOT EXISTS idx_table_unique_column ON table_name(column_name);

-- Or create partial index
-- CREATE INDEX IF NOT EXISTS idx_table_conditional 
-- ON table_name(column_name) WHERE condition;
""",
            '4': header + """-- Add constraint with idempotency check
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'constraint_name'
    ) THEN
        ALTER TABLE your_table_name 
        ADD CONSTRAINT constraint_name CHECK (condition);
    END IF;
END $$;

-- Or add foreign key
-- ALTER TABLE your_table_name 
-- ADD CONSTRAINT fk_name 
-- FOREIGN KEY (column) REFERENCES other_table(id);
""",
            '5': header + """-- Data migration
-- Example: Update existing records

UPDATE your_table_name
SET column_name = new_value
WHERE condition;

-- Or insert new reference data
INSERT INTO your_table_name (column1, column2)
VALUES 
    ('value1', 'value2'),
    ('value3', 'value4')
ON CONFLICT (unique_column) DO NOTHING;
""",
            '6': header + """-- Custom migration
-- Write your SQL here

"""
        }
        
        return templates.get(choice, templates['6'])
    
    def _get_downgrade_template(self, choice: str, version: str, name: str) -> str:
        """Generate downgrade template based on type."""
        header = f"""-- Migration Downgrade: {version}_{name}
-- Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- Description: Rollback for {name.replace('_', ' ').title()}

-- This migration will revert the changes made in {version}_{name}.sql

"""
        
        templates = {
            '1': header + """-- Drop table (WARNING: This deletes all data!)
DROP TABLE IF EXISTS your_table_name CASCADE;
""",
            '2': header + """-- Revert column changes

-- If you added a column, drop it
-- ALTER TABLE your_table_name DROP COLUMN IF EXISTS new_column_name;

-- If you modified a column, change it back
-- ALTER TABLE your_table_name ALTER COLUMN column_name TYPE original_type;

-- If you dropped a column, recreate it (if possible)
-- ALTER TABLE your_table_name ADD COLUMN old_column_name original_type;
""",
            '3': header + """-- Drop index
DROP INDEX IF EXISTS idx_table_column;
""",
            '4': header + """-- Drop constraint
ALTER TABLE your_table_name DROP CONSTRAINT IF EXISTS constraint_name;
""",
            '5': header + """-- Revert data migration
-- Example: Undo the changes made in upgrade

-- DELETE FROM your_table_name WHERE condition;

-- Or restore original values
-- UPDATE your_table_name 
-- SET column_name = original_value 
-- WHERE condition;
""",
            '6': header + """-- Custom downgrade
-- Write SQL to revert your changes

"""
        }
        
        return templates.get(choice, templates['6'])
    
    def show_status(self):
        """Show current migration status."""
        print("\n" + "="*70)
        print("📊 Migration Status")
        print("="*70)
        
        applied = self._parse_tracking_file()
        all_migrations = self._get_all_migrations()
        pending = self._get_pending_migrations()
        
        print(f"\n✅ Applied: {len(applied)}")
        print(f"⏳ Pending: {len(pending)}")
        print(f"📁 Total:   {len(all_migrations)}")
        
        if applied:
            print("\n" + "="*70)
            print("Applied Migrations:")
            print("="*70)
            for m in applied:
                print(f"  ✅ {m['version']} - {m['name']}")
                print(f"     Applied: {m['applied_at']} by {m['applied_by']}")
        
        if pending:
            print("\n" + "="*70)
            print("Pending Migrations:")
            print("="*70)
            for version, name in pending:
                print(f"  ⏳ {version} - {name}")
            print(f"\n💡 Run: python scripts/migrate.py upgrade")
        else:
            print("\n✨ All migrations are up to date!")
    
    def generate_upgrade_sql(self, dry_run: bool = False):
        """Generate SQL for all pending migrations."""
        pending = self._get_pending_migrations()
        
        if not pending:
            print("\n✨ No pending migrations to apply")
            return
        
        print("\n" + "="*70)
        if dry_run:
            print("🔍 DRY RUN: Upgrade SQL Preview")
        else:
            print("⬆️  Upgrade SQL (Copy to Supabase SQL Editor)")
        print("="*70)
        
        sql_parts = ["BEGIN;", ""]
        
        for version, name in pending:
            sql_parts.append(f"-- ==================== Migration {version}: {name} ====================")
            sql_parts.append(self._read_migration_file(version, name, 'up'))
            sql_parts.append("")
        
        sql_parts.append("COMMIT;")
        sql_parts.append("-- ROLLBACK; -- Uncomment this line if you want to test without committing")
        
        full_sql = "\n".join(sql_parts)
        
        print("\n" + full_sql)
        
        if not dry_run:
            print("\n" + "="*70)
            print("📋 Next Steps:")
            print("="*70)
            print("1. Copy the SQL above")
            print("2. Go to Supabase Dashboard → SQL Editor")
            print("3. Paste and execute the SQL")
            print("4. If successful, mark migrations as applied:")
            for version, name in pending:
                print(f"   python scripts/migrate.py mark-applied {version}")
        else:
            print("\n" + "="*70)
            print("ℹ️  This was a dry run - no changes were made")
            print("="*70)
    
    def generate_downgrade_sql(self, target_version: str, dry_run: bool = False):
        """Generate SQL to downgrade to a specific version."""
        applied = self._parse_tracking_file()
        
        if not applied:
            print("\n❌ No migrations to downgrade")
            return
        
        # Find migrations to rollback (those after target_version)
        to_rollback = [
            (m['version'], m['name']) 
            for m in applied 
            if int(m['version']) > int(target_version)
        ]
        
        if not to_rollback:
            print(f"\n✨ Already at or below version {target_version}")
            return
        
        # Reverse order for downgrade
        to_rollback.reverse()
        
        print("\n" + "="*70)
        if dry_run:
            print(f"🔍 DRY RUN: Downgrade SQL Preview (to version {target_version})")
        else:
            print(f"⬇️  Downgrade SQL to version {target_version} (Copy to Supabase SQL Editor)")
        print("="*70)
        print(f"\n⚠️  WARNING: This will rollback {len(to_rollback)} migration(s)")
        print("Migrations to rollback:")
        for version, name in to_rollback:
            print(f"  - {version}: {name}")
        
        sql_parts = ["BEGIN;", ""]
        
        for version, name in to_rollback:
            sql_parts.append(f"-- ==================== Rollback {version}: {name} ====================")
            sql_parts.append(self._read_migration_file(version, name, 'down'))
            sql_parts.append("")
        
        sql_parts.append("COMMIT;")
        sql_parts.append("-- ROLLBACK; -- Uncomment this line if you want to test without committing")
        
        full_sql = "\n".join(sql_parts)
        
        print("\n" + full_sql)
        
        if not dry_run:
            print("\n" + "="*70)
            print("📋 Next Steps:")
            print("="*70)
            print("1. Copy the SQL above")
            print("2. Go to Supabase Dashboard → SQL Editor")
            print("3. Paste and execute the SQL")
            print("4. If successful, mark migrations as unapplied:")
            for version, name in to_rollback:
                print(f"   python scripts/migrate.py mark-unapplied {version}")
        else:
            print("\n" + "="*70)
            print("ℹ️  This was a dry run - no changes were made")
            print("="*70)
    
    def mark_applied(self, version: str, notes: str = ""):
        """Mark a migration as applied."""
        # Check if migration file exists
        all_migrations = {v: n for v, n in self._get_all_migrations()}
        
        if version not in all_migrations:
            print(f"❌ Migration {version} not found")
            return
        
        # Check if already applied
        applied = self._parse_tracking_file()
        if any(m['version'] == version for m in applied):
            print(f"⚠️  Migration {version} is already marked as applied")
            return
        
        # Add to tracking file
        name = all_migrations[version]
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        user = self._get_git_user()
        
        # Read current content
        content = self.tracking_file.read_text(encoding='utf-8')
        
        # Add new row
        new_row = f"| {version} | {name} | {timestamp} | {user} | {notes} |\n"
        content = content.rstrip() + "\n" + new_row
        
        self.tracking_file.write_text(content, encoding='utf-8')
        
        print(f"✅ Marked migration {version} ({name}) as applied")
        print(f"   Applied at: {timestamp}")
        print(f"   Applied by: {user}")
        print(f"\n💡 Don't forget to commit APPLIED_MIGRATIONS.md:")
        print(f"   git add migrations/APPLIED_MIGRATIONS.md")
        print(f"   git commit -m \"Applied migration {version}: {name}\"")
    
    def mark_unapplied(self, version: str):
        """Mark a migration as unapplied (for rollback)."""
        applied = self._parse_tracking_file()
        
        if not any(m['version'] == version for m in applied):
            print(f"⚠️  Migration {version} is not marked as applied")
            return
        
        # Remove from tracking file
        content = self.tracking_file.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        new_lines = []
        removed = False
        for line in lines:
            if line.startswith(f"| {version} |"):
                removed = True
                continue
            new_lines.append(line)
        
        if removed:
            self.tracking_file.write_text('\n'.join(new_lines), encoding='utf-8')
            print(f"✅ Marked migration {version} as unapplied")
            print(f"\n💡 Don't forget to commit APPLIED_MIGRATIONS.md:")
            print(f"   git add migrations/APPLIED_MIGRATIONS.md")
            print(f"   git commit -m \"Rolled back migration {version}\"")
        else:
            print(f"❌ Failed to remove migration {version} from tracking file")


def print_help():
    """Print detailed help message."""
    help_text = """
╔════════════════════════════════════════════════════════════════════════════╗
║           Database Migration System - Iksan AI Interview                   ║
╚════════════════════════════════════════════════════════════════════════════╝

COMMANDS:

  create                    Create a new migration (interactive)
                           Generates both upgrade and downgrade SQL files

  status                    Show migration status
                           Lists applied and pending migrations

  upgrade                   Generate SQL for all pending migrations
                           Copy output to Supabase SQL Editor

  upgrade --dry-run         Preview upgrade SQL without executing

  downgrade <version>       Generate SQL to rollback to specific version
                           Example: downgrade 002

  downgrade <version> --dry-run
                           Preview downgrade SQL without executing

  mark-applied <version>    Mark migration as applied after manual execution
                           Example: mark-applied 003

  mark-unapplied <version>  Mark migration as unapplied after rollback
                           Example: mark-unapplied 003

  help                      Show this help message

WORKFLOW:

  1. Create new migration:
     $ python scripts/migrate.py create

  2. Edit generated SQL files:
     - migrations/00X_name.sql (upgrade)
     - migrations/00X_name.down.sql (downgrade)

  3. Preview changes:
     $ python scripts/migrate.py upgrade --dry-run

  4. Generate SQL to execute:
     $ python scripts/migrate.py upgrade

  5. Copy SQL to Supabase Dashboard → SQL Editor and execute

  6. Mark as applied:
     $ python scripts/migrate.py mark-applied 00X

  7. Commit tracking file:
     $ git add migrations/APPLIED_MIGRATIONS.md
     $ git commit -m "Applied migration 00X"

EXAMPLES:

  # Create a new migration for adding a column
  $ python scripts/migrate.py create
  > What type: 2 (Alter table)
  > Name: add_user_avatar

  # Check what needs to be applied
  $ python scripts/migrate.py status

  # Test the upgrade SQL
  $ python scripts/migrate.py upgrade --dry-run

  # Generate upgrade SQL
  $ python scripts/migrate.py upgrade
  # Copy to Supabase and execute

  # Mark as applied
  $ python scripts/migrate.py mark-applied 003

  # Rollback if needed
  $ python scripts/migrate.py downgrade 002
  # Copy to Supabase and execute
  $ python scripts/migrate.py mark-unapplied 003

NOTES:

  - All SQL files are executed manually in Supabase SQL Editor
  - Migrations are tracked in migrations/APPLIED_MIGRATIONS.md
  - Always commit APPLIED_MIGRATIONS.md after marking migrations
  - Use --dry-run to preview SQL before executing
  - Downgrade SQL should reverse upgrade changes completely

"""
    print(help_text)


def main():
    parser = argparse.ArgumentParser(
        description="Database Migration Management System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False
    )
    
    parser.add_argument('command', nargs='?', help='Command to execute')
    parser.add_argument('args', nargs='*', help='Command arguments')
    parser.add_argument('--dry-run', action='store_true', help='Preview SQL without executing')
    parser.add_argument('--help', '-h', action='store_true', help='Show help')
    
    args = parser.parse_args()
    
    if args.help or args.command == 'help':
        print_help()
        return
    
    system = MigrationSystem()
    
    if args.command == 'create':
        system.create_migration()
    
    elif args.command == 'status':
        system.show_status()
    
    elif args.command == 'upgrade':
        system.generate_upgrade_sql(dry_run=args.dry_run)
    
    elif args.command == 'downgrade':
        if not args.args:
            print("❌ Please specify target version: downgrade <version>")
            return
        target_version = args.args[0]
        system.generate_downgrade_sql(target_version, dry_run=args.dry_run)
    
    elif args.command == 'mark-applied':
        if not args.args:
            print("❌ Please specify version: mark-applied <version>")
            return
        version = args.args[0]
        notes = args.args[1] if len(args.args) > 1 else ""
        system.mark_applied(version, notes)
    
    elif args.command == 'mark-unapplied':
        if not args.args:
            print("❌ Please specify version: mark-unapplied <version>")
            return
        version = args.args[0]
        system.mark_unapplied(version)
    
    else:
        print(f"❌ Unknown command: {args.command}")
        print("Run: python scripts/migrate.py help")


if __name__ == "__main__":
    main()
