"""
Test script to verify Supabase connection and retrieve schools data
"""
import os
import sys

# Ensure the project root is on sys.path so `app` package imports work when running
# this file directly (prevents ModuleNotFoundError in certain environments).
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from supabase import create_client
from app.core.config import settings

# Create Supabase client for testing (outside of FastAPI request context)
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def test_connection():
    """Test Supabase connection and retrieve schools data"""
    print("=" * 60)
    print("Testing Supabase Database Connection")
    print("=" * 60)
    
    # Display connection info (without showing full key)
    print(f"\nSupabase URL: {settings.SUPABASE_URL}")
    print(f"API Key configured: {'Yes' if settings.SUPABASE_KEY else 'No'}")
    
    try:
        # Test 1: Check connection by querying schools table
        print("\n" + "-" * 60)
        print("Test 1: Retrieving all schools from 'schools' table")
        print("-" * 60)
        
        response = supabase.table('schools').select('*').execute()

        # Check for API errors
        if getattr(response, 'error', None) is not None:
            print(f"\n✗ Supabase error: {getattr(response, 'error', None)}")
            return False

        # Fallback: some client versions return dict-like responses
        data = None
        if hasattr(response, 'data'):
            data = response.data
        elif isinstance(response, dict) and 'data' in response:
            data = response['data']
        else:
            data = []
        
        print(f"\n✓ Connection successful!")
        print(f"✓ Total schools found: {len(data)}")
        
        if data:
            print("\nSchools data:")
            print("-" * 60)
            for idx, school in enumerate(data, 1):
                if isinstance(school, dict):
                    print(f"{idx}. ID: {school.get('id')}, Name: {school.get('school_name')}")
                else:
                    print(f"{idx}. {school}")
        else:
            print("\n⚠ No schools found in the database (table is empty)")
        
        # Test 2: Check table structure
        print("\n" + "-" * 60)
        print("Test 2: Checking schools table structure")
        print("-" * 60)
        
        if data:
            sample_record = data[0]
            if isinstance(sample_record, dict):
                for key in sample_record.keys():
                    print(f"  - {key}: {type(sample_record[key]).__name__}")
            else:
                print("  - Sample record is not a mapping; unable to list keys")
        
        print("\n" + "=" * 60)
        print("✓ All tests passed successfully!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error occurred: {type(e).__name__}")
        print(f"✗ Error message: {str(e)}")
        print("\n" + "=" * 60)
        print("✗ Connection test failed!")
        print("=" * 60)
        return False

if __name__ == "__main__":
    test_connection()
