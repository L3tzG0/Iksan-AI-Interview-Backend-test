from pydantic import BaseModel
from typing import List

class RagQuery(BaseModel):
    """Schema for the input query text used for RAG retrieval."""
    query_text: str

class RagResult(BaseModel):
    """Schema for the questions retrieved from the RAG database."""
    reference_questions: List[str]
    source_query: str