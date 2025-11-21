from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin
import uuid

class UserProfile(Base, TimestampMixin):
    """
    User profile table that extends Supabase auth.users.
    The id is a UUID that references auth.users(id).
    Password management is handled by Supabase Auth.
    """
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id"))

    role = relationship("Role", back_populates="user_profiles")
    teacher = relationship("Teacher", back_populates="user_profile", uselist=False)
    student = relationship("Student", back_populates="user_profile", uselist=False)
