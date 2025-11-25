from typing import List, Annotated, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, status
from supabase import Client
from app.core.database import get_supabase
from app.core.config import settings
from app.core.security import get_current_user
from app.schemas.interview_session import (
    InterviewSessionResponse, 
    InterviewSessionCreate,
    SessionInitiateResponse
)
from app.services.storage_service import StorageService
from app.services.document_service import DocumentService
from app.services.interview_session_service import InterviewSessionService
from app.services.text_extraction_service import TextExtractionService
from app.services.feedback_service import FeedbackService
from app.services.student_service import StudentService

router = APIRouter()

@router.get("/", response_model=List[InterviewSessionResponse])
async def read_sessions(
    supabase: Annotated[Client, Depends(get_supabase)]
):
    """Get all interview sessions"""
    response = supabase.table('sessions').select('*').execute()
    return response.data


@router.post("/initiate", response_model=SessionInitiateResponse)
async def initiate_interview_session(
    file: Optional[UploadFile] = File(None, description="Document file (PDF, DOCX, TXT, MD)"),
    raw_text: Optional[str] = Form(None, description="Raw text content"),
    student_id: int = Form(..., description="Student ID"),
    current_user = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Initiate new interview session by processing document text or raw text.
    
    Requires: Authentication (any logged-in user)
    
    Parameters:
    - file (optional): Document file to process (PDF, DOCX, TXT, MD)
    - raw_text (optional): Raw text content
    - student_id (required): Student ID
    
    Note: At least one of 'file' or 'raw_text' must be provided.
    If both are provided, the file will be processed and raw_text will be ignored.
    
    Security measures:
    - Authentication required (JWT token)
    - Student existence validation
    - File type validation (MIME type) - when file is provided
    - File signature verification (magic numbers) - when file is provided
    - Filename sanitization - when file is provided
    - File size limits - when file is provided
    
    Simplified flow (no storage):
    1. Validates authentication
    2. Validates at least one of file or raw_text is provided
    3. Validates student exists
    4. If file provided: validates file type, signature, and size, extracts text
    5. If only raw_text provided: uses raw_text directly
    6. Creates session with status "in_progress"
    7. Saves raw_text to documents table
    8. Creates initial detailed_feedbacks record
    9. Returns success response
    
    If any step fails, the session is marked as failed.
    """
    # Initialize services
    storage_service = StorageService(supabase)  # Used for validation only
    session_service = InterviewSessionService(supabase)
    document_service = DocumentService(supabase)
    extraction_service = TextExtractionService()
    feedback_service = FeedbackService(supabase)
    student_service = StudentService(supabase)
    
    session_id: int | None = None
    
    try:
        # Step 0: Validate that at least one of file or raw_text is provided
        if not file and not raw_text:
            raise HTTPException(
                status_code=400,
                detail="Either 'file' or 'raw_text' must be provided"
            )
        
        # Step 1: Validate student exists
        student = await student_service.get_student(student_id)
        
        # Step 2: Create session
        session = session_service.create_session(student_id=student_id, status="in_progress")
        session_id = session['id']
        
        # Ensure session_id is set (type narrowing)
        assert session_id is not None, "Session ID must be set after creation"
        
        # Step 3: Process file or use raw_text
        extracted_text: str
        
        if file:
            # File provided - process it (ignore raw_text if also provided)
            # Step 3a: Validate file type and filename
            storage_service.validate_file(file)
            
            # Step 3b: Read file bytes
            file_bytes = await file.read()
            
            # Validate file size
            if len(file_bytes) > settings.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB"
                )
            
            # Verify file signature (magic numbers)
            content_type = file.content_type or "application/octet-stream"
            storage_service.verify_file_signature(file_bytes, content_type)
            
            # Step 3c: Extract text from document
            extracted_text = extraction_service.extract_text_from_file(
                file_bytes=file_bytes,
                content_type=content_type
            )
        else:
            # Only raw_text provided - use it directly
            extracted_text = raw_text  # type: ignore
        
        # Step 4: Save extracted_text to documents table
        document = document_service.create_document(
            session_id=session_id,
            raw_text=extracted_text
        )
        
        # Step 5: Create initial detailed_feedbacks record
        await feedback_service.create_detailed_feedback(session_id=session_id)
        
        # Step 6: Return simple success response
        return SessionInitiateResponse(
            success=True,
            message="Interview session initiated successfully",
            session_id=session['id']
        )
        
    except HTTPException:
        # HTTPExceptions already have proper status codes and messages
        # Perform rollback before re-raising
        await _rollback_session_creation(session_service, session_id)
        raise
        
    except Exception as e:
        # Unexpected errors - rollback and return 500
        await _rollback_session_creation(session_service, session_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate interview session: {str(e)}"
        )


async def _rollback_session_creation(
    session_service: InterviewSessionService,
    session_id: int | None = None
):
    """
    Rollback changes if session initiation fails.
    
    Simplified: Only marks session as failed (no storage cleanup needed).
    We keep the session record for debugging purposes.
    """
    # Mark session as failed (keep for debugging, don't delete)
    if session_id:
        try:
            session_service.update_session_status(session_id, status="failed")
        except Exception as e:
            print(f"Warning: Failed to update session status during rollback: {str(e)}")