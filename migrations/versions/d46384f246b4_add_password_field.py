"""add password field

Revision ID: d46384f246b4
Revises: 74b5f64c68e4
Create Date: 2025-04-08 09:52:56.207639

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'd46384f246b4'
down_revision: Union[str, None] = '74b5f64c68e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('books', 'published_date',
               existing_type=sa.DATE(),
               nullable=True)
    op.add_column('users', sa.Column('password_hash', sqlmodel.sql.sqltypes.AutoString(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'password_hash')
    op.alter_column('books', 'published_date',
               existing_type=sa.DATE(),
               nullable=False)
    # ### end Alembic commands ###
