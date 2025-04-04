"""created new table user_quiz_stats

Revision ID: aaf1df1c4df0
Revises: 6af3b58238cf
Create Date: 2025-03-07 13:44:36.868320

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aaf1df1c4df0'
down_revision: Union[str, None] = '6af3b58238cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user_quiz_stats',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('category', sa.String(), nullable=False),
    sa.Column('difficulty', sa.String(), nullable=False),
    sa.Column('solved_count', sa.Integer(), nullable=True),
    sa.Column('correct_count', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_quiz_stats_id'), 'user_quiz_stats', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_user_quiz_stats_id'), table_name='user_quiz_stats')
    op.drop_table('user_quiz_stats')
    # ### end Alembic commands ###
