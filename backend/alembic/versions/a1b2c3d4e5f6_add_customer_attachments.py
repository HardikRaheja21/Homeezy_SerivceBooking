"""add customer_attachments to bookings

Revision ID: a1b2c3d4e5f6
Revises: 5e9a4dc1d0c2
Create Date: 2026-05-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "5e9a4dc1d0c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "bookings",
        sa.Column("customer_attachments", sa.JSON(), nullable=True, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_column("bookings", "customer_attachments")
