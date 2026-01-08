"""add_student_number_tracking

Revision ID: 1083c9966354
Revises: c8f5a2b9d1e3
Create Date: 2026-01-08 13:32:56.385351

Description: Add student_number_tracking table and get_next_student_number function
for sequential student ID generation per school+major combination.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '1083c9966354'
down_revision: Union[str, Sequence[str], None] = 'c8f5a2b9d1e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create student_number_tracking table and get_next_student_number function."""
    conn = op.get_bind()
    
    # =========================================================================
    # CREATE STUDENT NUMBER TRACKING TABLE
    # =========================================================================
    
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS public.student_number_tracking (
            id BIGSERIAL PRIMARY KEY,
            school_id BIGINT NOT NULL REFERENCES public.schools(id) ON DELETE CASCADE,
            major_id BIGINT NOT NULL REFERENCES public.majors(id) ON DELETE CASCADE,
            last_student_number INT NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(school_id, major_id)
        );
    """))
    
    # Index for efficient lookups
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_student_number_tracking_school_major 
            ON public.student_number_tracking(school_id, major_id);
    """))
    
    # =========================================================================
    # FUNCTION: get_next_student_number
    # Atomically gets and increments student number for school+major combination
    # =========================================================================
    
    conn.execute(text("""
        CREATE OR REPLACE FUNCTION public.get_next_student_number(
            p_school_id BIGINT,
            p_major_id BIGINT
        )
        RETURNS INT
        LANGUAGE plpgsql
        AS $$
        DECLARE
            v_next_number INT;
        BEGIN
            -- Insert or update the tracking record and return the new number
            INSERT INTO public.student_number_tracking (school_id, major_id, last_student_number)
            VALUES (p_school_id, p_major_id, 1)
            ON CONFLICT (school_id, major_id)
            DO UPDATE SET 
                last_student_number = student_number_tracking.last_student_number + 1,
                updated_at = now()
            RETURNING last_student_number INTO v_next_number;
            
            RETURN v_next_number;
        END;
        $$;
    """))


def downgrade() -> None:
    """Drop get_next_student_number function and student_number_tracking table."""
    conn = op.get_bind()
    
    # Drop function
    conn.execute(text("DROP FUNCTION IF EXISTS public.get_next_student_number(BIGINT, BIGINT);"))
    
    # Drop table
    conn.execute(text("DROP TABLE IF EXISTS public.student_number_tracking;"))
