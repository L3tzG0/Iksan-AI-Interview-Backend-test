# Interview Session Initiation - Documentation

## Overview

The interview session initiation process allows students to upload documents (resume, portfolio, etc.) to start a new AI interview session. The system processes the document synchronously, extracting text content and storing it for interview generation.

## Architecture

### Flow Diagram

```
Frontend → Upload Document → Backend API
                                ↓
                        Validate File
                                ↓
                    Create Session (status: "in_progress")
                                ↓
                    Upload to Supabase Storage
                                ↓
                    Extract Text from Document
                                ↓
                    Save Document Record to DB
                                ↓
                        Return Response
                                ↓
            (If any step fails → Rollback)
```

### Components

#### 1. Storage Service (`app/services/storage_service.py`)
Handles all Supabase storage operations:
- **File Validation** - Checks file type and size
- **Upload** - Stores files in organized bucket structure
- **Delete** - Removes files (used in rollback)
- **URL Generation** - Creates public/signed URLs

#### 2. Text Extraction Service (`app/services/text_extraction_service.py`)
Extracts text content from uploaded documents:
- **PDF** - Uses PyPDF2/pdfplumber (to be implemented)
- **DOCX** - Uses python-docx (to be implemented)
- **TXT/MD** - Direct text reading (to be implemented)
- **Current Status** - Returns placeholder text

#### 3. Document Service (`app/services/document_service.py`)
Manages document database records:
- **Create Document** - Inserts document metadata and extracted text
- **Get Document** - Retrieves document by session ID

#### 4. Interview Session Service (`app/services/interview_session_service.py`)
Manages interview session records:
- **Create Session** - Creates new session with initial status
- **Update Status** - Updates session state and completion data
- **Delete Session** - Hard delete for rollback scenarios
- **Get Session** - Retrieves session by ID

## API Endpoint

### POST `/api/v1/interview-sessions/initiate`

Initiates a new interview session by uploading a document.

#### Request

**Content-Type:** `multipart/form-data`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | UploadFile | Yes | Document file (PDF, DOCX, TXT, MD) |
| `student_id` | integer | Yes | ID of the student initiating the session |

**Example using cURL:**

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/interview-sessions/initiate" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/resume.pdf" \
  -F "student_id=123"
```

**Example using Python requests:**

```python
import requests

url = "http://127.0.0.1:8000/api/v1/interview-sessions/initiate"

files = {
    'file': ('resume.pdf', open('resume.pdf', 'rb'), 'application/pdf')
}
data = {
    'student_id': 123
}

response = requests.post(url, files=files, data=data)
print(response.json())
```

**Example using JavaScript fetch:**

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('student_id', 123);

const response = await fetch('http://127.0.0.1:8000/api/v1/interview-sessions/initiate', {
  method: 'POST',
  body: formData
});

const data = await response.json();
console.log(data);
```

#### Response

**Success (200 OK):**

```json
{
  "session_id": 456,
  "student_id": 123,
  "status": "in_progress",
  "document": {
    "id": 789,
    "document_path": "interviews/123/456/20251124_103000_a1b2c3d4_resume.pdf",
    "processed_at": "2025-11-24T10:30:00.000000"
  },
  "created_at": "2025-11-24T10:30:00.000000"
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | integer | Unique ID of the created interview session |
| `student_id` | integer | ID of the student |
| `status` | string | Current session status (always "in_progress" on creation) |
| `document.id` | integer | Unique ID of the document record |
| `document.document_path` | string | Storage path in Supabase bucket |
| `document.processed_at` | string (ISO 8601) | Timestamp when text extraction completed |
| `created_at` | string (ISO 8601) | Session creation timestamp |

**Error Responses:**

| Status Code | Reason | Example Response |
|-------------|--------|------------------|
| `400 Bad Request` | Invalid file type | `{"detail": "Invalid file type. Allowed types: application/pdf, ..."}` |
| `400 Bad Request` | File too large | `{"detail": "File too large. Maximum size: 10.0MB"}` |
| `500 Internal Server Error` | Upload failure | `{"detail": "Failed to upload file to storage: ..."}` |
| `500 Internal Server Error` | Database error | `{"detail": "Database error while creating session: ..."}` |

## Configuration

### Environment Variables

Required in `.env` file:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_STORAGE_BUCKET=iksan-ai-interview

# File Upload Configuration
MAX_FILE_SIZE=10485760  # 10MB in bytes
```

### Default Settings

Defined in `app/core/config.py`:

```python
# File Upload Limits
MAX_FILE_SIZE = 10485760  # 10MB

# Allowed MIME Types
ALLOWED_FILE_TYPES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # DOCX
    "text/markdown",
    "text/plain"
]
```

## Storage Structure

### Supabase Storage Bucket

**Bucket Name:** `iksan-ai-interview`

**File Path Format:**
```
interviews/{student_id}/{session_id}/{timestamp}_{uuid}_{original_filename}
```

**Example:**
```
interviews/123/456/20251124_103000_a1b2c3d4_resume.pdf
```

**Path Components:**
- `{student_id}` - Student's unique ID
- `{session_id}` - Interview session ID
- `{timestamp}` - Upload timestamp (YYYYMMDD_HHMMSS)
- `{uuid}` - Random 8-character UUID for uniqueness
- `{original_filename}` - Original uploaded filename (spaces replaced with underscores)

### Storage Policies

Configure in Supabase Dashboard → Storage → Policies:

**Recommended policies:**
1. **Students can upload to their own folder**
   ```sql
   CREATE POLICY "Students can upload own documents"
   ON storage.objects FOR INSERT
   TO authenticated
   WITH CHECK (
     bucket_id = 'iksan-ai-interview' AND
     (storage.foldername(name))[1] = 'interviews' AND
     (storage.foldername(name))[2] = auth.uid()::text
   );
   ```

2. **Service role has full access**
   ```sql
   CREATE POLICY "Service role full access"
   ON storage.objects
   TO service_role
   USING (bucket_id = 'iksan-ai-interview');
   ```

## Database Schema

### Sessions Table

Stores interview session metadata:

```sql
CREATE TABLE sessions (
  id SERIAL PRIMARY KEY,
  student_id INTEGER NOT NULL REFERENCES students(id),
  status VARCHAR(50) NOT NULL,
  completed_at TIMESTAMP,
  total_score NUMERIC(5,2),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

**Status Values:**
- `in_progress` - Interview session is active
- `completed` - Interview finished successfully
- `failed` - Session creation or processing failed

### Documents Table

Stores document metadata and extracted text:

```sql
CREATE TABLE documents (
  id SERIAL PRIMARY KEY,
  session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  raw_text TEXT,
  document_path VARCHAR(500) NOT NULL,
  processed_at TIMESTAMP
);
```

## Process Flow Details

### Step-by-Step Execution

#### 1. **File Validation**
```python
storage_service.validate_file(file)
```
- Checks if `file.content_type` is in `ALLOWED_FILE_TYPES`
- Returns 400 error if invalid

#### 2. **Session Creation**
```python
session = session_service.create_session(
    student_id=student_id, 
    status="in_progress"
)
session_id = session['id']
```
- Inserts new record in `sessions` table
- Initial status: `"in_progress"`
- Returns session with auto-generated ID

#### 3. **Read File Bytes**
```python
file_bytes = await file.read()
```
- Reads entire file into memory
- Checks size doesn't exceed `MAX_FILE_SIZE`
- Returns 400 error if too large

#### 4. **Upload to Storage**
```python
document_path = await storage_service.upload_document(
    file_bytes=file_bytes,
    filename=file.filename,
    content_type=file.content_type,
    student_id=student_id,
    session_id=session_id
)
```
- Generates unique storage path
- Uploads to Supabase storage bucket
- Returns storage path on success

#### 5. **Text Extraction (Synchronous)**
```python
raw_text = extraction_service.extract_text_from_file(
    file_bytes=file_bytes,
    content_type=file.content_type
)
```
- **Currently:** Returns placeholder text `"[Text extraction pending - to be implemented]"`
- **Future:** Will extract actual text based on file type
- **Note:** This is a blocking operation - frontend waits for completion

#### 6. **Create Document Record**
```python
document = document_service.create_document(
    session_id=session_id,
    document_path=document_path,
    raw_text=raw_text,
    processed_at=datetime.utcnow()
)
```
- Inserts record in `documents` table
- Links document to session via `session_id`
- Stores extracted text in `raw_text` field
- Records processing completion time

#### 7. **Build Response**
```python
return SessionInitiateResponse(
    session_id=session['id'],
    student_id=session['student_id'],
    status=session['status'],
    document=DocumentUploadResponse(...),
    created_at=session['created_at']
)
```

## Error Handling & Rollback

### Rollback Strategy

If **any step fails** after session creation, the system performs a rollback:

```python
async def _rollback_session_creation(
    storage_service,
    session_service,
    document_path,
    session_id
):
    # 1. Delete uploaded file from storage
    if document_path:
        storage_service.delete_document(document_path)
    
    # 2. Mark session as failed (keep for debugging)
    if session_id:
        session_service.update_session_status(
            session_id, 
            status="failed"
        )
```

### Why Keep Failed Sessions?

Failed sessions are **not deleted**, but marked as `status="failed"`. This allows:
- **Debugging** - Analyze what went wrong
- **Analytics** - Track failure rates
- **User Support** - Help users troubleshoot issues
- **Audit Trail** - Maintain complete history

### Error Scenarios

| Failure Point | Rollback Actions | Final State |
|---------------|------------------|-------------|
| File validation | None needed | No session created |
| Session creation | None needed | No changes |
| File upload | Mark session as failed | Session exists with status="failed" |
| Text extraction | Delete file, mark session failed | Session exists with status="failed" |
| Document DB insert | Delete file, mark session failed | Session exists with status="failed" |

## Text Extraction (Future Implementation)

### Current Status

The `TextExtractionService` is a **placeholder** that returns mock text:

```python
def extract_text_from_file(self, file_bytes: bytes, content_type: str) -> str:
    return "[Text extraction pending - to be implemented]"
```

### Planned Implementation

#### PDF Extraction
```python
def _extract_from_pdf(self, file_bytes: bytes) -> str:
    import PyPDF2
    from io import BytesIO
    
    pdf_reader = PyPDF2.PdfReader(BytesIO(file_bytes))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text
```

**Dependencies needed:**
```bash
pip install PyPDF2
# or
pip install pdfplumber  # Alternative with better extraction
```

#### DOCX Extraction
```python
def _extract_from_docx(self, file_bytes: bytes) -> str:
    import docx
    from io import BytesIO
    
    doc = docx.Document(BytesIO(file_bytes))
    text = "\n".join([para.text for para in doc.paragraphs])
    return text
```

**Dependencies needed:**
```bash
pip install python-docx
```

#### Text/Markdown Extraction
```python
def _extract_from_text(self, file_bytes: bytes) -> str:
    return file_bytes.decode('utf-8')
```

### Future `extract_text_from_file` Implementation
```python
def extract_text_from_file(self, file_bytes: bytes, content_type: str) -> str:
    if content_type == "application/pdf":
        return self._extract_from_pdf(file_bytes)
    elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return self._extract_from_docx(file_bytes)
    elif content_type in ["text/plain", "text/markdown"]:
        return self._extract_from_text(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {content_type}")
```

## Testing

### Manual Testing with Swagger UI

1. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```

2. Open http://127.0.0.1:8000/docs

3. Find `POST /api/v1/interview-sessions/initiate`

4. Click "Try it out"

5. Upload a test file and enter a student ID

6. Click "Execute"

### Testing with cURL

```bash
# Test with PDF
curl -X POST "http://127.0.0.1:8000/api/v1/interview-sessions/initiate" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_resume.pdf" \
  -F "student_id=1"

# Test with invalid file type
curl -X POST "http://127.0.0.1:8000/api/v1/interview-sessions/initiate" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_image.jpg" \
  -F "student_id=1"

# Test with large file (should fail)
curl -X POST "http://127.0.0.1:8000/api/v1/interview-sessions/initiate" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@large_file.pdf" \
  -F "student_id=1"
```

### Verify in Database

After successful upload, check the database:

```sql
-- Check session was created
SELECT * FROM sessions WHERE student_id = 1 ORDER BY created_at DESC LIMIT 1;

-- Check document was saved
SELECT * FROM documents ORDER BY processed_at DESC LIMIT 1;
```

### Verify in Supabase Storage

1. Go to Supabase Dashboard → Storage
2. Open `iksan-ai-interview` bucket
3. Navigate to `interviews/{student_id}/{session_id}/`
4. Verify file was uploaded

## Performance Considerations

### Current Implementation

The endpoint is **synchronous** - it waits for all operations to complete before returning:

**Advantages:**
- Simple error handling
- Immediate feedback to user
- No need for polling or webhooks

**Disadvantages:**
- Blocks during text extraction
- May timeout on large files
- Limited concurrent processing

### Recommended for Production

For production use, consider **asynchronous processing**:

```
1. Upload file → Return immediately with session_id
2. Process in background worker (Celery, etc.)
3. Update session status when complete
4. Frontend polls for status or uses WebSocket
```

### Current Timing Estimates

| Operation | Estimated Time |
|-----------|----------------|
| File validation | < 1ms |
| Session creation | 10-50ms |
| File upload (1MB) | 100-500ms |
| Text extraction (placeholder) | < 1ms |
| Text extraction (real PDF) | 500ms - 5s |
| Document DB insert | 10-50ms |
| **Total (current)** | ~200ms - 1s |
| **Total (with real extraction)** | 1s - 6s |

## Security Considerations

### File Validation

- **MIME type checking** - Validates `content_type`
- **File size limits** - Prevents DoS attacks
- **Extension validation** - Future: verify file extension matches content

### Storage Security

- **Private bucket** - Files not publicly accessible by default
- **Row Level Security** - Students can only access their own files
- **Signed URLs** - Temporary access tokens (future feature)

### Input Sanitization

- **Filename sanitization** - Spaces replaced with underscores
- **Path traversal prevention** - Controlled path generation
- **SQL injection protection** - Using parameterized queries

### Authentication

**Current:** No authentication required (development phase)

**Production:** Add JWT authentication:
```python
@router.post("/initiate")
async def initiate_interview_session(
    file: UploadFile,
    student_id: int,
    current_user: User = Depends(get_current_user),  # Add this
    supabase: Client = Depends(get_supabase)
):
    # Verify current_user.id matches student_id
    # ...
```

## Troubleshooting

### Common Issues

#### "File too large" error
**Solution:** Reduce file size or increase `MAX_FILE_SIZE` in config

#### "Invalid file type" error
**Solution:** Ensure file is PDF, DOCX, TXT, or MD format

#### "Failed to upload file to storage"
**Possible causes:**
- Invalid Supabase credentials
- Storage bucket doesn't exist
- Insufficient permissions
- Network issues

**Solution:** Verify `.env` configuration and bucket setup

#### Session created but document not saved
**Possible causes:**
- Text extraction failed
- Database connection issue

**Solution:** Check logs and verify rollback marked session as "failed"

## Next Steps

### Immediate Improvements

1. **Implement actual text extraction** - Add PyPDF2/python-docx
2. **Add authentication** - Protect endpoint with JWT
3. **Add rate limiting** - Prevent abuse
4. **Add file type verification** - Verify file content matches extension

### Future Enhancements 
Perhaps post launch on 5 December
1. **Asynchronous processing** - Use background workers
2. **Progress tracking** - Real-time status updates
3. **OCR support** - Extract text from images/scanned PDFs
4. **Virus scanning** - Scan uploaded files for malware
5. **Multiple file upload** - Support uploading multiple documents
6. **File compression** - Compress large files automatically
7. **CDN integration** - Faster file delivery

## Related Documentation

- [Database Schema](./DB_SCHEMA.md)
- [Supabase Setup](./README_SUPABASE.md)
- [API Documentation](http://127.0.0.1:8000/docs)

---

**Last Updated:** November 24, 2025  
**API Version:** v1  
**Status:** Development (Text extraction placeholder)
