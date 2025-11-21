from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, users, teachers, students, classes, schools, majors,
    interview_sessions, interview_scores, feedback
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(teachers.router, prefix="/teachers", tags=["teachers"])
api_router.include_router(students.router, prefix="/students", tags=["students"])
api_router.include_router(classes.router, prefix="/classes", tags=["classes"])
api_router.include_router(schools.router, prefix="/schools", tags=["schools"])
api_router.include_router(majors.router, prefix="/majors", tags=["majors"])
api_router.include_router(interview_sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(interview_scores.router, prefix="/scores", tags=["scores"])
api_router.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
