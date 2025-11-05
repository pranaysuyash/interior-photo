"""Initial migration: users and transformations tables

Revision ID: 001_initial_migration
Revises:
Create Date: 2025-11-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_migration'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('credits', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('subscription_tier', sa.Enum('FREE', 'PRO', 'ENTERPRISE', name='subscriptiontier'), nullable=False, server_default='FREE'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_id', 'users', ['id'], unique=False)

    # Create transformations table
    op.create_table(
        'transformations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('job_id', sa.String(length=255), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='transformationstatus'), nullable=False, server_default='PENDING'),
        sa.Column('original_image_url', sa.String(length=1024), nullable=False),
        sa.Column('transformed_image_url', sa.String(length=1024), nullable=True),
        sa.Column('vibe', sa.String(length=100), nullable=False),
        sa.Column('colors', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('processing_time_seconds', sa.Float(), nullable=True),
        sa.Column('model_used', sa.String(length=255), nullable=True),
        sa.Column('prompt_used', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_transformations_id', 'transformations', ['id'], unique=False)
    op.create_index('ix_transformations_job_id', 'transformations', ['job_id'], unique=True)
    op.create_index('ix_transformations_user_id', 'transformations', ['user_id'], unique=False)
    op.create_index('ix_transformations_status', 'transformations', ['status'], unique=False)

    # Create reference_images table
    op.create_table(
        'reference_images',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transformation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('image_url', sa.String(length=1024), nullable=False),
        sa.Column('image_type', sa.String(length=50), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['transformation_id'], ['transformations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_reference_images_id', 'reference_images', ['id'], unique=False)
    op.create_index('ix_reference_images_transformation_id', 'reference_images', ['transformation_id'], unique=False)


def downgrade() -> None:
    # Drop reference_images table
    op.drop_index('ix_reference_images_transformation_id', table_name='reference_images')
    op.drop_index('ix_reference_images_id', table_name='reference_images')
    op.drop_table('reference_images')

    # Drop transformations table
    op.drop_index('ix_transformations_status', table_name='transformations')
    op.drop_index('ix_transformations_user_id', table_name='transformations')
    op.drop_index('ix_transformations_job_id', table_name='transformations')
    op.drop_index('ix_transformations_id', table_name='transformations')
    op.drop_table('transformations')

    # Drop users table
    op.drop_index('ix_users_id', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')

    # Drop enums
    sa.Enum(name='transformationstatus').drop(op.get_bind())
    sa.Enum(name='subscriptiontier').drop(op.get_bind())
