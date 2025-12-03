# Interview Session Initiation - Documentation

## Overview

The interview session initiation process allows students to upload documents (resume, portfolio, etc.) to start a new AI interview session. The system processes the document text extraction synchronously and stores it for interview generation.

**Note:** File storage to Supabase bucket is currently **deprecated**. Files are processed in-memory only, and text content is stored in the database.

## Architecture

### Flow Diagram

```
Frontend → Upload Document → Backend API
                                ↓
                        Validate File Type & Size
                                ↓
                    Create Session (status: "in_progress")
                                ↓
                    Extract Text from Document (in-memory)
                                ↓
                    Save raw_text to documents table
                                ↓
                Create detailed_feedbacks record (session_id only)
                                ↓
                    Return Success Response
                                ↓
            (If any step fails → Mark session as "failed")
```

### Components

#### 1. Storage Service (`app/services/storage_service.py`) - DEPRECATED
**Status:** Currently only used for file validation
- **File Validation** - Checks file type and size
- **Upload** - ~~Stores files in organized bucket structure~~ (deprecated)
- **Delete** - ~~Removes files~~ (deprecated)
- **URL Generation** - ~~Creates public/signed URLs~~ (deprecated)

**Note:** Upload/delete/URL generation methods are preserved for future use but not currently utilized.

#### 2. Text Extraction Service (`app/services/text_extraction_service.py`)
Extracts text content from uploaded documents:
- **PDF** - Uses PyPDF2/pdfplumber (to be implemented)
- **DOCX** - Uses python-docx (to be implemented)
- **TXT/MD** - Direct text reading (to be implemented)
- **Current Status** - Returns placeholder text

#### 3. Document Service (`app/services/document_service.py`)
Manages document database records:
- **Create Document** - Inserts document with `session_id` and `raw_text` only
- **Get Document** - Retrieves document by session ID

#### 4. Interview Session Service (`app/services/interview_session_service.py`)
Manages interview session records:
- **Create Session** - Creates new session with initial status
- **Update Status** - Updates session state and completion data
- **Delete Session** - Hard delete for rollback scenarios
- **Get Session** - Retrieves session by ID

#### 5. Feedback Service (`app/services/feedback_service.py`)
Manages feedback records:
- **Create Detailed Feedback** - Creates initial empty feedback record with only `session_id`

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
  "success": true,
  "message": "Interview session initiated successfully",
  "session_id": 456
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Always `true` for successful requests |
| `message` | string | Success message |
| `session_id` | integer | Unique ID of the created interview session |

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

# DEPRECATED: Storage bucket not currently in use
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

### Supabase Storage - DEPRECATED

**Status:** File storage is currently not in use. This section is kept for future reference.

Files are no longer uploaded to Supabase storage. Text content is extracted in-memory and stored directly in the database.

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
  raw_text TEXT
);
```

**Note:** `document_path` and `processed_at` columns have been removed as files are no longer stored.

### Detailed Feedbacks Table

Stores interview feedback records:

```sql
CREATE TABLE detailed_feedbacks (
  id SERIAL PRIMARY KEY,
  session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  question_order INT,
  question_text TEXT,
  answer_text TEXT,
  evaluation_text TEXT,
  is_correct BOOLEAN DEFAULT FALSE,
  score NUMERIC(5,2),
  transcript TEXT
);
```

**Note:** 
- `audio_path` column has been removed as audio files are not stored
- `question_order` is now nullable to allow initial empty record creation

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

#### 4. **Text Extraction (Synchronous)**
```python
raw_text = extraction_service.extract_text_from_file(
    file_bytes=file_bytes,
    content_type=file.content_type
)
```
- **Currently:** Returns placeholder text `"[Text extraction pending - to be implemented]"`
- **Future:** Will extract actual text based on file type
- **Note:** This is a blocking operation - frontend waits for completion

#### 5. **Save Text to Database**
```python
document = document_service.create_document(
    session_id=session_id,
    raw_text=raw_text
)
```
- Inserts record in `documents` table
- Links document to session via `session_id`
- Stores extracted text in `raw_text` field

#### 6. **Create Feedback Record**
```python
await feedback_service.create_detailed_feedback(session_id=session_id)
```
- Inserts initial record in `detailed_feedbacks` table
- Only `session_id` is populated, all other fields are NULL

#### 7. **Build Response**
```python
return SessionInitiateResponse(
    success=True,
    message="Interview session initiated successfully",
    session_id=session['id']
)
```

## Error Handling & Rollback

### Rollback Strategy

If **any step fails** after session creation, the system marks the session as failed:

```python
async def _rollback_session_creation(
    session_service,
    session_id
):
    # Mark session as failed (keep for debugging)
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
| File size check | Mark session as failed | Session exists with status="failed" |
| Text extraction | Mark session failed | Session exists with status="failed" |
| Document DB insert | Mark session failed | Session exists with status="failed" |
| Feedback DB insert | Mark session failed | Session exists with status="failed" |

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

-- Check document was saved with text
SELECT id, session_id, LEFT(raw_text, 100) as text_preview 
FROM documents 
WHERE session_id = (SELECT id FROM sessions WHERE student_id = 1 ORDER BY created_at DESC LIMIT 1);

-- Check detailed_feedback record was created
SELECT * FROM detailed_feedbacks 
WHERE session_id = (SELECT id FROM sessions WHERE student_id = 1 ORDER BY created_at DESC LIMIT 1);
```

### Verify Storage - N/A

Storage verification is no longer applicable as files are not uploaded to Supabase storage.

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
| File read | 10-100ms |
| Text extraction (placeholder) | < 1ms |
| Text extraction (real PDF) | 500ms - 5s |
| Document DB insert | 10-50ms |
| Feedback DB insert | 10-50ms |
| **Total (current)** | ~50ms - 300ms |
| **Total (with real extraction)** | 500ms - 6s |

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
**Status:** This error no longer occurs as storage is deprecated.

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
4. **Add file content verification** - Verify file content matches extension

### Future Enhancements

**File Storage Re-enablement (if needed):**
1. Add back `document_path` and `processed_at` columns to `documents` table
2. Add back `audio_path` column to `detailed_feedbacks` table
3. Uncomment storage upload/delete code in endpoint
4. Update response schema to include file URLs
5. Configure Supabase storage bucket and policies

**Other Improvements (post-launch):**
1. **Asynchronous processing** - Use background workers
2. **Progress tracking** - Real-time status updates
3. **OCR support** - Extract text from images/scanned PDFs
4. **Virus scanning** - Scan uploaded files for malware
5. **Multiple file upload** - Support uploading multiple documents
6. **File compression** - Compress large files automatically

## Related Documentation

- [Database Schema](./DB_SCHEMA.md)
- [Supabase Setup](./README_SUPABASE.md)
- [API Documentation](http://127.0.0.1:8000/docs)

---

**Last Updated:** November 25, 2025  
**API Version:** v1  
**Status:** Development (Storage deprecated, text extraction placeholder)
