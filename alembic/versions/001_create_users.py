"""create users table

Revision ID: 001_create_users
Revises: 
Create Date: 2025-12-08 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_create_users'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('cognito_sub', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    
    # Create unique indexes
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_cognito_sub', 'users', ['cognito_sub'], unique=True)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_users_cognito_sub', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    
    # Drop table
    op.drop_table('users')
