"""Added score field with default value 0

Revision ID: 671e9a13289f
Revises: b67e919041c3
Create Date: 2025-02-12 16:57:43.929088

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '671e9a13289f'
down_revision: Union[str, None] = 'b67e919041c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('score', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'score')
    # ### end Alembic commands ###
