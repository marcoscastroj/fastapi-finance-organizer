"""create_investments_table

Revision ID: c5e937d11820
Revises: a8d29f12b614
Create Date: 2026-08-18 23:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5e937d11820'
down_revision: Union[str, Sequence[str], None] = 'a8d29f12b614'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'investments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('ticker', sa.String(length=20), nullable=False),
        sa.Column('nome', sa.String(length=255), nullable=False),
        sa.Column('classe', sa.String(length=50), nullable=False),
        sa.Column('quantidade', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('preco_medio', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('cotacao_atual', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_investments_user_id'), 'investments', ['user_id'], unique=False)
    op.create_index(op.f('ix_investments_ticker'), 'investments', ['ticker'], unique=False)
    op.create_index(op.f('ix_investments_classe'), 'investments', ['classe'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_investments_classe'), table_name='investments')
    op.drop_index(op.f('ix_investments_ticker'), table_name='investments')
    op.drop_index(op.f('ix_investments_user_id'), table_name='investments')
    op.drop_table('investments')
