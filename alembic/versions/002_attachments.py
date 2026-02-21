"""
Add attachments table

Revision ID: 002_attachments
Revises: 001_baseline_migration
Create Date: 2025-02-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = '002_attachments'
down_revision: Union[str, None] = '001_baseline'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создаём таблицу attachments
    op.create_table(
        'attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=512), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(length=127), nullable=True),
        sa.Column(
            'created_at',
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("timezone('UTC', current_timestamp)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['message_id'],
            ['messages.id'],
            ondelete='CASCADE',
        ),
    )
    
    # Индекс для быстрого поиска вложений по message_id
    op.create_index(
        'idx_attachments_message_id',
        'attachments',
        ['message_id'],
    )


def downgrade() -> None:
    op.drop_index('idx_attachments_message_id', table_name='attachments')
    op.drop_table('attachments')
