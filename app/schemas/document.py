from datetime import datetime
from typing import Optional
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


class DocumentUploadResponse(BaseModel):
    """Response schema for document upload"""
    id: int
    document_path: str
    processed_at: datetime

    class Config:
        from_attributes = True
