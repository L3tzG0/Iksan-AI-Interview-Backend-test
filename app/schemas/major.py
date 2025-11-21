from pydantic import BaseModel

class MajorBase(BaseModel):
    major_name: str

class MajorCreate(MajorBase):
    pass

class MajorUpdate(MajorBase):
    pass

class MajorResponse(MajorBase):
    id: int

    class Config:
        from_attributes = True
