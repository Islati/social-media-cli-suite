"""empty message

Revision ID: 15963450ce1a
Revises: 06da23bb125f
Create Date: 2022-09-04 17:15:43.659315

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '15963450ce1a'
down_revision = '06da23bb125f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('social_media_posts', sa.Column('api_id', sa.Text(), nullable=False))
    op.add_column('social_media_posts', sa.Column('platform', sa.Text(), nullable=False))
    op.add_column('social_media_posts', sa.Column('clip_id', sa.Integer(), nullable=True))
    op.drop_constraint('social_media_posts_upload_id_fkey', 'social_media_posts', type_='foreignkey')
    op.create_foreign_key(None, 'social_media_posts', 'video_clips', ['clip_id'], ['id'])
    op.drop_column('social_media_posts', 'upload_id')
    op.drop_column('social_media_posts', 'post_image_url')
    op.drop_column('social_media_posts', 'post_text')
    op.drop_column('social_media_posts', 'uploaded')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('social_media_posts', sa.Column('uploaded', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.add_column('social_media_posts', sa.Column('post_text', sa.TEXT(), autoincrement=False, nullable=False))
    op.add_column('social_media_posts', sa.Column('post_image_url', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('social_media_posts', sa.Column('upload_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'social_media_posts', type_='foreignkey')
    op.create_foreign_key('social_media_posts_upload_id_fkey', 'social_media_posts', 'media_uploads', ['upload_id'], ['id'])
    op.drop_column('social_media_posts', 'clip_id')
    op.drop_column('social_media_posts', 'platform')
    op.drop_column('social_media_posts', 'api_id')
    # ### end Alembic commands ###
