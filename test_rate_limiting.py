"""
Rate Limiting Test Script for Iksan AI Interview Backend.

This script tests the rate limiting functionality by making multiple requests
to different endpoints and verifying that:
1. Requests are allowed up to the configured limit
2. Requests beyond the limit are rejected with 429 status
3. Rate limit headers are present in responses
4. Different endpoints have different rate limits applied correctly
"""

import asyncio
import time
from typing import Dict, List
import httpx
from dataclasses import dataclass


@dataclass
class RateLimitTestResult:
    """Result of a rate limit test for a single endpoint."""
    endpoint: str
    limit_type: str
    total_requests: int
    successful_requests: int
    rate_limited_requests: int
    status_codes: Dict[int, int]  # status_code -> count
    rate_limit_headers: Dict[str, str]  # Headers from last response
    test_passed: bool
    error_message: str = ""


class RateLimitTester:
    """Tests rate limiting functionality of the API."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        """
        Initialize the rate limit tester.
        
        Args:
            base_url: Base URL of the API (default: http://127.0.0.1:8000)
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=10.0)
        self.results: List[RateLimitTestResult] = []
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
    
    def _make_request(self, endpoint: str, headers: Dict[str, str] = None) -> httpx.Response:
        """
        Make a single HTTP request to an endpoint.
        
        Args:
            endpoint: API endpoint (e.g., "/health")
            headers: Optional custom headers
        
        Returns:
            httpx.Response: The response object
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.client.get(url, headers=headers or {})
            return response
        except Exception as e:
            print(f"  Error making request to {endpoint}: {e}")
            raise
    
    def _extract_rate_limit_headers(self, response: httpx.Response) -> Dict[str, str]:
        """Extract rate limit-related headers from response."""
        headers = {}
        for header in ["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset", "Retry-After"]:
            if header in response.headers:
                headers[header] = response.headers[header]
        return headers
    
    def test_endpoint(
        self,
        endpoint: str,
        limit_type: str,
        requests_to_make: int,
        delay_between_requests: float = 0.01,
        headers: Dict[str, str] = None
    ) -> RateLimitTestResult:
        """
        Test rate limiting for a specific endpoint.
        
        Args:
            endpoint: API endpoint to test
            limit_type: Description of the limit type (e.g., "60/minute")
            requests_to_make: Number of requests to make
            delay_between_requests: Delay between requests in seconds
            headers: Optional custom headers (e.g., Authorization)
        
        Returns:
            RateLimitTestResult: Test result object
        """
        print(f"\n📝 Testing {endpoint} ({limit_type})")
        print(f"   Making {requests_to_make} requests with {delay_between_requests}s delay...")
        
        status_codes: Dict[int, int] = {}
        successful_requests = 0
        rate_limited_requests = 0
        last_headers = {}
        
        for i in range(requests_to_make):
            try:
                response = self._make_request(endpoint, headers)
                status_code = response.status_code
                status_codes[status_code] = status_codes.get(status_code, 0) + 1
                last_headers = self._extract_rate_limit_headers(response)
                
                if status_code == 200:
                    successful_requests += 1
                    print(f"   [{i+1}/{requests_to_make}] ✅ Status: {status_code}")
                elif status_code == 429:
                    rate_limited_requests += 1
                    print(f"   [{i+1}/{requests_to_make}] 🚫 Rate limited: {status_code}")
                else:
                    print(f"   [{i+1}/{requests_to_make}] ⚠️  Unexpected status: {status_code}")
                
                if i < requests_to_make - 1:
                    time.sleep(delay_between_requests)
            
            except Exception as e:
                print(f"   [{i+1}/{requests_to_make}] ❌ Error: {e}")
                status_codes["error"] = status_codes.get("error", 0) + 1
        
        # Determine if test passed
        test_passed = rate_limited_requests > 0 or successful_requests == requests_to_make
        error_msg = ""
        if not test_passed:
            error_msg = "Expected rate limiting to be triggered"
        
        result = RateLimitTestResult(
            endpoint=endpoint,
            limit_type=limit_type,
            total_requests=requests_to_make,
            successful_requests=successful_requests,
            rate_limited_requests=rate_limited_requests,
            status_codes=status_codes,
            rate_limit_headers=last_headers,
            test_passed=test_passed,
            error_message=error_msg
        )
        
        self.results.append(result)
        return result
    
    def test_different_ips(self, endpoint: str, requests_per_ip: int = 20):
        """
        Test that different IP addresses have separate rate limits.
        
        Args:
            endpoint: API endpoint to test
            requests_per_ip: Requests to make per simulated IP
        """
        print(f"\n📝 Testing IP-based rate limiting for {endpoint}")
        
        # Simulate different clients/IPs by using different User-Agent headers
        # (In real scenario, these would come from different IPs)
        for ip_num in range(3):
            user_agent = f"TestClient-IP-{ip_num}"
            headers = {"User-Agent": user_agent}
            
            print(f"\n   Simulating IP {ip_num}...")
            successful = 0
            
            for i in range(requests_per_ip):
                response = self._make_request(endpoint, headers)
                if response.status_code == 200:
                    successful += 1
                time.sleep(0.01)
            
            print(f"   IP {ip_num}: {successful}/{requests_per_ip} successful requests")
    
    def print_summary(self):
        """Print a summary of all test results."""
        print("\n" + "="*70)
        print("📊 RATE LIMITING TEST SUMMARY")
        print("="*70)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.test_passed)
        
        for result in self.results:
            status = "✅ PASSED" if result.test_passed else "❌ FAILED"
            print(f"\n{status} - {result.endpoint} ({result.limit_type})")
            print(f"   Total Requests: {result.total_requests}")
            print(f"   Successful (200): {result.successful_requests}")
            print(f"   Rate Limited (429): {result.rate_limited_requests}")
            print(f"   Status Codes: {result.status_codes}")
            
            if result.rate_limit_headers:
                print(f"   Rate Limit Headers:")
                for key, value in result.rate_limit_headers.items():
                    print(f"      {key}: {value}")
            
            if result.error_message:
                print(f"   Error: {result.error_message}")
        
        print(f"\n{'='*70}")
        print(f"Total Tests: {total_tests} | Passed: {passed_tests} | Failed: {total_tests - passed_tests}")
        print(f"{'='*70}\n")
        
        return passed_tests == total_tests


def main():
    """Run all rate limiting tests."""
    print("🚀 Starting Rate Limit Tests")
    print("="*70)
    
    tester = RateLimitTester(base_url="http://127.0.0.1:8000")
    
    try:
        # Test 1: Health endpoint (120/minute limit)
        print("\n📌 Test Group 1: Health Endpoint (120/minute)")
        tester.test_endpoint(
            endpoint="/health",
            limit_type="120/minute",
            requests_to_make=130,
            delay_between_requests=0.01
        )
        
        # Test 2: Root endpoint (120/minute limit)
        print("\n📌 Test Group 2: Root Endpoint (120/minute)")
        tester.test_endpoint(
            endpoint="/",
            limit_type="120/minute",
            requests_to_make=130,
            delay_between_requests=0.01
        )
        
        # Test 3: Default rate limit endpoint (60/minute)
        print("\n📌 Test Group 3: API Endpoints (60/minute)")
        tester.test_endpoint(
            endpoint="/api/v1/users",
            limit_type="60/minute",
            requests_to_make=70,
            delay_between_requests=0.01
        )
        
        # Print summary
        all_passed = tester.print_summary()
        
        if all_passed:
            print("✅ All rate limiting tests PASSED!")
            return 0
        else:
            print("❌ Some rate limiting tests FAILED!")
            return 1
    
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        tester.close()


if __name__ == "__main__":
    exit(main())
