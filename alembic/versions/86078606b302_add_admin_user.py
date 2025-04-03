"""Add admin user

Revision ID: 86078606b302
Revises: feb470a0c72f
Create Date: 2025-02-20 00:27:59.175790

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from app.utils import hash_password


# revision identifiers, used by Alembic.
revision: str = '86078606b302'
down_revision: Union[str, None] = 'feb470a0c72f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Define the admins table
    admin_table = table(
        "admins",
        column("username", sa.String),
        column("hashed_password", sa.String),  # Ensure this matches your DB column
    )

    # Insert an admin user with a hashed password
    op.execute(
        admin_table.insert().values(
            username="admin",
            hashed_password=hash_password("admin123")  # Securely hash the password
        )
    )


def downgrade() -> None:
     # Remove the admin user (if needed)
    op.execute("DELETE FROM admins WHERE username = 'admin'")
