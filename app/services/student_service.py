from supabase import Client
from fastapi import HTTPException, status
from app.schemas.student import StudentCreate, StudentUpdate

class StudentService:
    """
    Service for student database operations.
    
    All methods are synchronous (def) because the Supabase Python client
    uses synchronous HTTP calls internally. FastAPI will automatically
    run these in a thread pool when called from async endpoints.
    """
    def __init__(self, supabase: Client):
        self.supabase = supabase

    def create_student(self, student: StudentCreate):
        """Create a new student"""
        try:
            response = self.supabase.table('students').insert(student.model_dump()).execute()
            return response.data[0]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def get_student(self, student_id: int):
        """Get student by ID"""
        try:
            response = self.supabase.table('students').select('*').eq('id', student_id).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
            return response.data[0]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def update_student(self, student_id: int, student: StudentUpdate):
        """Update student information"""
        try:
            response = self.supabase.table('students').update(student.model_dump(exclude_unset=True)).eq('id', student_id).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
            return response.data[0]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
