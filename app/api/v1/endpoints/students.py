"""
API endpoints for student account creation.

Uses SQLAlchemy AsyncSession for database operations.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_role, RoleContext
from app.core.database import get_db
from app.schemas.student import (
    StudentAccountCreate, 
    StudentAccountResponse,
    StudentBulkCreateRequest,
    StudentBulkCreateResponse,
)
from app.services.student_registration_service import StudentRegistrationService
from app.repositories.teacher_repository import TeacherRepository

router = APIRouter()


@router.post("/create", response_model=StudentAccountResponse)
async def create_student_account(
    student_account_in: StudentAccountCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    role_context: RoleContext = Depends(require_role(["teacher", "admin"])),
):
    """
    Create a new student account with auto-generated student ID and password.
    
    Requires: Teacher or Admin role
    
    The student ID is auto-generated as a 12-digit number:
    - 3 digits: school_number
    - 4 digits: major_number  
    - 5 digits: sequential student_number
    
    Password is auto-generated with 8+ characters including uppercase, 
    lowercase, digit, and symbol.
    
    Parameters:
    - full_name: Student's full name (required)
    - school_name: School name (creates if not exists)
    - major_name: Major name (creates if not exists)
    - class_name: Class name (required with grade_level to assign class)
    - grade_level: Grade level for the class
    - class_id: Alternative - use existing class ID
    
    Returns: The created student account with credentials
    """
    role_id = role_context.role_id
    if role_id not in [1, 2]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers and admins can create student accounts"
        )
    
    # Get teacher's school_id if they are a teacher
    creator_school_id = None
    if role_id == 2:  # Teacher
        teacher_repo = TeacherRepository(db)
        teacher = await teacher_repo.get_by_user_id(role_context.user.id)
        if teacher:
            creator_school_id = teacher.school_id
        
        # Prevent teachers from specifying school_name
        if student_account_in.school_name is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teachers cannot specify school_name. Students will be created for your school automatically."
            )
    
    registration_service = StudentRegistrationService(db)
    
    try:
        result = await registration_service.create_student_account(
            student_account_in,
            creator_school_id=creator_school_id
        )
        
        # Service returns StudentAccountResponse directly
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create student account: {str(e)}"
        )


@router.post("/bulk-create", response_model=StudentBulkCreateResponse)
async def bulk_create_student_accounts(
    request: StudentBulkCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    role_context: RoleContext = Depends(require_role(["teacher", "admin"])),
):
    """
    Create multiple student accounts in a single transaction.
    
    Requires: Teacher or Admin role
    
    All-or-nothing: If any student creation fails, the entire batch is rolled back.
    
    Each student gets:
    - Auto-generated 12-digit student ID
    - Auto-generated secure password
    - Auth account (using fake email pattern for username login)
    
    Parameters:
    - students: List of student account creation requests
    
    Returns: 
    - students: List of created student accounts with credentials
    - created_count: Number of successfully created accounts
    """
    
    role_id = role_context.role_id
    if role_id not in [1, 2]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers and admins can create student accounts"
        )
    
    if not request.students:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one student must be provided"
        )
    
    if len(request.students) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 100 students can be created at once"
        )
    
    # Get teacher's school_id if they are a teacher
    creator_school_id = None
    if role_id == 2:  # Teacher
        teacher_repo = TeacherRepository(db)
        teacher = await teacher_repo.get_by_user_id(role_context.user.id)
        if teacher:
            creator_school_id = teacher.school_id
        
        # Prevent teachers from specifying school_name in any student
        for idx, student in enumerate(request.students):
            if student.school_name is not None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Teachers cannot specify school_name. Student at index {idx} contains school_name field. Students will be created for your school automatically."
                )
    
    registration_service = StudentRegistrationService(db)
    
    try:
        results = await registration_service.bulk_create_student_accounts(request.students, creator_school_id=creator_school_id)
        
        # results is already a list of StudentAccountResponse objects
        return StudentBulkCreateResponse(
            students=results,
            created_count=len(results)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create student accounts: {str(e)}"
        )

