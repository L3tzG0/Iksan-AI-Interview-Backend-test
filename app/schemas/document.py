from datetime import datetime
from pydantic import BaseModel

class DocumentBase(BaseModel):
    session_id: int
    raw_text: str
    document_path: str

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: int
    processed_at: datetime

    class Config:
        from_attributes = True
