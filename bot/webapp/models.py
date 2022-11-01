import datetime
import uuid

import maya
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.orm import backref

from bot.webapp.database import db, SqlModel, SurrogatePK, TimeMixin

"""
Secondary table for the social media posts to show many-to-many relationship with hashtags.
"""
post_hashtags_table = db.Table('post_hashtags',
                               db.Column('post_id', db.Integer, db.ForeignKey('social_media_posts.id')),
                               db.Column('hashtag_id', db.Integer, db.ForeignKey('hashtags.id')))


class User(SqlModel, TimeMixin, SurrogatePK):
    __tablename__ = 'users'
    username = db.Column(db.String, unique=True, nullable=False)

    twitter_url = db.Column(db.String, unique=True, nullable=True)
    instagram_url = db.Column(db.String, unique=True, nullable=True)
    facebook_url = db.Column(db.String, unique=True, nullable=True)
    youtube_url = db.Column(db.String, unique=True, nullable=True)
    spotify_url = db.Column(db.String, unique=True, nullable=True)
    soundcloud_url = db.Column(db.String, unique=True, nullable=True)

    active_feed = db.Column(db.Boolean, default=True)
    feed_priority = db.Column(db.Float, default=1, nullable=False)  # lower = higher priority

    def __init__(self, username, twitter_url=None, instagram_url=None, facebook_url=None, youtube_url=None,
                 spotify_url=None, soundcloud_url=None, active_feed=True, feed_priority=1):
        super().__init__(
            username=username,
            twitter_url=twitter_url,
            instagram_url=instagram_url,
            facebook_url=facebook_url,
            youtube_url=youtube_url,
            spotify_url=spotify_url,
            soundcloud_url=soundcloud_url,
            active_feed=active_feed,
            feed_priority=feed_priority
        )


class RedditRepost(SqlModel, SurrogatePK, TimeMixin):
    """
    Model represents a repost (scraped from reddit)
    """

    __tablename__ = "reddit_reposts"

    post_id = db.Column(db.String(255), nullable=False, unique=True)
    title = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(255), nullable=False)

    def __init__(self, post_id, title, url):
        super().__init__(post_id=post_id, title=title, url=url)

    @staticmethod
    def get_post(post_id):
        return RedditRepost.query.filter_by(post_id=post_id).first()

    @staticmethod
    def has_been_posted(post_id):
        return RedditRepost.get_post(post_id) is not None


class SentMail(SurrogatePK, TimeMixin, SqlModel):
    """
    Messages sent to users.
    """
    __tablename__ = "sent_mail"

    contact_id = db.Column(db.Integer, db.ForeignKey("contacts.id"), nullable=False)
    contact = db.relationship("Contact", backref=backref('sent_mail', uselist=True), uselist=False)

    mail_id = db.Column(db.Integer, db.ForeignKey("mail_messages.id"), nullable=False)
    mail = db.relationship("MailMessage", backref=backref('sent_mail', uselist=True), uselist=False)

    def __init__(self, contact, mail):
        super().__init__(
            contact=contact,
            contact_id=contact.id,
            mail=mail,
            mail_id=mail.id
        )


class Contact(SurrogatePK, TimeMixin, SqlModel):
    """
    Contact information for a user.
    """
    __tablename__ = "contacts"

    full_name = db.Column(db.Text, nullable=False)
    instagram_url = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    bio = db.Column(db.Text, nullable=True)
    business = db.Column(db.Boolean, default=False, nullable=False)
    verified_email = db.Column(db.Boolean, default=False, nullable=False)
    verification_requested = db.Column(db.Boolean, default=False, nullable=True)

    def __init__(self, full_name, instagram_url, email, bio, business, verified_email, verification_requested=False):
        super().__init__(
            full_name=full_name,
            instagram_url=instagram_url,
            email=email,
            business=business,
            bio=bio,
            verified_email=verified_email,
            verification_requested=verification_requested
        )

    @hybrid_property
    def has_emailed_in_past_week(self):
        """
        Check if the user has been emailed recently.
        """
        return self.has_emailed_recently(days=7)

    @hybrid_property
    def has_emailed_in_past_month(self):
        return self.has_emailed_recently(days=30)

    @hybrid_method
    def has_emailed_recently(self, days):
        return SentMail.query.filter(SentMail.created_at >= maya.now().subtract(days=days).datetime(),
                                     SentMail.contact_id == self.id).count() > 0


class MailMessage(SurrogatePK, TimeMixin, SqlModel):
    """
    Message that is sent via mail. Re-used across multiple users.
    """
    __tablename__ = 'mail_messages'

    name = db.Column(db.Text, nullable=False, unique=True)
    subject = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    html = db.Column(db.Text, nullable=True)

    def __init__(self, name, subject, body, html=None):
        super().__init__(
            name=name,
            subject=subject,
            body=body,
            html=html
        )

    def __repr__(self):
        return f"MailMessage(id={self.id}, to={self.to}, subject={self.subject},name={self.name})"


class Hashtag(SurrogatePK, TimeMixin, SqlModel):
    """
    Hashtags used on posts.
    :param SurrogatePK:
    :param TimeMixin:
    :param SqlModel:
    :return:
    """
    __tablename__ = "hashtags"

    name = db.Column(db.String(255), nullable=False)

    def __init__(self, name):
        super().__init__(name=name)


class ImageDb(SurrogatePK, TimeMixin, SqlModel):
    """
    Image class. Used for posts.
    """
    __tablename__ = "images"

    url = db.Column(db.String(255), nullable=False)
    title = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)

    def __init__(self, url, title, description):
        super().__init__(url=url, title=title, description=description)


class VideoClip(SurrogatePK, TimeMixin, SqlModel):
    """
    Represents a previously created video clip (with the bot)
    """
    __tablename__ = "video_clips"

    url = db.Column(db.String(255), nullable=False)
    title = db.Column(db.Text, nullable=False)
    start_time = db.Column(db.Integer, nullable=False)
    duration = db.Column(db.Integer, nullable=False)

    def __init__(self, url, title, start_time, duration):
        super().__init__(url=url, title=title, start_time=start_time, duration=duration)


class MediaUpload(SurrogatePK, TimeMixin, SqlModel):
    """
    Represents a media upload to the API
    """
    __tablename__ = "media_uploads"

    access_url = db.Column(db.Text, nullable=False)
    content_type = db.Column(db.Text, nullable=False)
    upload_url = db.Column(db.Text, nullable=False)

    uploaded = db.Column(db.Boolean, default=False)

    clip = db.relationship("VideoClip", backref=backref("upload", uselist=False), uselist=False)
    clip_id = db.Column(db.Integer, db.ForeignKey('video_clips.id'), nullable=True)

    image = db.relationship("ImageDb", backref=backref("upload", uselist=False), uselist=False)
    image_id = db.Column(db.Integer, db.ForeignKey('images.id'), nullable=True)

    def __init__(self, access_url, content_type, upload_url, clip=None, image=None):
        super().__init__(access_url=access_url, content_type=content_type, upload_url=upload_url, uploaded=False,
                         clip=clip, clip_id=clip.id if clip is not None else None, image=image,
                         image_id=image.id if image is not None else None)

    @hybrid_property
    def is_expired(self):
        return datetime.datetime.utcnow() >= self.created_at + datetime.timedelta(days=30)

    @hybrid_property
    def is_video(self):
        return self.clip is not None

    @hybrid_property
    def is_image(self):
        return self.image is not None


class SocialMediaPost(SurrogatePK, TimeMixin, SqlModel):
    """
    Represents a social media post made with the API
    """
    __tablename__ = "social_media_posts"

    api_id = db.Column(db.Text, nullable=True)
    platforms = db.Column(db.Text, nullable=True)
    post_url = db.Column(db.Text, nullable=True)

    title = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)

    post_time = db.Column(db.DateTime, nullable=True)

    media_upload = db.relationship("MediaUpload", backref=backref("social_media_post", uselist=False), uselist=False)
    media_upload_id = db.Column(db.Integer, db.ForeignKey('media_uploads.id'), nullable=True)

    hashtags = db.relationship("Hashtag", secondary=post_hashtags_table, backref="posts")

    def __init__(self, api_id, platforms, post_time, media_upload, hashtags, post_url=None, title=None,
                 description=None):
        super().__init__(api_id=api_id, platforms=platforms,
                         post_time=maya.MayaDT.from_iso8601(post_time).datetime(),
                         post_url=post_url,
                         media_upload=media_upload,
                         media_upload_id=media_upload.id,
                         hashtags=[Hashtag.get_or_create(name=hashtag) for hashtag in hashtags],
                         title=title,
                         description=description.replace("\n", "\u2063\n") if description is not None else None)

    @hybrid_property
    def is_video(self):
        return self.media_upload.is_video

    @hybrid_property
    def is_image(self):
        return self.media_upload.is_image


class PublishedSocialMediaPost(SurrogatePK, TimeMixin, SqlModel):
    """
    Represents a social media post made with the API
    """
    __tablename__ = "published_social_media_posts"

    platform = db.Column(db.Text, nullable=False)
    social_media_post_id = db.Column(db.Integer, db.ForeignKey('social_media_posts.id'), nullable=False)
    social_media_post = db.relationship("SocialMediaPost", backref=backref("published_data", uselist=True),
                                        uselist=False)

    post_url = db.Column(db.Text, nullable=True)

    def __init__(self, platform, social_media_post, post_url):
        super().__init__(platform=platform, social_media_post=social_media_post,
                         social_media_post_id=social_media_post.id,
                         post_url=post_url)
