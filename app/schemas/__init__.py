from app.schemas.auth import Token, TokenData, LoginRequest, RegisterRequest
from app.schemas.role import RoleBase, RoleCreate, RoleResponse
from app.schemas.user import UserProfileBase, UserProfileCreate, UserProfileUpdate, UserProfileResponse, UserProfileWithRole
from app.schemas.teacher import TeacherBase, TeacherCreate, TeacherResponse, TeacherWithUser
from app.schemas.school import SchoolBase, SchoolCreate, SchoolUpdate, SchoolResponse
from app.schemas.major import MajorBase, MajorCreate, MajorUpdate, MajorResponse
from app.schemas.class_schema import ClassBase, ClassCreate, ClassUpdate, ClassResponse, ClassWithTeacher
from app.schemas.student import StudentBase, StudentCreate, StudentUpdate, StudentResponse, StudentWithDetails
from app.schemas.interview_session import InterviewSessionBase, InterviewSessionCreate, InterviewSessionUpdate, InterviewSessionResponse, InterviewSessionWithDetails
from app.schemas.document import DocumentBase, DocumentCreate, DocumentResponse
from app.schemas.summary import InterviewSummaryBase, InterviewSummaryCreate, InterviewSummaryUpdate, InterviewSummaryResponse
from app.schemas.detailed_feedback import InterviewDetailedFeedbackBase, InterviewDetailedFeedbackCreate, InterviewDetailedFeedbackUpdate, InterviewDetailedFeedbackResponse
from app.schemas.next_step import InterviewNextStepBase, InterviewNextStepCreate, InterviewNextStepUpdate, InterviewNextStepResponse
