"""Add support_tickets table

Revision ID: a9c1f8b3d527
Revises: 4bb22efad373
Create Date: 2026-02-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9c1f8b3d527'
down_revision: Union[str, None] = '4bb22efad373'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'support_tickets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('zendesk_ticket_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('subject', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(50), nullable=True, server_default='new'),
        sa.Column('priority', sa.String(50), nullable=True, server_default='normal'),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('portal', sa.String(50), nullable=True),
        sa.Column('request_id', sa.String(100), nullable=True),
        sa.Column('resume_version_id', sa.Integer(), nullable=True),
        sa.Column('subscription_tier', sa.String(50), nullable=True),
        sa.Column('tokens_remaining', sa.Integer(), nullable=True),
        sa.Column('zendesk_url', sa.String(500), nullable=True),
        sa.Column('last_comment_at', sa.DateTime(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_support_tickets_id'), 'support_tickets', ['id'], unique=False)
    op.create_index(op.f('ix_support_tickets_zendesk_ticket_id'), 'support_tickets', ['zendesk_ticket_id'], unique=True)
    op.create_index(op.f('ix_support_tickets_user_id'), 'support_tickets', ['user_id'], unique=False)
    op.create_index(op.f('ix_support_tickets_status'), 'support_tickets', ['status'], unique=False)
    op.create_index(op.f('ix_support_tickets_category'), 'support_tickets', ['category'], unique=False)
    op.create_index(op.f('ix_support_tickets_portal'), 'support_tickets', ['portal'], unique=False)
    op.create_index(op.f('ix_support_tickets_request_id'), 'support_tickets', ['request_id'], unique=False)
    op.create_index(op.f('ix_support_tickets_created_at'), 'support_tickets', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_support_tickets_created_at'), table_name='support_tickets')
    op.drop_index(op.f('ix_support_tickets_request_id'), table_name='support_tickets')
    op.drop_index(op.f('ix_support_tickets_portal'), table_name='support_tickets')
    op.drop_index(op.f('ix_support_tickets_category'), table_name='support_tickets')
    op.drop_index(op.f('ix_support_tickets_status'), table_name='support_tickets')
    op.drop_index(op.f('ix_support_tickets_user_id'), table_name='support_tickets')
    op.drop_index(op.f('ix_support_tickets_zendesk_ticket_id'), table_name='support_tickets')
    op.drop_index(op.f('ix_support_tickets_id'), table_name='support_tickets')
    op.drop_table('support_tickets')
