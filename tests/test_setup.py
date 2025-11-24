#!/usr/bin/env python3
"""
Test script to verify Supabase integration is working correctly.
Run this after migration to ensure everything is set up properly.
"""

import os
import sys

# Ensure the project root is on sys.path so `app` package imports work when running
# this file directly (it was failing with ModuleNotFoundError in some environments).
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.core.database import supabase
from app.core.config import settings

def test_config():
    """Test that configuration is loaded correctly."""
    print("🔍 Testing Configuration...")
    try:
        assert settings.SUPABASE_URL, "SUPABASE_URL not set"
        assert settings.SUPABASE_KEY, "SUPABASE_KEY not set"
        print(f"   ✅ SUPABASE_URL: {settings.SUPABASE_URL}")
        print(f"   ✅ SUPABASE_KEY: {'*' * 20}...{settings.SUPABASE_KEY[-10:]}")
        return True
    except Exception as e:
        print(f"   ❌ Configuration Error: {e}")
        return False

def test_supabase_client():
    """Test that Supabase client is initialized."""
    print("\n🔍 Testing Supabase Client...")
    try:
        assert supabase is not None, "Supabase client not initialized"
        assert hasattr(supabase, 'auth'), "Auth module not available"
        assert hasattr(supabase, 'table'), "Table module not available"
        print("   ✅ Supabase client initialized")
        print("   ✅ Auth module available")
        print("   ✅ Table module available")
        return True
    except Exception as e:
        print(f"   ❌ Client Error: {e}")
        return False

def test_auth_methods():
    """Test that auth methods are available."""
    print("\n🔍 Testing Auth Methods...")
    try:
        assert hasattr(supabase.auth, 'sign_up'), "sign_up method not available"
        assert hasattr(supabase.auth, 'sign_in_with_password'), "sign_in_with_password not available"
        assert hasattr(supabase.auth, 'get_user'), "get_user method not available"
        assert hasattr(supabase.auth, 'sign_out'), "sign_out method not available"
        print("   ✅ sign_up method available")
        print("   ✅ sign_in_with_password method available")
        print("   ✅ get_user method available")
        print("   ✅ sign_out method available")
        return True
    except Exception as e:
        print(f"   ❌ Auth Methods Error: {e}")
        return False

def test_table_methods():
    """Test that table query methods are available."""
    print("\n🔍 Testing Table Query Methods...")
    try:
        # Test table builder
        table = supabase.table('test')
        assert hasattr(table, 'select'), "select method not available"
        assert hasattr(table, 'insert'), "insert method not available"
        assert hasattr(table, 'update'), "update method not available"
        assert hasattr(table, 'delete'), "delete method not available"
        print("   ✅ select method available")
        print("   ✅ insert method available")
        print("   ✅ update method available")
        print("   ✅ delete method available")
        return True
    except Exception as e:
        print(f"   ❌ Table Methods Error: {e}")
        return False

def test_imports():
    """Test that all necessary modules can be imported."""
    print("\n🔍 Testing Module Imports...")
    try:
        from app.services.auth_service import AuthService
        print("   ✅ AuthService imported")
        
        from app.services.student_service import StudentService
        print("   ✅ StudentService imported")
        
        from app.services.teacher_service import TeacherService
        print("   ✅ TeacherService imported")
        
        from app.core.security import get_current_user
        print("   ✅ Security module imported")
        
        from app.api.v1.endpoints.auth import router
        print("   ✅ Auth router imported")
        
        return True
    except Exception as e:
        print(f"   ❌ Import Error: {e}")
        return False

def test_fastapi_app():
    """Test that FastAPI app can start."""
    print("\n🔍 Testing FastAPI Application...")
    try:
        from app.main import app
        assert app is not None, "FastAPI app not initialized"
        print("   ✅ FastAPI app initialized")
        print(f"   ✅ App title: {app.title}")
        return True
    except Exception as e:
        print(f"   ❌ FastAPI Error: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("🚀 Supabase Migration Test Suite")
    print("=" * 60)
    
    results = []
    results.append(("Configuration", test_config()))
    results.append(("Supabase Client", test_supabase_client()))
    results.append(("Auth Methods", test_auth_methods()))
    results.append(("Table Methods", test_table_methods()))
    results.append(("Module Imports", test_imports()))
    results.append(("FastAPI App", test_fastapi_app()))
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    failed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Total: {passed + failed} | Passed: {passed} | Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! Migration successful!")
        print("\n📝 Next steps:")
        print("   1. Create your database schema in Supabase Dashboard")
        print("   2. Set up Row Level Security (RLS) policies")
        print("   3. Start the server: uvicorn app.main:app --reload")
        print("   4. Test endpoints at http://127.0.0.1:8000/docs")
        print("=" * 60)
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
