"""add card phone_additional and messengers

Revision ID: c4a8e2f91b0d
Revises: b3491f91cc0b
Create Date: 2026-08-10 11:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4a8e2f91b0d"
down_revision: Union[str, Sequence[str], None] = "b3491f91cc0b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("cards", sa.Column("phone_additional", sa.String(length=64), nullable=True))
    op.add_column("cards", sa.Column("telegram", sa.String(length=255), nullable=True))
    op.add_column("cards", sa.Column("whatsapp", sa.String(length=255), nullable=True))
    op.add_column("cards", sa.Column("viber", sa.String(length=255), nullable=True))
    op.add_column("cards", sa.Column("wechat", sa.String(length=255), nullable=True))
    op.add_column("cards", sa.Column("messenger_max", sa.String(length=255), nullable=True))
    op.add_column("cards", sa.Column("discord", sa.String(length=255), nullable=True))
    op.add_column("cards", sa.Column("vk", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("cards", "vk")
    op.drop_column("cards", "discord")
    op.drop_column("cards", "messenger_max")
    op.drop_column("cards", "wechat")
    op.drop_column("cards", "viber")
    op.drop_column("cards", "whatsapp")
    op.drop_column("cards", "telegram")
    op.drop_column("cards", "phone_additional")
