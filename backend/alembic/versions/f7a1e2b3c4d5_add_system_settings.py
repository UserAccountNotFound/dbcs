"""Добавление таблицы system_settings."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f7a1e2b3c4d5"
down_revision: Union[str, None] = "e6c0d4f9b2a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "system_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("docs_enabled", sa.Boolean(), nullable=False),
        sa.Column("redoc_enabled", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_system_settings")),
    )
    op.execute(
        sa.text(
            """
            INSERT INTO system_settings (id, docs_enabled, redoc_enabled, updated_at)
            VALUES (1, 1, 1, UTC_TIMESTAMP())
            """
        )
    )


def downgrade() -> None:
    op.drop_table("system_settings")
