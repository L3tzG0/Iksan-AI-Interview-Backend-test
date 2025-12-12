"""
Test script to verify all GET endpoints are working correctly
"""
import requests
from typing import Dict, List

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_get_endpoint(endpoint: str, name: str) -> Dict:
    """Test a GET endpoint and return results"""
    url = f"{BASE_URL}/{endpoint}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        status = "✓ PASS"
        count = len(data) if isinstance(data, list) else 1
        error = None
    except requests.exceptions.RequestException as e:
        status = "✗ FAIL"
        count = 0
        data = None
        error = str(e)
    
    return {
        "name": name,
        "endpoint": endpoint,
        "status": status,
        "count": count,
        "data": data,
        "error": error
    }

def main():
    """Test all GET endpoints"""
    print("=" * 80)
    print("Testing All GET Endpoints")
    print("=" * 80)
    
    # Define all endpoints to test
    endpoints = [
        ("schools/", "Schools"),
        ("majors/", "Majors"),
        ("classes/", "Classes"),
        ("students/", "Students"),
        ("sessions/", "Interview Sessions"),
    ]
    
    results = []
    
    for endpoint, name in endpoints:
        result = test_get_endpoint(endpoint, name)
        results.append(result)
    
    # Display results
    print("\n" + "-" * 80)
    print(f"{'Endpoint':<25} {'Status':<10} {'Records':<10} {'URL':<35}")
    print("-" * 80)
    
    for result in results:
        print(f"{result['name']:<25} {result['status']:<10} {result['count']:<10} /{result['endpoint']}")
    
    # Display detailed results
    print("\n" + "=" * 80)
    print("Detailed Results")
    print("=" * 80)
    
    for result in results:
        print(f"\n{result['name']} ({result['status']})")
        print("-" * 80)
        if result['error']:
            print(f"Error: {result['error']}")
        else:
            if result['count'] > 0:
                print(f"Found {result['count']} record(s)")
                if isinstance(result['data'], list) and len(result['data']) > 0:
                    print("\nSample record:")
                    sample = result['data'][0]
                    for key, value in sample.items():
                        print(f"  {key}: {value}")
            else:
                print("No records found (empty table)")
    
    # Summary
    print("\n" + "=" * 80)
    passed = sum(1 for r in results if r['status'] == "✓ PASS")
    failed = sum(1 for r in results if r['status'] == "✗ FAIL")
    print(f"Summary: {passed} passed, {failed} failed out of {len(results)} endpoints")
    print("=" * 80)
    
    return failed == 0

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
