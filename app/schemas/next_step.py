from typing import Optional
from pydantic import BaseModel

class NextStepBase(BaseModel):
    session_id: int
    title: str
    description_text: str

class NextStepCreate(NextStepBase):
    pass

class NextStepUpdate(BaseModel):
    title: Optional[str] = None
    description_text: Optional[str] = None

class NextStepResponse(NextStepBase):
    id: int

    class Config:
        from_attributes = True
