from app.schemas.auth import Token, TokenData, LoginRequest, RegisterRequest
from app.schemas.role import RoleBase, RoleCreate, RoleResponse
from app.schemas.user import UserBase, UserCreate, UserUpdate, UserResponse, UserWithRole
from app.schemas.teacher import TeacherBase, TeacherCreate, TeacherResponse, TeacherWithUser
from app.schemas.school import SchoolBase, SchoolCreate, SchoolUpdate, SchoolResponse
from app.schemas.major import MajorBase, MajorCreate, MajorUpdate, MajorResponse
from app.schemas.class_schema import ClassBase, ClassCreate, ClassUpdate, ClassResponse, ClassWithTeacher
from app.schemas.student import StudentBase, StudentCreate, StudentUpdate, StudentResponse, StudentWithDetails
from app.schemas.interview_session import InterviewSessionBase, InterviewSessionCreate, InterviewSessionUpdate, InterviewSessionResponse, InterviewSessionWithDetails
from app.schemas.document import DocumentBase, DocumentCreate, DocumentResponse
from app.schemas.interview_score import InterviewScoreBase, InterviewScoreCreate, InterviewScoreUpdate, InterviewScoreResponse
from app.schemas.summary import SummaryBase, SummaryCreate, SummaryUpdate, SummaryResponse
from app.schemas.detailed_feedback import DetailedFeedbackBase, DetailedFeedbackCreate, DetailedFeedbackUpdate, DetailedFeedbackResponse
from app.schemas.next_step import NextStepBase, NextStepCreate, NextStepUpdate, NextStepResponse
