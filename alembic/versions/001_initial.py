"""Initial migration

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'rooms',
        sa.Column('id', sa.String(5), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('creator_id', sa.String(255), nullable=False),
        sa.Column('creator_name', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        'queue_entries',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('room_id', sa.String(5), sa.ForeignKey('rooms.id'), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('user_name', sa.String(255), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='waiting'),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('queue_entries')
    op.drop_table('rooms')
