class Config(object):
    """
    Base configuration object.
    """
    Debug = True,
    SQLALCHEMY_DATABASE_URI = "postgresql://islatisk@localhost:5432/vidbot"
    POSTS = []
    FEED_PAGE_SIZE = 200
    YOUTUBE_API_KEY = "<your_api_key>"
    SECRET_KEY = "<secret_key>"
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300

    FLASK_DEBUG = 1

    CORS_HEADERS = "Content-Type"

    TAGS = [
        ('[ytdesc]', lambda vidbot: vidbot.yt_vid.description),
        ('[yttitle]', lambda vidbot: vidbot.yt_vid.title),
    ]

    MAIL_SERVER = 'smtp.sendgrid.net'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_DEBUG = False
    MAIL_USERNAME = "apikey"
    MAIL_PASSWORD = "<password for mail api>"
    MAIL_DEFAULT_SENDER = None
    MAIL_MAX_EMAILS = None
    MAIL_SUPPRESS_SEND = False
    MAIL_ASCII_ATTACHMENTS = False

    EMAIL_VALIDATION_TIMEOUT = 3

    AYRSHARE_API_KEY = "<ayrshare api key>"
    SENDGRID_API_KEY = "<sendgrid api key>"

    # Debounce.io API Key
    EMAIL_VALIDATION_API_KEY = '<debounce.io key>'

    REDDIT_USERNAME = ""
    REDDIT_PASSWORD = ""
    REDDIT_CLIENT_ID = ""
    REDDIT_CLIENT_SECRET = ""


class DefaultConfig(Config):
    """
    Configure the applications values & behaviour.
    """

    Debug = True
    SQLALCHEMY_DATABASE_URI = "postgresql://islatisk@localhost:5432/vidbot"

    TAGS = [
        ('[bio]', '🎶 Music Link in Bio 🔗'),
        ('[ytchannel]', 'https://www.youtube.com/channel/UC1HBD9-ZHbEe1cN8Pa2BL_g'),
        ('[ytvid]', lambda vidbot: vidbot.yt_vid.url),
        ('[skreet]', 'skreet.ca'),
        ('[viddesc]',
         lambda
             vidbot: vidbot.yt_vid.description if vidbot.youtube_video_download_link is not None else vidbot.tiktok_downloader.title if vidbot.tiktok_downloader is not None else ""),
        ('[title]',
         lambda vidbot: vidbot.yt_vid.title if vidbot.youtube_video_download_link is not None else vidbot.post_title),
        ('[keywords]', lambda vidbot: vidbot.compile_keywords()),
        ('[hashtags]', lambda vidbot: vidbot.compile_hashtag_string()),
        ('[ytthumbnail]', lambda vidbot: vidbot.yt_vid.thumbnail_url),
        ('[desc]', lambda vidbot: vidbot.post_description),
        ('[reddit-post-title]', lambda vidbot: vidbot.reddit_post.title if vidbot.reddit_post is not None else "")
    ]

    PLATFORM_DEFAULTS = {
        'twitter': {
            'post': '🎶 Music @ http://skreet.ca 🔗 Follow, Like & Retweet \n\n[desc]',
            'image_alt_text': "[title]"
        },
        'instagram': {
            'post': '🎶 Music @ http://skreet.ca 🔗 Follow, Like & Comment\n[desc]',
        },
        'youtube': {
            'post': '[desc] 🎶 Music @ http://skreet.ca 🔗 Like, Subscribe & Share \n[viddesc]',
            'visibility': "public",
        },
        "facebook": {
            'post': '[desc] \n 🎶 Music @ http://skreet.ca 🔗 Like, Share, Follow & Comment \n[viddesc]',
            'title': '[title]',
            'altText': '[desc]',
            'mediaCaptions': '[desc] \n 🎶 Music @ http://skreet.ca 🔗 Like, Share, Follow & Comment \n[viddesc] [hashtags]'
        }
    }


class ProductionConfig(Config):
    Debug = False
    SQLALCHEMY_DATABASE_URI = "postgresql://islatisk@localhost:5432/vidbot"
