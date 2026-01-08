"""create interview queue table

Revision ID: 687a506bdc0b
Revises: 1083c9966354
Create Date: 2026-01-08 15:23:33.599178

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '687a506bdc0b'
down_revision: Union[str, Sequence[str], None] = '1083c9966354'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Create the table
    op.create_table(
        'interview_queue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_type', sa.Text(), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.Text(), server_default='pending', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('locked_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create the index
    op.create_index(
        'idx_queue_status_created', 
        'interview_queue', 
        ['status', 'created_at'], 
        unique=False
    )


def downgrade() -> None:
    # Drop index first
    op.drop_index('idx_queue_status_created', table_name='interview_queue')
    # Drop table
    op.drop_table('interview_queue')