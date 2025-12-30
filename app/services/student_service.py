from supabase import AsyncClient
from fastapi import HTTPException, status

# Explicit columns to select for students (avoiding SELECT *)
STUDENT_COLUMNS = "id, student_id, user_id, school_id, major_id, current_class_id, interview_session_quota, created_at, updated_at"
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

    async def consume_session_quota(self, student_id: int, expected_quota: int) -> int:
        """Atomically decrement interview_session_quota by 1 when the expected value matches."""
        if expected_quota <= 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Interview session quota exhausted"
            )

        try:
            response = (
                await self.supabase
                .table('students')
                .update({'interview_session_quota': expected_quota - 1})
                .eq('id', student_id)
                .eq('interview_session_quota', expected_quota)
                .execute()
            )

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Interview session quota could not be updated. Please try again."
                )

            updated_quota = response.data[0].get("interview_session_quota")
            return int(updated_quota) if updated_quota is not None else expected_quota - 1
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
