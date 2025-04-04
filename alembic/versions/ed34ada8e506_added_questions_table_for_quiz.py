"""Added questions table for quiz

Revision ID: ed34ada8e506
Revises: 671e9a13289f
Create Date: 2025-02-12 17:12:49.709624

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ed34ada8e506'
down_revision: Union[str, None] = '671e9a13289f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('questions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('question_text', sa.String(), nullable=False),
    sa.Column('option_a', sa.String(), nullable=False),
    sa.Column('option_b', sa.String(), nullable=False),
    sa.Column('option_c', sa.String(), nullable=False),
    sa.Column('option_d', sa.String(), nullable=False),
    sa.Column('correct_option', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_questions_id'), 'questions', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_questions_id'), table_name='questions')
    op.drop_table('questions')
    # ### end Alembic commands ###
