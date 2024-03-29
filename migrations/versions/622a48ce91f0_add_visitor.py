"""add visitor

Revision ID: 622a48ce91f0
Revises: ee481e23e0bd
Create Date: 2022-02-10 19:57:13.255865

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '622a48ce91f0'
down_revision = 'ee481e23e0bd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('person', schema=None) as batch_op:
        batch_op.add_column(sa.Column('visitor', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('person', schema=None) as batch_op:
        batch_op.drop_column('visitor')

    # ### end Alembic commands ###
