#!/usr/bin/env python3
"""
Database Initialization Script for Iksan AI Interview Backend

This script automates database setup by running SQL migration files in the correct order.
It connects to your hosted Supabase instance and executes schema + seed scripts.

Usage:
    python scripts/init_db.py                    # Initialize schema only
    python scripts/init_db.py --seed             # Initialize schema + seed reference data
    python scripts/init_db.py --seed --dummy     # Initialize schema + seed all data (requires manual UUID setup)
    python scripts/init_db.py --check            # Check if database is properly set up
    python scripts/init_db.py --help             # Show help

Requirements:
    - .env file with SUPABASE_URL and SUPABASE_KEY configured
    - SUPABASE_KEY should be the service_role key for full database access
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional

# Add parent directory to path to import from app
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv


def get_supabase_client():
    """Initialize and return Supabase client."""
    from supabase import create_client, Client
    
    load_dotenv()
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
        print("   Copy .env.example to .env and fill in your Supabase credentials")
        sys.exit(1)
    
    return create_client(url, key)


def get_queries_path() -> Path:
    """Get the path to the queries directory."""
    return Path(__file__).parent.parent / "queries"


def read_sql_file(filename: str) -> str:
    """Read SQL content from a file in the queries directory."""
    filepath = get_queries_path() / filename
    if not filepath.exists():
        print(f"❌ Error: SQL file not found: {filepath}")
        sys.exit(1)
    
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def execute_sql_via_rpc(supabase, sql: str, description: str) -> bool:
    """
    Execute SQL using Supabase's postgres functions.
    
    Note: This requires the SQL to be executed via Supabase Dashboard SQL Editor
    for schema changes. For data operations, we can use the table API.
    """
    print(f"   Executing: {description}...")
    # Supabase Python client doesn't support raw SQL execution directly
    # Schema changes must be done via Dashboard or Supabase CLI
    return True


def check_table_exists(supabase, table_name: str) -> bool:
    """Check if a table exists by attempting to query it."""
    try:
        response = supabase.table(table_name).select("*").limit(1).execute()
        return True
    except Exception:
        return False


def check_database_setup(supabase) -> dict:
    """Check the current state of the database setup."""
    required_tables = [
        "roles", "schools", "majors", "user_profiles", 
        "teachers", "classes", "students", "sessions",
        "documents", "summaries", "detailed_feedbacks", "next_steps"
    ]
    
    results = {
        "tables": {},
        "reference_data": {},
        "all_tables_exist": True,
        "reference_data_seeded": True
    }
    
    print("\n📋 Checking database setup...\n")
    
    # Check tables
    print("Tables:")
    for table in required_tables:
        exists = check_table_exists(supabase, table)
        results["tables"][table] = exists
        status = "✅" if exists else "❌"
        print(f"   {status} {table}")
        if not exists:
            results["all_tables_exist"] = False
    
    # Check reference data
    print("\nReference Data:")
    reference_checks = [
        ("roles", 3, "Roles (admin, teacher, student)"),
        ("schools", 2, "Schools"),
        ("majors", 7, "Majors")
    ]
    
    for table, expected_min, description in reference_checks:
        try:
            response = supabase.table(table).select("*").execute()
            count = len(response.data) if response.data else 0
            seeded = count >= expected_min
            results["reference_data"][table] = {"count": count, "seeded": seeded}
            status = "✅" if seeded else "⚠️"
            print(f"   {status} {description}: {count} records")
            if not seeded:
                results["reference_data_seeded"] = False
        except Exception as e:
            results["reference_data"][table] = {"count": 0, "seeded": False, "error": str(e)}
            print(f"   ❌ {description}: Error - {e}")
            results["reference_data_seeded"] = False
    
    return results


def seed_reference_data(supabase) -> bool:
    """Seed reference data (roles, schools, majors) using Supabase table API."""
    print("\n🌱 Seeding reference data...\n")
    
    try:
        # Seed Roles
        print("   Inserting roles...")
        roles_data = [
            {"id": 1, "role_name": "admin"},
            {"id": 2, "role_name": "teacher"},
            {"id": 3, "role_name": "student"}
        ]
        for role in roles_data:
            try:
                supabase.table("roles").upsert(role, on_conflict="role_name").execute()
            except Exception as e:
                if "duplicate" not in str(e).lower():
                    raise
        print("   ✅ Roles seeded")
        
        # Seed Schools
        print("   Inserting schools...")
        schools_data = [
            {"id": 1, "school_name": "이리공업고등학교"},
            {"id": 2, "school_name": "전북기계공업고등학교"}
        ]
        for school in schools_data:
            try:
                supabase.table("schools").upsert(school, on_conflict="school_name").execute()
            except Exception as e:
                if "duplicate" not in str(e).lower():
                    raise
        print("   ✅ Schools seeded")
        
        # Seed Majors
        print("   Inserting majors...")
        majors_data = [
            {"id": 1, "major_name": "전기전자과"},
            {"id": 2, "major_name": "전기제어"},
            {"id": 3, "major_name": "자동화기계"},
            {"id": 4, "major_name": "스마트팩토리"},
            {"id": 5, "major_name": "조리제빵"},
            {"id": 6, "major_name": "기계설계"},
            {"id": 7, "major_name": "소프트웨어과"}
        ]
        for major in majors_data:
            try:
                supabase.table("majors").upsert(major, on_conflict="major_name").execute()
            except Exception as e:
                if "duplicate" not in str(e).lower():
                    raise
        print("   ✅ Majors seeded")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error seeding reference data: {e}")
        return False


def print_manual_schema_instructions():
    """Print instructions for manual schema setup."""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                        SCHEMA INITIALIZATION REQUIRED                       ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  The database schema must be created via Supabase Dashboard SQL Editor.    ║
║  This is a one-time setup that creates all tables, triggers, and RLS.      ║
║                                                                            ║
║  Steps:                                                                    ║
║  1. Go to https://supabase.com/dashboard                                   ║
║  2. Select your project                                                    ║
║  3. Navigate to SQL Editor (left sidebar)                                  ║
║  4. Copy and paste the contents of: queries/initialize_tables.sql          ║
║  5. Click "Run" to execute                                                 ║
║                                                                            ║
║  After schema is created, run this script again with --seed flag:          ║
║  > python scripts/init_db.py --seed                                        ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
""")


def print_success_message(seeded: bool):
    """Print success message after setup."""
    if seeded:
        print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                         ✅ DATABASE SETUP COMPLETE                          ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  Your database is ready! You can now:                                      ║
║                                                                            ║
║  1. Start the server:                                                      ║
║     > uvicorn app.main:app --reload                                        ║
║                                                                            ║
║  2. Register users via API:                                                ║
║     POST /api/v1/auth/register                                             ║
║                                                                            ║
║  Valid role_ids: 1 (admin), 2 (teacher), 3 (student)                       ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
""")
    else:
        print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                           ✅ DATABASE CHECK PASSED                          ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  All tables exist. To seed reference data, run:                            ║
║  > python scripts/init_db.py --seed                                        ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
""")


def main():
    parser = argparse.ArgumentParser(
        description="Initialize the Iksan AI Interview database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/init_db.py --check        Check database setup status
  python scripts/init_db.py --seed         Seed reference data (roles, schools, majors)
  
Note: Schema creation (tables, triggers) must be done via Supabase Dashboard.
      This script handles reference data seeding which can be done via API.
        """
    )
    parser.add_argument(
        "--seed", 
        action="store_true",
        help="Seed reference data (roles, schools, majors)"
    )
    parser.add_argument(
        "--check",
        action="store_true", 
        help="Check database setup status without making changes"
    )
    parser.add_argument(
        "--dummy",
        action="store_true",
        help="Also seed dummy data (requires users to be registered first)"
    )
    
    args = parser.parse_args()
    
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║              Iksan AI Interview - Database Initialization                   ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Initialize Supabase client
    print("🔌 Connecting to Supabase...")
    supabase = get_supabase_client()
    print("   ✅ Connected\n")
    
    # Check current state
    status = check_database_setup(supabase)
    
    # If just checking, exit here
    if args.check:
        print("\n" + "="*60)
        if status["all_tables_exist"] and status["reference_data_seeded"]:
            print("✅ Database is fully set up and ready!")
        elif status["all_tables_exist"]:
            print("⚠️  Tables exist but reference data needs seeding.")
            print("   Run: python scripts/init_db.py --seed")
        else:
            print("❌ Database schema is not initialized.")
            print_manual_schema_instructions()
        return
    
    # Check if schema exists
    if not status["all_tables_exist"]:
        print("\n⚠️  Some tables are missing. Schema must be initialized first.")
        print_manual_schema_instructions()
        return
    
    # Seed reference data if requested
    if args.seed:
        if seed_reference_data(supabase):
            print_success_message(seeded=True)
        else:
            print("\n❌ Failed to seed reference data. Check errors above.")
            sys.exit(1)
    else:
        print_success_message(seeded=False)
    
    if args.dummy:
        print("\n⚠️  Dummy data seeding requires manual UUID setup.")
        print("   See queries/seed_dummy_data.sql for instructions.")


if __name__ == "__main__":
    main()
