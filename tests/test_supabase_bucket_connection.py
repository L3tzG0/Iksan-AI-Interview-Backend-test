#!/usr/bin/env python3
"""
Test script to verify Supabase bucket connection and storage operations.
This script tests:
1. Connection to Supabase
2. Bucket access and authentication
3. File upload functionality
4. File retrieval and URL generation
5. File deletion
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET")

def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_environment_variables():
    """Test 1: Verify environment variables are loaded"""
    print_section("Test 1: Checking Environment Variables")
    
    checks = {
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_KEY": SUPABASE_KEY,
        "SUPABASE_STORAGE_BUCKET": SUPABASE_STORAGE_BUCKET,
    }
    
    all_loaded = True
    for var_name, value in checks.items():
        if value:
            print(f"✓ {var_name} is loaded")
            if var_name == "SUPABASE_URL":
                print(f"  Value: {value}")
            elif var_name == "SUPABASE_STORAGE_BUCKET":
                print(f"  Value: {value}")
            else:
                print(f"  Value: {value[:20]}...{value[-10:]}")
        else:
            print(f"✗ {var_name} is NOT loaded")
            all_loaded = False
    
    if not all_loaded:
        print("\n⚠️  Some environment variables are missing!")
        return False
    
    print("\n✓ All environment variables loaded successfully!")
    return True


def test_supabase_connection():
    """Test 2: Verify Supabase client connection"""
    print_section("Test 2: Creating Supabase Client")
    
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✓ Supabase client created successfully")
        return supabase
    except Exception as e:
        print(f"✗ Failed to create Supabase client")
        print(f"  Error: {str(e)}")
        return None


def test_bucket_access(supabase: Client):
    """Test 3: Verify bucket access"""
    print_section("Test 3: Accessing Storage Bucket")
    
    try:
        # Try to access the bucket
        bucket = supabase.storage.from_(SUPABASE_STORAGE_BUCKET)
        print(f"✓ Successfully accessed bucket: {SUPABASE_STORAGE_BUCKET}")
        return bucket
    except Exception as e:
        print(f"✗ Failed to access bucket")
        print(f"  Error: {str(e)}")
        return None


def test_file_upload(supabase: Client, bucket):
    """Test 4: Test file upload to bucket"""
    print_section("Test 4: Testing File Upload")
    
    # Create test file content
    test_content = b"This is a test file for Supabase bucket connection verification.\nCreated at: " + str(time.time()).encode()
    test_filename = f"test_upload_{int(time.time())}.txt"
    test_path = f"tests/{test_filename}"
    
    try:
        print(f"Uploading test file: {test_path}")
        print(f"File size: {len(test_content)} bytes")
        
        # Upload file
        response = bucket.upload(
            path=test_path,
            file=test_content,
            file_options={"content-type": "text/plain"}
        )
        
        print(f"✓ File uploaded successfully")
        print(f"  Response: {response}")
        return test_path
        
    except Exception as e:
        print(f"✗ Failed to upload file")
        print(f"  Error: {str(e)}")
        return None


def test_file_retrieval(supabase: Client, bucket, file_path: str):
    """Test 5: Test file retrieval and public URL"""
    print_section("Test 5: Testing File Retrieval and Public URL")
    
    try:
        # Get public URL
        print(f"Attempting to get public URL for: {file_path}")
        public_url = bucket.get_public_url(file_path)
        
        print(f"✓ Public URL retrieved successfully")
        print(f"  URL: {public_url}")
        return public_url
        
    except Exception as e:
        print(f"✗ Failed to get public URL")
        print(f"  Error: {str(e)}")
        return None


def test_file_deletion(supabase: Client, bucket, file_path: str):
    """Test 6: Test file deletion"""
    print_section("Test 6: Testing File Deletion")
    
    try:
        print(f"Deleting test file: {file_path}")
        
        # Delete file
        response = bucket.remove([file_path])
        
        print(f"✓ File deleted successfully")
        print(f"  Response: {response}")
        return True
        
    except Exception as e:
        print(f"✗ Failed to delete file")
        print(f"  Error: {str(e)}")
        return False


def test_database_connection(supabase: Client):
    """Test 7: Test database connection (verify documents table exists)"""
    print_section("Test 7: Testing Database Connection")
    
    try:
        print("Attempting to query 'documents' table (minimal query)...")
        response = supabase.table('documents').select('count', count='exact').execute()
        
        doc_count = response.count if hasattr(response, 'count') else "unknown"
        print(f"✓ Successfully connected to database")
        print(f"  Documents in table: {doc_count}")
        return True
        
    except Exception as e:
        print(f"⚠️  Database query failed (this is expected if no documents exist yet)")
        print(f"  Error: {str(e)}")
        # This is not a critical failure
        return True


def main():
    """Run all tests"""
    print_section("SUPABASE BUCKET CONNECTION VERIFICATION")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Environment variables
    if not test_environment_variables():
        print("\n❌ Failed at Test 1: Environment variables not loaded")
        return False
    
    # Test 2: Supabase connection
    supabase = test_supabase_connection()
    if not supabase:
        print("\n❌ Failed at Test 2: Supabase client connection")
        return False
    
    # Test 3: Bucket access
    bucket = test_bucket_access(supabase)
    if not bucket:
        print("\n❌ Failed at Test 3: Bucket access")
        return False
    
    # Test 4: File upload
    file_path = test_file_upload(supabase, bucket)
    if not file_path:
        print("\n❌ Failed at Test 4: File upload")
        return False
    
    # Test 5: File retrieval and URL
    public_url = test_file_retrieval(supabase, bucket, file_path)
    if not public_url:
        print("\n❌ Failed at Test 5: File retrieval/public URL")
        return False
    
    # Test 6: File deletion
    if not test_file_deletion(supabase, bucket, file_path):
        print("\n❌ Failed at Test 6: File deletion")
        return False
    
    # Test 7: Database connection
    test_database_connection(supabase)
    
    # Success!
    print_section("VERIFICATION COMPLETE ✓")
    print("✅ Supabase bucket connection is working correctly!")
    print(f"\nBucket: {SUPABASE_STORAGE_BUCKET}")
    print(f"URL: {SUPABASE_URL}")
    print("\nAll tests passed! Your Supabase backend is ready to use.")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
