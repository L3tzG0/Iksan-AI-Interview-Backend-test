from pydantic import BaseModel

class DocumentBase(BaseModel):
    session_id: int
    cleaned_text: str

class DocumentResponse(DocumentBase):
    id: int

    class Config:
        from_attributes = True
