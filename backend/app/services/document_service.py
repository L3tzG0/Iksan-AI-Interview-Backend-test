"""
Document Service for document database operations.

Handles document records associated with interview sessions
using SQLAlchemy AsyncSession.
"""
from typing import Optional, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.document import Document


class DocumentService:
    """Service for handling document database operations."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize service with SQLAlchemy session.
        
        Args:
            db: SQLAlchemy AsyncSession for database operations
        """
        self.db = db
    
    async def create_document(
        self,
        session_id: int,
        cleaned_text: str
    ) -> dict:
        """
        Create document record in database with cleaned text.
        
        Args:
            session_id: ID of the interview session
            cleaned_text: LLM-optimized cleaned text content
        
        Returns:
            dict: Created document record
        
        Raises:
            HTTPException: If creation fails
        """
        try:
            document = Document(
                session_id=session_id,
                cleaned_text=cleaned_text
            )
            
            self.db.add(document)
            await self.db.flush()
            await self.db.refresh(document)
            
            return self._to_dict(document)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Database error while creating document: {str(e)}"
            )
    
    async def get_document_by_session(self, session_id: int) -> Optional[dict]:
        """
        Get document by session ID.
        
        Args:
            session_id: Session ID
        
        Returns:
            dict or None: Document record if found
        """
        try:
            stmt = select(Document).where(Document.session_id == session_id)
            result = await self.db.execute(stmt)
            document = result.scalar_one_or_none()
            
            return self._to_dict(document) if document else None
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch document: {str(e)}"
            )

    def _to_dict(self, document: Document) -> dict:
        """
        Convert Document model to dictionary.
        
        Args:
            document: Document SQLAlchemy model instance
        
        Returns:
            dict: Dictionary representation
        """
        return {
            "id": document.id,
            "session_id": document.session_id,
            "cleaned_text": document.cleaned_text,
        }
