from typing import Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None

class TokenData(BaseModel):
    email: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role_id: int

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    role_id: Optional[int] = None
    role_name: Optional[str] = None
    student_details: Optional[Dict[str, Any]] = None
    teacher_details: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
