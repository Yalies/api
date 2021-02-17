"""rename username

Revision ID: 2c0626fc0cc4
Revises: 3f4af6f2ac8a
Create Date: 2021-02-16 20:11:59.125644

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2c0626fc0cc4'
down_revision = '3f4af6f2ac8a'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('key', sa.Column('user_id', sa.String(), nullable=True))
    op.drop_constraint('key_user_username_fkey', 'key', type_='foreignkey')
    op.alter_column('users', 'username', new_column_name='id')
    op.create_foreign_key('key_user_id_fkey', 'key', 'users', ['user_id'], ['id'])
    op.drop_column('key', 'user_username')
    #op.add_column('users', sa.Column('id', sa.String(), nullable=False))
    #op.drop_column('users', 'username')


def downgrade():
    pass
