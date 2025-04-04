"""removed level column from questions table

Revision ID: 0d48742c743c
Revises: dd86a7c6fbe2
Create Date: 2025-02-18 23:55:35.783753

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0d48742c743c'
down_revision: Union[str, None] = 'dd86a7c6fbe2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('questions', 'level')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('questions', sa.Column('level', sa.VARCHAR(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
