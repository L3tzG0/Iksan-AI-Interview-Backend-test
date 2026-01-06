import os
import random
import time
from locust import HttpUser, task, between, events, tag
from locust.exception import RescheduleTask
import io
from app.core.config import settings

# ============================================================================
# Configuration - Set these environment variables or modify defaults
# ============================================================================
TEST_USER_EMAIL = "test@email.com"
TEST_USER_PASSWORD = "123456"

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
    
class InterviewLoadTester(BaseAPIUser):
    """
    Simulates a student initiating an interview session 
    via both raw text and PDF file uploads.
    """
    wait_time = between(5, 10)

    @tag('initiate_with_file')
    @task(3) # Weight of 3: More frequent than raw text
    def initiate_with_pdf(self):
        if not self.access_token:
            return

        # A valid, minimal 1-page PDF file content (base64 encoded)
        # This is better than b"A"*500000 because it won't crash the parser
        minimal_pdf = (
            b"%PDF-1.1\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << >> "
            b"/Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 21 >>\n"
            b"stream\nBT /F1 12 Tf (Hello) Tj ET\nendstream\nendobj\n"
            b"xref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n"
            b"0000000052 00000 n\n0000000101 00000 n\n0000000178 00000 n\n"
            b"trailer\n<< /Size 5 /Root 1 0 obj >>\nstartxref\n249\n%%EOF"
        )
        
        file_obj = io.BytesIO(minimal_pdf)
        files = {"file": ("resume_load_test.pdf", file_obj, "application/pdf")}
        
        form_data = {
            "field": "Engineering",
            "role": "Backend Developer"
        }

        self._send_initiate_request(data=form_data, files=files)

    @tag('initiate_with_text')
    @task(1) # Weight of 1: Less frequent
    def initiate_with_text(self):
        """Simulates sending raw text instead of a file."""
        if not self.access_token:
            return

        form_data = {
            "field": "Data Science",
            "role": "Researcher",
            "raw_text": "Experienced data scientist with a focus on LLMs and scalability."
        }

        # For multipart/form-data with no file, we still use 'data'
        self._send_initiate_request(data=form_data, files=None)

    def _send_initiate_request(self, data, files):
        """Helper to handle the POST request logic."""
        with self.client.post(
            "/api/v1/sessions/initiate",
            data=data,
            files=files,
            headers=self._get_auth_headers(),
            catch_response=True
        ) as response:
            if response.status_code in [200, 202]:
                response.success()
            # 2. Treat 409 as Success (User Concurrency Limit)
            elif response.status_code == 409:
                # response.success()
                response.failure("Single user spam problem")
            # 3. Handle Auth Expiration (Still a failure because it requires re-login)
            elif response.status_code == 401:
                response.failure("Auth Expired - Re-logging")
                self._login() 
            else:
                response.failure(f"Failed {response.status_code}: {response.text[:100]}")