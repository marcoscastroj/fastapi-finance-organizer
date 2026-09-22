"""add recurrence to transactions

Revision ID: a8d29f12b614
Revises: e4c8b21a9d0f
Create Date: 2026-08-18 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a8d29f12b614'
down_revision: Union[str, Sequence[str], None] = 'e4c8b21a9d0f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'transactions',
        sa.Column('recorrencia', sa.String(length=20), nullable=False, server_default='UNICA')
    )


def downgrade() -> None:
    op.drop_column('transactions', 'recorrencia')
