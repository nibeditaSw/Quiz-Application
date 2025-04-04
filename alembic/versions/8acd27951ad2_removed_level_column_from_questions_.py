"""removed level column from questions table

Revision ID: 8acd27951ad2
Revises: 658c0d67a5ca
Create Date: 2025-02-18 17:43:48.715696

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8acd27951ad2'
down_revision: Union[str, None] = '658c0d67a5ca'
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
