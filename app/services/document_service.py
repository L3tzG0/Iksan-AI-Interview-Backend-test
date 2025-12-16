from datetime import datetime
from typing import Optional, Any
from fastapi import HTTPException
from supabase import AsyncClient

# Explicit columns to select for documents (avoiding SELECT *)
DOCUMENT_COLUMNS = "id, session_id, cleaned_text"


class DocumentService:
    """Service for handling document database operations"""
    
    def __init__(self, supabase: AsyncClient):
        self.supabase = supabase
    
    async def create_document(
        self,
        session_id: int,
        cleaned_text: str
    ) -> Any:
        """
        Create document record in database with cleaned text
        
        Args:
            session_id: ID of the interview session
            cleaned_text: LLM-optimized cleaned text content
        
        Returns:
            dict: Created document record
        
        Raises:
            HTTPException: If creation fails
        """
        try:
            document_data = {
                "session_id": session_id,
                "cleaned_text": cleaned_text
            }
            
            response = await self.supabase.table('documents').insert(document_data).execute()
            
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
    
    async def get_document_by_session(self, session_id: int) -> Optional[Any]:
        """
        Get document by session ID with explicit column selection
        
        Args:
            session_id: Session ID
        
        Returns:
            dict or None: Document record if found
        """
        try:
            response = await self.supabase.table('documents').select(DOCUMENT_COLUMNS).eq('session_id', session_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch document: {str(e)}"
            )
