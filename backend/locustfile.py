"""
Locust load testing configuration for Iksan AI Interview Backend.

Usage:
    # Run with web UI (default)
    locust -f locustfile.py --host=http://localhost:8000
    
    # Run headless
    locust -f locustfile.py --headless --users 100 --spawn-rate 10 -H http://localhost:8000
    
    # Run with specific user class
    locust -f locustfile.py StudentUser --host=http://localhost:8000
"""

import os
import random
import time
from locust import HttpUser, task, between, events, tag
from locust.exception import RescheduleTask


# ============================================================================
# Configuration - Set these environment variables or modify defaults
# ============================================================================
TEST_USER_EMAIL = os.getenv("LOCUST_TEST_EMAIL", "test@example.com")
TEST_USER_PASSWORD = os.getenv("LOCUST_TEST_PASSWORD", "testpassword123")

# For registration tests (will append random suffix)
TEST_BASE_EMAIL = os.getenv("LOCUST_BASE_EMAIL", "loadtest")
TEST_EMAIL_DOMAIN = os.getenv("LOCUST_EMAIL_DOMAIN", "example.com")


# ============================================================================
# Event Hooks for test lifecycle
# ============================================================================
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("=" * 60)
    print("Load test starting...")
    print(f"Target host: {environment.host}")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("=" * 60)
    print("Load test completed!")
    print("=" * 60)


# ============================================================================
# Base User Class with common functionality
# ============================================================================
class BaseAPIUser(HttpUser):
    """Base user class with common authentication and API patterns."""
    
    abstract = True  # Don't instantiate this class directly
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.access_token = None
        self.refresh_token = None
        self.user_data = None
    
    def on_start(self):
        """Called when a simulated user starts."""
        # Try to authenticate if credentials are available
        if TEST_USER_EMAIL and TEST_USER_PASSWORD:
            self._login()
    
    def _login(self):
        """Authenticate and store tokens."""
        with self.client.post(
            "/api/v1/auth/login",
            json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            },
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")
                self.user_data = data.get("user")
                response.success()
            elif response.status_code == 429:
                # Rate limited - treat as success
                response.success()
            else:
                response.failure(f"Login failed: {response.status_code}")
    
    def _get_auth_headers(self):
        """Get authorization headers if authenticated."""
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}


# ============================================================================
# Anonymous User - Tests public endpoints without authentication
# ============================================================================
class AnonymousUser(BaseAPIUser):
    """
    Simulates anonymous users accessing public endpoints.
    Weight: 3 (30% of users if mixed with authenticated users)
    """
    
    weight = 3
    
    def on_start(self):
        """Anonymous users don't need to authenticate."""
        pass
    
    @task(5)
    @tag("public", "health")
    def health_check(self):
        """Check API health/root endpoint."""
        with self.client.get("/", name="GET /", catch_response=True) as response:
            if response.status_code == 429:
                response.success()
    
    @task(3)
    @tag("public", "docs")
    def get_api_docs(self):
        """Access OpenAPI documentation."""
        with self.client.get("/docs", name="GET /docs", catch_response=True) as response:
            if response.status_code == 429:
                response.success()
    
    @task(3)
    @tag("public", "schools")
    def list_schools(self):
        """List schools (public endpoint)."""
        skip = random.randint(0, 50)
        limit = random.choice([10, 20, 50])
        with self.client.get(
            f"/api/v1/schools/?skip={skip}&limit={limit}",
            name="GET /api/v1/schools/",
            catch_response=True
        ) as response:
            if response.status_code == 429:
                response.success()
    
    @task(3)
    @tag("public", "majors")
    def list_majors(self):
        """List majors (public endpoint)."""
        skip = random.randint(0, 50)
        limit = random.choice([10, 20, 50])
        with self.client.get(
            f"/api/v1/majors/?skip={skip}&limit={limit}",
            name="GET /api/v1/majors/",
            catch_response=True
        ) as response:
            if response.status_code == 429:
                response.success()
    
    @task(2)
    @tag("public", "roles")
    def list_roles(self):
        """List available roles."""
        with self.client.get("/api/v1/roles/", name="GET /api/v1/roles/", catch_response=True) as response:
            if response.status_code == 429:
                response.success()
    
    @task(2)
    @tag("public", "classes")
    def list_classes(self):
        """List classes."""
        skip = random.randint(0, 20)
        limit = random.choice([10, 20])
        with self.client.get(
            f"/api/v1/classes/?skip={skip}&limit={limit}",
            name="GET /api/v1/classes/",
            catch_response=True
        ) as response:
            if response.status_code == 429:
                response.success()
    
    @task(2)
    @tag("public", "search")
    def search_schools(self):
        """Search schools by name."""
        search_terms = ["고등", "중학", "학교", "서울", "익산"]
        search = random.choice(search_terms)
        with self.client.get(
            f"/api/v1/schools/?search={search}",
            name="GET /api/v1/schools/?search=[term]",
            catch_response=True
        ) as response:
            if response.status_code == 429:
                response.success()
    
    @task(2)
    @tag("public", "search")
    def search_majors(self):
        """Search majors by name."""
        search_terms = ["공학", "과학", "정보", "디자인", "경영"]
        search = random.choice(search_terms)
        with self.client.get(
            f"/api/v1/majors/?search={search}",
            name="GET /api/v1/majors/?search=[term]",
            catch_response=True
        ) as response:
            if response.status_code == 429:
                response.success()


# ============================================================================
# Authenticated User - Tests endpoints requiring authentication
# ============================================================================
class AuthenticatedUser(BaseAPIUser):
    """
    Simulates authenticated users performing various actions.
    Weight: 5 (50% of users)
    """
    
    weight = 5
    wait_time = between(2, 5)
    
    @task(3)
    @tag("auth", "profile")
    def get_current_user(self):
        """Get current user profile."""
        if not self.access_token:
            raise RescheduleTask()
        
        with self.client.get(
            "/api/v1/auth/me",
            headers=self._get_auth_headers(),
            catch_response=True,
            name="GET /api/v1/auth/me"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                # Rate limited - treat as success
                response.success()
            elif response.status_code == 401:
                # Token expired, try to re-login
                self._login()
                response.failure("Token expired, re-authenticating")
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(2)
    @tag("auth", "users")
    def list_users(self):
        """List user profiles with various filters."""
        if not self.access_token:
            raise RescheduleTask()
        
        # Random pagination parameters
        skip = random.randint(0, 50)
        limit = random.choice([10, 20, 50])
        with_role = random.choice(["true", "false"])
        
        with self.client.get(
            f"/api/v1/users/?skip={skip}&limit={limit}&with_role={with_role}",
            headers=self._get_auth_headers(),
            name="GET /api/v1/users/",
            catch_response=True
        ) as response:
            if response.status_code == 429:
                response.success()
    
    @task(2)
    @tag("auth", "teachers")
    def list_teachers(self):
        """List teachers."""
        if not self.access_token:
            raise RescheduleTask()
        
        skip = random.randint(0, 20)
        limit = random.choice([10, 20])
        
        with self.client.get(
            f"/api/v1/teachers/?skip={skip}&limit={limit}",
            headers=self._get_auth_headers(),
            name="GET /api/v1/teachers/",
            catch_response=True
        ) as response:
            if response.status_code == 429:
                response.success()
    
    @task(2)
    @tag("auth", "students")
    def list_students(self):
        """List students."""
        if not self.access_token:
            raise RescheduleTask()
        
        skip = random.randint(0, 50)
        limit = random.choice([10, 20, 50])
        
        with self.client.get(
            f"/api/v1/students/?skip={skip}&limit={limit}",
            headers=self._get_auth_headers(),
            name="GET /api/v1/students/",
            catch_response=True
        ) as response:
            if response.status_code == 429:
                response.success()
    
    @task(1)
    @tag("auth", "public")
    def browse_public_data(self):
        """Browse public data while authenticated."""
        endpoints = [
            "/api/v1/schools/",
            "/api/v1/majors/",
            "/api/v1/roles/",
            "/api/v1/classes/"
        ]
        endpoint = random.choice(endpoints)
        with self.client.get(
            endpoint,
            headers=self._get_auth_headers(),
            name=f"GET {endpoint}",
            catch_response=True
        ) as response:
            if response.status_code == 429:
                response.success()


# ============================================================================
# Student User - Tests student-specific functionality
# ============================================================================
class StudentUser(BaseAPIUser):
    """
    Simulates student users accessing interview sessions.
    Weight: 7 (higher priority for student workflows)
    """
    
    weight = 7
    wait_time = between(3, 8)  # Students spend more time between actions
    
    @task(5)
    @tag("student", "sessions")
    def get_my_sessions(self):
        """Get student's interview session history."""
        if not self.access_token:
            raise RescheduleTask()
        
        skip = random.randint(0, 10)
        limit = random.choice([10, 20])
        status_filter = random.choice([None, "completed", "in_progress", "failed"])
        
        url = f"/api/v1/sessions/?skip={skip}&limit={limit}"
        if status_filter:
            url += f"&status_filter={status_filter}"
        
        with self.client.get(
            url,
            headers=self._get_auth_headers(),
            catch_response=True,
            name="GET /api/v1/sessions/"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                # Rate limited - treat as success
                response.success()
            elif response.status_code == 403:
                # User might not be a student
                response.failure("User is not a student")
            elif response.status_code == 401:
                self._login()
                response.failure("Token expired")
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(3)
    @tag("student", "sessions", "detail")
    def get_session_detail(self):
        """Get details of a specific session."""
        if not self.access_token:
            raise RescheduleTask()
        
        # Try to get a session detail (using random IDs for testing)
        session_id = random.randint(1, 100)
        
        with self.client.get(
            f"/api/v1/sessions/{session_id}",
            headers=self._get_auth_headers(),
            catch_response=True,
            name="GET /api/v1/sessions/[id]"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                # Rate limited - treat as success
                response.success()
            elif response.status_code == 404:
                # Session not found is acceptable in load testing
                response.success()
            elif response.status_code in [401, 403]:
                response.success()  # Expected for testing
            else:
                response.failure(f"Unexpected error: {response.status_code}")
    
    @task(2)
    @tag("student", "profile")
    def check_profile(self):
        """Check student profile."""
        if not self.access_token:
            raise RescheduleTask()
        
        with self.client.get(
            "/api/v1/auth/me",
            headers=self._get_auth_headers(),
            name="GET /api/v1/auth/me",
            catch_response=True
        ) as response:
            if response.status_code == 429:
                response.success()
    
    @task(1)
    @tag("student", "browse")
    def browse_reference_data(self):
        """Browse schools and majors for reference."""
        if random.choice([True, False]):
            with self.client.get(
                "/api/v1/schools/",
                headers=self._get_auth_headers(),
                name="GET /api/v1/schools/",
                catch_response=True
            ) as response:
                if response.status_code == 429:
                    response.success()
        else:
            with self.client.get(
                "/api/v1/majors/",
                headers=self._get_auth_headers(),
                name="GET /api/v1/majors/",
                catch_response=True
            ) as response:
                if response.status_code == 429:
                    response.success()


# ============================================================================
# Auth Stress User - Specifically tests authentication endpoints
# ============================================================================
class AuthStressUser(HttpUser):
    """
    Stress tests authentication endpoints.
    Use with caution due to rate limiting.
    Weight: 1 (lower weight to avoid overwhelming auth system)
    """
    
    weight = 1
    wait_time = between(5, 15)  # Longer wait to respect rate limits
    
    @task(3)
    @tag("auth", "login")
    def login_attempt(self):
        """Attempt login with test credentials."""
        with self.client.post(
            "/api/v1/auth/login",
            json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            },
            catch_response=True,
            name="POST /api/v1/auth/login"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                # Rate limited - expected behavior
                response.success()
            elif response.status_code == 401:
                # Invalid credentials - expected for testing
                response.success()
            else:
                response.failure(f"Unexpected: {response.status_code}")
    
    @task(1)
    @tag("auth", "register")
    def register_attempt(self):
        """Attempt registration (will likely fail due to duplicate)."""
        # Generate a unique email for testing
        unique_suffix = f"{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        test_email = f"{TEST_BASE_EMAIL}_{unique_suffix}@{TEST_EMAIL_DOMAIN}"
        
        with self.client.post(
            "/api/v1/auth/register",
            json={
                "email": test_email,
                "password": "TestPassword123!",
                "full_name": f"Load Test User {unique_suffix}",
                "role_id": random.choice([1, 2, 3])  # Random role
            },
            catch_response=True,
            name="POST /api/v1/auth/register"
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            elif response.status_code == 429:
                # Rate limited
                response.success()
            elif response.status_code == 400:
                # Validation error or duplicate
                response.success()
            else:
                response.failure(f"Unexpected: {response.status_code}")


# ============================================================================
# Heavy Load User - Simulates intensive API usage
# ============================================================================
class HeavyLoadUser(BaseAPIUser):
    """
    Simulates heavy API usage with rapid requests.
    Used for stress testing.
    Weight: 2
    """
    
    weight = 2
    wait_time = between(0.5, 2)  # Shorter wait times for stress testing
    
    @task(10)
    @tag("heavy", "list")
    def rapid_list_requests(self):
        """Rapidly request list endpoints."""
        endpoints = [
            "/api/v1/schools/",
            "/api/v1/majors/",
            "/api/v1/roles/",
            "/api/v1/classes/",
        ]
        
        for _ in range(3):
            endpoint = random.choice(endpoints)
            with self.client.get(endpoint, name=f"GET {endpoint}", catch_response=True) as response:
                if response.status_code == 429:
                    response.success()
    
    @task(5)
    @tag("heavy", "pagination")
    def pagination_stress(self):
        """Test pagination with various parameters."""
        endpoints = [
            "/api/v1/schools/",
            "/api/v1/majors/",
            "/api/v1/classes/"
        ]
        
        endpoint = random.choice(endpoints)
        
        # Test different page sizes
        for limit in [1, 10, 50, 100]:
            skip = random.randint(0, 100)
            with self.client.get(
                f"{endpoint}?skip={skip}&limit={limit}",
                name=f"GET {endpoint}?pagination",
                catch_response=True
            ) as response:
                if response.status_code == 429:
                    response.success()
    
    @task(3)
    @tag("heavy", "search")
    def search_stress(self):
        """Stress test search functionality."""
        search_terms = ["가", "나", "다", "학", "교", "test", ""]
        
        for _ in range(5):
            term = random.choice(search_terms)
            endpoint = random.choice(["/api/v1/schools/", "/api/v1/majors/"])
            
            with self.client.get(
                f"{endpoint}?search={term}",
                name=f"GET {endpoint}?search=[term]",
                catch_response=True
            ) as response:
                if response.status_code == 429:
                    response.success()
