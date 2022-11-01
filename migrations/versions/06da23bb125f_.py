"""empty message

Revision ID: 06da23bb125f
Revises: 1a8b1055b4fe
Create Date: 2022-09-04 17:02:03.224238

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '06da23bb125f'
down_revision = '1a8b1055b4fe'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('social_media_posts',
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('post_url', sa.Text(), nullable=False),
    sa.Column('post_text', sa.Text(), nullable=False),
    sa.Column('post_image_url', sa.Text(), nullable=True),
    sa.Column('uploaded', sa.Boolean(), nullable=True),
    sa.Column('upload_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['upload_id'], ['media_uploads.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('social_media_posts')
    # ### end Alembic commands ###