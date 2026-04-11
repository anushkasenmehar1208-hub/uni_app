"""add other_degree_text to usermemory

Revision ID: a1b2c3d4e5f6
Revises: 5ed222f79f8b
Create Date: 2026-04-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '5ed222f79f8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('usermemory', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'other_degree_text',
                sqlmodel.sql.sqltypes.AutoString(),
                server_default=sa.text("('')"),
                nullable=False,
            )
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('usermemory', schema=None) as batch_op:
        batch_op.drop_column('other_degree_text')
