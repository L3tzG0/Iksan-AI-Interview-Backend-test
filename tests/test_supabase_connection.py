"""
Test script to verify Supabase connection and retrieve schools data
"""
from app.core.database import supabase
from app.core.config import settings

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
        
        print(f"\n✓ Connection successful!")
        print(f"✓ Total schools found: {len(response.data)}")
        
        if response.data:
            print("\nSchools data:")
            print("-" * 60)
            for idx, school in enumerate(response.data, 1):
                print(f"{idx}. ID: {school.get('id')}, Name: {school.get('school_name')}")
        else:
            print("\n⚠ No schools found in the database (table is empty)")
        
        # Test 2: Check table structure
        print("\n" + "-" * 60)
        print("Test 2: Checking schools table structure")
        print("-" * 60)
        
        if response.data:
            sample_record = response.data[0]
            print(f"\nColumns in schools table:")
            for key in sample_record.keys():
                print(f"  - {key}: {type(sample_record[key]).__name__}")
        
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
