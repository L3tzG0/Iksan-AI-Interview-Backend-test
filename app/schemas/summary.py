from typing import Optional
from pydantic import BaseModel

class SummaryBase(BaseModel):
    session_id: int
    strength_text: str
    areas_for_growth_text: str

class SummaryCreate(SummaryBase):
    pass

class SummaryUpdate(BaseModel):
    strength_text: Optional[str] = None
    areas_for_growth_text: Optional[str] = None

class SummaryResponse(SummaryBase):
    id: int

    class Config:
        from_attributes = True
