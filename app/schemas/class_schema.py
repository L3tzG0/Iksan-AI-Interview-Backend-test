from typing import Optional
from pydantic import BaseModel, Field

class ClassBase(BaseModel):
    class_name: str
    grade_level: int = Field(..., ge=1, le=3, description="Grade level: 1, 2, or 3")

class ClassCreate(ClassBase):
    pass

class ClassUpdate(BaseModel):
    class_name: Optional[str] = None
    grade_level: Optional[int] = Field(None, ge=1, le=3, description="Grade level: 1, 2, or 3")

class ClassResponse(ClassBase):
    id: int

    class Config:
        from_attributes = True
