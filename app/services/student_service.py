from supabase import AsyncClient
from fastapi import HTTPException, status

# Explicit columns to select for students (avoiding SELECT *)
STUDENT_COLUMNS = "id, student_id, user_id, school_id, major_id, current_class_id, created_at, updated_at"
# STUDENT_COLUMNS_WITH_RELATIONS = """
#     id, student_id, user_id, school_id, major_id, current_class_id, created_at, updated_at,
#     user_profiles(id, email, full_name, role_id),
#     schools(id, school_name),
#     majors(id, major_name),
#     classes(id, class_name, grade_level)
# """


class StudentService:
    """
    Service for student database operations.
    
    All methods are async because the Supabase AsyncClient
    uses async HTTP calls. This ensures proper connection handling
    under concurrent load.
    """
    def __init__(self, supabase: AsyncClient):
        self.supabase = supabase

    async def get_student(self, student_id: int):
        """Get student by ID (primary key) with explicit column selection"""
        try:
            response = await self.supabase.table('students').select(STUDENT_COLUMNS).eq('id', student_id).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
