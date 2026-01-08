from pydantic import BaseModel

class MajorBase(BaseModel):
    major_name: str

class MajorResponse(MajorBase):
    id: int

    class Config:
        from_attributes = True
