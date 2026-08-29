"""Добавление таблицы smtp_settings."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e6c0d4f9b2a3"
down_revision: Union[str, None] = "d5b9c3e8a1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "smtp_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("host", sa.String(length=255), nullable=False),
        sa.Column("port", sa.Integer(), nullable=False),
        sa.Column("use_tls", sa.Boolean(), nullable=False),
        sa.Column("use_ssl", sa.Boolean(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=False),
        sa.Column("password", sa.Text(), nullable=False),
        sa.Column("from_email", sa.String(length=255), nullable=False),
        sa.Column("from_name", sa.String(length=255), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_smtp_settings")),
    )
    op.execute(
        sa.text(
            """
            INSERT INTO smtp_settings (
                id, enabled, host, port, use_tls, use_ssl,
                username, password, from_email, from_name, updated_at
            ) VALUES (
                1, 0, 'smtp.gmail.com', 587, 1, 0,
                '', '', '', 'DBCS', UTC_TIMESTAMP()
            )
            """
        )
    )


def downgrade() -> None:
    op.drop_table("smtp_settings")
