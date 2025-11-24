from datetime import datetime
from typing import Optional
from supabase import Client
from fastapi import HTTPException, status


class InterviewSessionService:
    """Service for handling interview session database operations"""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
    
    def create_session(self, student_id: int, status: str = "in_progress") -> dict:
        """
        Create new interview session
        
        Args:
            student_id: ID of the student
            status: Initial status (default: "in_progress")
        
        Returns:
            dict: Created session record
        
        Raises:
            HTTPException: If creation fails
        """
        try:
            session_data = {
                "student_id": student_id,
                "status": status
            }
            
            response = self.supabase.table('sessions').insert(session_data).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to create session record"
                )
            
            return response.data[0]
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Database error while creating session: {str(e)}"
            )
    
    def update_session_status(
        self, 
        session_id: int, 
        status: str,
        completed_at: Optional[datetime] = None,
        total_score: Optional[float] = None
    ) -> dict:
        """
        Update session status and related fields
        
        Args:
            session_id: Session ID
            status: New status value
            completed_at: Completion timestamp (optional)
            total_score: Total score (optional)
        
        Returns:
            dict: Updated session record
        
        Raises:
            HTTPException: If update fails
        """
        try:
            update_data = {"status": status}
            
            if completed_at:
                update_data["completed_at"] = completed_at.isoformat()
            if total_score is not None:
                update_data["total_score"] = total_score
            
            response = self.supabase.table('sessions').update(update_data).eq('id', session_id).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=404,
                    detail=f"Session with id {session_id} not found"
                )
            
            return response.data[0]
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update session: {str(e)}"
            )
    
    def delete_session(self, session_id: int) -> bool:
        """
        Delete session (hard delete for rollback)
        
        Args:
            session_id: Session ID to delete
        
        Returns:
            bool: True if successful
        
        Raises:
            HTTPException: If deletion fails
        """
        try:
            response = self.supabase.table('sessions').delete().eq('id', session_id).execute()
            return True
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete session: {str(e)}"
            )
    
    def get_session(self, session_id: int) -> Optional[dict]:
        """
        Get session by ID
        
        Args:
            session_id: Session ID
        
        Returns:
            dict or None: Session record if found
        """
        try:
            response = self.supabase.table('sessions').select('*').eq('id', session_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch session: {str(e)}"
            )
