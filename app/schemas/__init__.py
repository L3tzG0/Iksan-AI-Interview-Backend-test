from app.schemas.auth import Token, TokenData, LoginRequest, RegisterRequest
from app.schemas.role import RoleBase, RoleResponse
from app.schemas.user import UserProfileBase, UserProfileCreate, UserProfileResponse, UserProfileWithRole
from app.schemas.school import SchoolBase, SchoolResponse
from app.schemas.major import MajorBase, MajorResponse
from app.schemas.class_schema import ClassBase, ClassCreate, ClassUpdate, ClassResponse
from app.schemas.student import StudentBase, StudentResponse
from app.schemas.interview_session import InterviewSessionBase, InterviewSessionCreate, InterviewSessionUpdate, InterviewSessionResponse, InterviewSessionWithDetails
from app.schemas.document import DocumentBase, DocumentResponse
from app.schemas.summary import InterviewSummaryBase, InterviewSummaryUpdate, InterviewSummaryResponse
from app.schemas.detailed_feedback import InterviewDetailedFeedbackBase, InterviewDetailedFeedbackCreate, InterviewDetailedFeedbackUpdate, InterviewDetailedFeedbackResponse
from app.schemas.next_step import InterviewNextStepBase, InterviewNextStepUpdate, InterviewNextStepResponse
