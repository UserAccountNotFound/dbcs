"""Добавление таблицы backup_settings."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d5b9c3e8a1f2"
down_revision: Union[str, None] = "c4a8e2f91b0d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "backup_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.String(length=512), nullable=False),
        sa.Column("schedule", sa.String(length=20), nullable=False),
        sa.Column("schedule_hour", sa.Integer(), nullable=False),
        sa.Column("schedule_weekday", sa.Integer(), nullable=False),
        sa.Column("retention_count", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("last_run_at", sa.DateTime(), nullable=True),
        sa.Column("last_status", sa.String(length=32), nullable=True),
        sa.Column("last_message", sa.Text(), nullable=True),
        sa.Column("last_backup_file", sa.String(length=512), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_backup_settings")),
    )
    op.execute(
        sa.text(
            """
            INSERT INTO backup_settings (
                id, storage_path, schedule, schedule_hour, schedule_weekday,
                retention_count, enabled, updated_at
            ) VALUES (
                1, '/var/lib/dbcs/backups', 'daily', 3, 0, 7, 1, UTC_TIMESTAMP()
            )
            """
        )
    )


def downgrade() -> None:
    op.drop_table("backup_settings")
