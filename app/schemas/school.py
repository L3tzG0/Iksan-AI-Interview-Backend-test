from pydantic import BaseModel

class SchoolBase(BaseModel):
    school_name: str

class SchoolResponse(SchoolBase):
    id: int

    class Config:
        from_attributes = True
