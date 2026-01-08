"""Baseline migration from existing Supabase schema

Revision ID: 5d226f6a67a4
Revises: 
Create Date: 2026-01-08 10:48:53.987332

This is a baseline migration that represents the existing database schema
after migrations 001-011 have been applied via the original SQL migration system.

IMPORTANT: This migration should NOT be run on an existing database.
Instead, run: alembic stamp 001_baseline
This marks the migration as applied without executing the upgrade() function.

For new database setups, this migration creates all necessary tables to match
the schema as of migration 011 (custom auth migration).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5d226f6a67a4'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create all tables from the existing schema.
    
    This represents the schema state after migrations 001-011.
    """
    
    # =========================================================================
    # Reference Tables
    # =========================================================================
    
    # roles table
    op.create_table(
        'roles',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('role_name', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('role_name')
    )
    
    # schools table (with school_number from migration 003)
    op.create_table(
        'schools',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('school_name', sa.String(), nullable=False),
        sa.Column('school_number', sa.CHAR(3), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('school_name'),
        sa.UniqueConstraint('school_number')
    )
    
    # majors table (with major_number from migration 003)
    op.create_table(
        'majors',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('major_name', sa.String(), nullable=False),
        sa.Column('major_number', sa.CHAR(4), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('major_name'),
        sa.UniqueConstraint('major_number')
    )
    
    # classes table
    op.create_table(
        'classes',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('class_name', sa.String(), nullable=False),
        sa.Column('grade_level', sa.Integer(), nullable=False),
        sa.CheckConstraint('grade_level IN (1, 2, 3)', name='classes_grade_level_check'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # =========================================================================
    # User Management Tables
    # =========================================================================
    
    # user_profiles table (with hashed_password from migration 011)
    op.create_table(
        'user_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('role_id', sa.BigInteger(), nullable=True),
        sa.Column('hashed_password', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_user_profiles_email', 'user_profiles', ['email'])
    op.create_index('idx_user_profiles_role_id', 'user_profiles', ['role_id'])
    
    # teachers table
    op.create_table(
        'teachers',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('school_id', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['user_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('idx_teachers_user_id', 'teachers', ['user_id'])
    op.create_index('idx_teachers_school_id', 'teachers', ['school_id'])
    
    # students table (with stored_password and quot
    op.create_table(
        'students',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('student_id', sa.String(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('school_id', sa.BigInteger(), nullable=False),
        sa.Column('major_id', sa.BigInteger(), nullable=False),
        sa.Column('current_class_id', sa.BigInteger(), nullable=False),
        sa.Column('interview_session_quota', sa.Integer(), server_default='2', nullable=False),
        sa.Column('stored_password', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('interview_session_quota >= 0', name='students_interview_session_quota_check'),
        sa.ForeignKeyConstraint(['current_class_id'], ['classes.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['major_id'], ['majors.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['user_id'], ['user_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('idx_students_user_id', 'students', ['user_id'])
    op.create_index('idx_students_student_id', 'students', ['student_id'])
    op.create_index('idx_students_school_id', 'students', ['school_id'])
    op.create_index('idx_students_major_id', 'students', ['major_id'])
    op.create_index('idx_students_class_id', 'students', ['current_class_id'])
    
    # =========================================================================
    # Session and Interview Tables
    # =========================================================================
    
    # sessions table (with typ
    op.create_table(
        'sessions',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('student_id', sa.BigInteger(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('type', sa.String(), server_default='job', nullable=False),
        sa.Column('total_score', sa.Numeric(3, 1), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('total_score >= 0 AND total_score <= 10', name='sessions_total_score_check'),
        sa.CheckConstraint("type IN ('job', 'university')", name='sessions_type_check'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_sessions_student_id', 'sessions', ['student_id'])
    
    # documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.BigInteger(), nullable=False),
        sa.Column('cleaned_text', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_documents_session_id', 'documents', ['session_id'])
    
    # summaries table
    op.create_table(
        'summaries',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.BigInteger(), nullable=False),
        sa.Column('strength_text', sa.Text(), nullable=True),
        sa.Column('areas_for_growth_text', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id')
    )
    
    # detailed_feedbacks table
    op.create_table(
        'detailed_feedbacks',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.BigInteger(), nullable=False),
        sa.Column('question_order', sa.Integer(), nullable=True),
        sa.Column('question_text', sa.Text(), nullable=True),
        sa.Column('answer_text', sa.Text(), nullable=True),
        sa.Column('evaluation_text', sa.Text(), nullable=True),
        sa.Column('is_correct', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('content_relevance_score', sa.Numeric(3, 1), nullable=True),
        sa.Column('structure_score', sa.Numeric(3, 1), nullable=True),
        sa.Column('fluency_score', sa.Numeric(3, 1), nullable=True),
        sa.Column('confidence_score', sa.Numeric(3, 1), nullable=True),
        sa.Column('overall_score', sa.Numeric(3, 1), nullable=True),
        sa.CheckConstraint('content_relevance_score >= 0 AND content_relevance_score <= 10', name='detailed_feedbacks_content_relevance_score_check'),
        sa.CheckConstraint('structure_score >= 0 AND structure_score <= 10', name='detailed_feedbacks_structure_score_check'),
        sa.CheckConstraint('fluency_score >= 0 AND fluency_score <= 10', name='detailed_feedbacks_fluency_score_check'),
        sa.CheckConstraint('confidence_score >= 0 AND confidence_score <= 10', name='detailed_feedbacks_confidence_score_check'),
        sa.CheckConstraint('overall_score >= 0 AND overall_score <= 10', name='detailed_feedbacks_overall_score_check'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_detailed_feedbacks_session_id', 'detailed_feedbacks', ['session_id'])
    op.create_index('idx_detailed_feedbacks_session_question_order', 'detailed_feedbacks', ['session_id', 'question_order'])
    
    # next_steps table
    op.create_table(
        'next_steps',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.BigInteger(), nullable=False),
        sa.Column('next_step_order', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description_text', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_next_steps_session_id', 'next_steps', ['session_id'])
    
    # =========================================================================
    # Student Registration Support Tables
    # =========================================================================
    
    # student_number_tracking table
    op.create_table(
        'student_number_tracking',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('school_id', sa.BigInteger(), nullable=False),
        sa.Column('major_id', sa.BigInteger(), nullable=False),
        sa.Column('last_student_number', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['major_id'], ['majors.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('school_id', 'major_id', name='student_number_tracking_school_id_major_id_key')
    )
    op.create_index('idx_student_number_tracking_school_major', 'student_number_tracking', ['school_id', 'major_id'])
    
    # =========================================================================
    # Email Domain Restrictions
    # =========================================================================
    
    op.create_table(
        'allowed_email_domains',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('domain', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('added_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint(r"domain ~ '^[a-z0-9.-]+\.[a-z]{2,}$'", name='domain_format'),
        sa.ForeignKeyConstraint(['added_by'], ['user_profiles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('domain')
    )
    op.create_index('idx_allowed_email_domains_domain', 'allowed_email_domains', ['domain'])
    op.create_index('idx_allowed_email_domains_active', 'allowed_email_domains', ['is_active'], postgresql_where=sa.text('is_active = true'))


def downgrade() -> None:
    """
    Drop all tables created by this migration.
    
    WARNING: This will destroy all data!
    """
    # Drop tables in reverse order of creation (respecting FK dependencies)
    op.drop_table('allowed_email_domains')
    op.drop_table('student_number_tracking')
    op.drop_table('next_steps')
    op.drop_table('detailed_feedbacks')
    op.drop_table('summaries')
    op.drop_table('documents')
    op.drop_table('sessions')
    op.drop_table('students')
    op.drop_table('teachers')
    op.drop_table('user_profiles')
    op.drop_table('classes')
    op.drop_table('majors')
    op.drop_table('schools')
    op.drop_table('roles')
