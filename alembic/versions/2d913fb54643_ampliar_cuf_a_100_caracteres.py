"""ampliar cuf a 100 caracteres

Revision ID: 2d913fb54643
Revises: 5c193cc7c26f
Create Date: 2026-06-15 16:51:38.406458

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2d913fb54643'
down_revision: Union[str, Sequence[str], None] = '5c193cc7c26f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column("facturas", "cuf", type_=sa.String(length=100))
    op.alter_column("notas_credito_debito", "cuf", type_=sa.String(length=100))


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column("notas_credito_debito", "cuf", type_=sa.String(length=50))
    op.alter_column("facturas", "cuf", type_=sa.String(length=50))
