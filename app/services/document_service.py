from datetime import datetime
from typing import Optional, Any
from fastapi import HTTPException
from supabase import Client


class DocumentService:
    """Service for handling document database operations"""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
    
    def create_document(
        self,
        session_id: int,
        document_path: str,
        raw_text: str,
        processed_at: datetime
    ) -> Any:
        """
        Create document record in database
        
        Args:
            session_id: ID of the interview session
            document_path: Storage path of the uploaded file
            raw_text: Extracted text content
            processed_at: Timestamp when text was extracted
        
        Returns:
            dict: Created document record
        
        Raises:
            HTTPException: If creation fails
        """
        try:
            document_data = {
                "session_id": session_id,
                "document_path": document_path,
                "raw_text": raw_text,
                "processed_at": processed_at.isoformat()
            }
            
            response = self.supabase.table('documents').insert(document_data).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to create document record"
                )
            
            return response.data[0]
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Database error while creating document: {str(e)}"
            )
    
    def get_document_by_session(self, session_id: int) -> Optional[Any]:
        """
        Get document by session ID
        
        Args:
            session_id: Session ID
        
        Returns:
            dict or None: Document record if found
        """
        try:
            response = self.supabase.table('documents').select('*').eq('session_id', session_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch document: {str(e)}"
            )
