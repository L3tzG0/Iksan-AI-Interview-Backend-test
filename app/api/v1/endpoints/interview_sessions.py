from typing import List, Annotated
from datetime import datetime
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from supabase import Client
from app.core.database import get_supabase
from app.core.config import settings
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
    file: UploadFile = File(..., description="Document file (PDF, DOCX, TXT, MD)"),
    student_id: int = Form(..., description="Student ID"),
    supabase: Client = Depends(get_supabase)
):
    """
    Initiate new interview session by processing document text.
    
    Simplified flow (no storage):
    1. Validates file type and size
    2. Creates session with status "in_progress"
    3. Extracts text from uploaded file (placeholder for now)
    4. Saves raw_text to documents table
    5. Creates initial detailed_feedbacks record
    6. Returns success response
    
    If any step fails, the session is marked as failed.
    """
    # Initialize services
    storage_service = StorageService(supabase)  # Used for validation only
    session_service = InterviewSessionService(supabase)
    document_service = DocumentService(supabase)
    extraction_service = TextExtractionService()
    feedback_service = FeedbackService(supabase)
    
    session_id = None
    
    try:
        # Step 1: Validate file type
        storage_service.validate_file(file)
        
        # Step 2: Create session
        session = session_service.create_session(student_id=student_id, status="in_progress")
        session_id = session['id']
        
        # Step 3: Read file bytes
        file_bytes = await file.read()
        
        # Validate file size
        if len(file_bytes) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB"
            )
        
        # Step 4: Extract text from document
        raw_text = extraction_service.extract_text_from_file(
            file_bytes=file_bytes,
            content_type=file.content_type
        )
        
        # Step 5: Save raw_text to documents table
        document = document_service.create_document(
            session_id=session_id,
            raw_text=raw_text
        )
        
        # Step 6: Create initial detailed_feedbacks record
        await feedback_service.create_detailed_feedback(session_id=session_id)
        
        # Step 7: Return simple success response
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
    session_id: int = None
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