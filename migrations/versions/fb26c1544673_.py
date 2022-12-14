"""empty message

Revision ID: fb26c1544673
Revises: 0159e613cc9e
Create Date: 2022-09-09 21:15:55.432316

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fb26c1544673'
down_revision = '0159e613cc9e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('mail_messages',
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('subject', sa.String(length=255), nullable=False),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('html', sa.Text(), nullable=True),
    sa.Column('sent', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('mail_messages')
    # ### end Alembic commands ###
