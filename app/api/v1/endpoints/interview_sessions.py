from typing import List, Annotated
from datetime import datetime
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from supabase import Client
from app.core.database import get_supabase
from app.schemas.interview_session import (
    InterviewSessionResponse, 
    InterviewSessionCreate,
    SessionInitiateResponse
)
from app.schemas.document import DocumentUploadResponse
from app.services.storage_service import StorageService
from app.services.document_service import DocumentService
from app.services.interview_session_service import InterviewSessionService
from app.services.text_extraction_service import TextExtractionService

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
    Initiate new interview session by uploading a document.
    
    This endpoint:
    1. Creates a new session with status "in_progress"
    2. Uploads the document to Supabase storage
    3. Extracts text from the document (currently placeholder)
    4. Saves document record with extracted text
    5. Returns session and document details
    
    The process is synchronous - it waits for all steps to complete.
    If any step fails, previous changes are rolled back.
    """
    storage_service = StorageService(supabase)
    session_service = InterviewSessionService(supabase)
    document_service = DocumentService(supabase)
    extraction_service = TextExtractionService()
    
    session_id = None
    document_path = None
    
    try:
        # Step 1: Validate file (type and content_type)
        storage_service.validate_file(file)
        
        # Step 2: Create session first (need ID for storage path)
        session = session_service.create_session(student_id=student_id, status="in_progress")
        session_id = session['id']
        
        # Step 3: Read file bytes (for both upload and extraction)
        file_bytes = await file.read()
        
        # Step 4: Upload to storage
        document_path = await storage_service.upload_document(
            file_bytes=file_bytes,
            filename=file.filename,
            content_type=file.content_type,
            student_id=student_id,
            session_id=session_id
        )
        
        # Step 5: Extract text from document (BLOCKING - waits for completion)
        raw_text = extraction_service.extract_text_from_file(
            file_bytes=file_bytes,
            content_type=file.content_type
        )
        
        # Step 6: Create document record in database
        processed_at = datetime.utcnow()
        document = document_service.create_document(
            session_id=session_id,
            document_path=document_path,
            raw_text=raw_text,
            processed_at=processed_at
        )
        
        # Step 7: Build and return response
        return SessionInitiateResponse(
            session_id=session['id'],
            student_id=session['student_id'],
            status=session['status'],
            document=DocumentUploadResponse(
                id=document['id'],
                document_path=document['document_path'],
                processed_at=document['processed_at']
            ),
            created_at=session['created_at']
        )
        
    except HTTPException:
        # HTTPExceptions already have proper status codes and messages
        # Perform rollback before re-raising
        await _rollback_session_creation(
            storage_service, session_service, document_path, session_id
        )
        raise
        
    except Exception as e:
        # Unexpected errors - rollback and return 500
        await _rollback_session_creation(
            storage_service, session_service, document_path, session_id
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate interview session: {str(e)}"
        )


async def _rollback_session_creation(
    storage_service: StorageService,
    session_service: InterviewSessionService,
    document_path: str = None,
    session_id: int = None
):
    """
    Rollback changes if session initiation fails.
    
    This is called when any step in the initiation process fails.
    However, we keep the session record and mark it as failed for debugging.
    """
    # Delete uploaded file from storage if it exists
    if document_path:
        try:
            storage_service.delete_document(document_path)
        except Exception as e:
            print(f"Warning: Failed to delete file during rollback: {str(e)}")
    
    # Mark session as failed (keep for debugging, don't delete)
    if session_id:
        try:
            session_service.update_session_status(session_id, status="failed")
        except Exception as e:
            print(f"Warning: Failed to update session status during rollback: {str(e)}")


@router.post("/", response_model=InterviewSessionResponse)
async def create_session(
    session_in: InterviewSessionCreate,
    supabase: Annotated[Client, Depends(get_supabase)]
):
    pass
