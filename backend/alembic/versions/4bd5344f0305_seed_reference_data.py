"""seed_reference_data

Revision ID: 4bd5344f0305
Revises: 5d226f6a67a4
Create Date: 2026-01-08 12:26:58.567790

Description: Seed reference data (roles, schools, majors)
This migration populates the reference tables with initial data.
Uses INSERT with ON CONFLICT to make the migration idempotent.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '4bd5344f0305'
down_revision: Union[str, Sequence[str], None] = '5d226f6a67a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    
    # ============================================================================
    # SEED ROLES
    # ============================================================================
    conn.execute(text("""
        INSERT INTO roles (id, role_name)
        VALUES 
            (1, 'admin'),
            (2, 'teacher'),
            (3, 'student')
        ON CONFLICT (role_name) DO NOTHING
    """))
    
    # Reset sequence if needed
    conn.execute(text("""
        SELECT setval('roles_id_seq', (SELECT MAX(id) FROM roles))
    """))
    
    # ============================================================================
    # SEED SCHOOLS
    # ============================================================================
    conn.execute(text("""
        INSERT INTO schools (id, school_name)
        VALUES 
            (1, '이리공업고등학교'),
            (2, '전북기계공업고등학교')
        ON CONFLICT (school_name) DO NOTHING
    """))
    
    # Reset sequence if needed
    conn.execute(text("""
        SELECT setval('schools_id_seq', (SELECT MAX(id) FROM schools))
    """))
    
    # ============================================================================
    # SEED MAJORS
    # ============================================================================
    conn.execute(text("""
        INSERT INTO majors (id, major_name)
        VALUES 
            (1, '전기전자과'),
            (2, '전기제어'),
            (3, '자동화기계'),
            (4, '스마트팩토리'),
            (5, '조리제빵'),
            (6, '기계설계'),
            (7, '소프트웨어과')
        ON CONFLICT (major_name) DO NOTHING
    """))
    
    # Reset sequence if needed
    conn.execute(text("""
        SELECT setval('majors_id_seq', (SELECT MAX(id) FROM majors))
    """))

    # ============================================================================
    # SEED ALLOWED EMAIL DOMAINS (students)
    # ============================================================================
    conn.execute(text("""
        INSERT INTO allowed_email_domains (id, domain, description, is_active)
        VALUES
            (1, 'students.internal', 'Internal domain for student accounts (must not be deleted)', true)
        ON CONFLICT (domain) DO NOTHING
    """))

    # Reset sequence if needed
    conn.execute(text("""
        SELECT setval('allowed_email_domains_id_seq', (SELECT MAX(id) FROM allowed_email_domains))
    """))


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    
    # Delete seeded data in reverse order
    conn.execute(text("DELETE FROM allowed_email_domains WHERE domain = 'students.internal'"))
    conn.execute(text("DELETE FROM majors WHERE id IN (1, 2, 3, 4, 5, 6, 7)"))
    conn.execute(text("DELETE FROM schools WHERE id IN (1, 2)"))
    conn.execute(text("DELETE FROM roles WHERE id IN (1, 2, 3)"))
