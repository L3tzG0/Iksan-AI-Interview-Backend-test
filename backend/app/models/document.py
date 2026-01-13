"""
Document model for session document storage.

Documents store the extracted text from uploaded files (resumes, CVs)
that are analyzed during interview sessions.

Schema Reference: migrations/001_initial_schema.sql lines 83-87
"""
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.session import Session


class Document(Base):
    """
    Document entity for session document storage.
    
    Attributes:
        id: Primary key (BIGSERIAL)
        session_id: Foreign key to sessions (cascade delete)
        cleaned_text: Extracted and processed text content
        
    Relationships:
        session: The Session this document belongs to
    """
    __tablename__ = "documents"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    cleaned_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Extracted and processed document text",
    )
    
    # Relationships
    session: Mapped["Session"] = relationship(
        "Session",
        back_populates="document",
        lazy="noload",  # No direct usage of Document.session anywhere.
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_documents_session_id", "session_id"),
    )
    
    def __repr__(self) -> str:
        text_preview = self.cleaned_text[:50] if self.cleaned_text else "None"
        return f"<Document(id={self.id}, session_id={self.session_id}, text='{text_preview}...')>"
