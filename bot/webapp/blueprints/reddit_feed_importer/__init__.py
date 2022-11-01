import mimetypes
import pprint
import traceback
from urllib.parse import urlparse
import os

import requests
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session, make_response
from flask_cors import cross_origin
from praw.reddit import Submission

from bot import utils
from bot.services.reddit import client as reddit_client
from bot.webapp.models import RedditRepost, ImageDb, SocialMediaPost

feed_importer = Blueprint('reddit_feed_importer', __name__, template_folder='templates', static_folder='static',
                          url_prefix='/feed-importer')


# todo implement saved subreddits for reposts.

def _get_posts(subreddit, sort_method, limit, allow_reposts=True):
    posts = reddit_client.get_posts(subreddit, limit=limit, sort_method=sort_method)

    if posts is None:
        print(f"Failed to get posts from {subreddit} | sort_method={sort_method} | limit={limit}")
        return []

    # Skip non-image posts & images we've posted before.
    _posts = []
    for post in posts:
        if post.is_self:
            continue

        repost = False

        if RedditRepost.has_been_posted(post.id):
            if not allow_reposts:
                continue

            repost = True

        if post.url is None:
            continue

        if not utils.is_image_file(post.url):
            continue

        _posts.append(
            dict(
                id=post.id,
                url=post.url,
                permalink=post.permalink,
                thumbnail=post.thumbnail,
                title=post.title,
                score=post.score,
                created_utc=post.created_utc,
                author=post.author.name if post.author else "",
                repost=repost,

            )
        )

    return _posts


@feed_importer.route('/', methods=['GET', 'OPTIONS'])
@cross_origin()
def index():
    if request.method == "OPTIONS":
        return build_cors_preflight_response()

    return jsonify({'status': 'Success', 'message': 'Feed Importer'})


reddit_valid_sort_methods = ('hot', 'new', 'rising', 'controversial', 'top')


@cross_origin()
@feed_importer.route('/schedule/', methods=['POST'])
def schedule():
    from bot.utils import upload_file_to_cloud, post_to_social, download_image, get_maya_time

    try:
        _json = request.form
    except:
        _json = request.get_json(force=True)

    post_id = _json['postId']
    media_url = _json['postUrl']
    body = _json['body']
    postWhen = _json['time']
    platforms = _json['platforms']
    tags = _json['tags'] if 'tags' in _json.keys() else []

    subreddit = session.get('subreddit', 'rap')
    sort_method = session.get('sort_method', 'hot')

    # Get submission from reddit API (PRAW object)
    post = Submission(reddit=reddit_client.reddit, id=post_id)

    content_type = mimetypes.guess_type(media_url)[0]
    extension = mimetypes.guess_extension(content_type)
    output_file_name = os.path.basename(urlparse(media_url).path)  # Get filename from url path
    # output_file_name = f"meme-{post.id}-post{extension}"

    # download image
    downloaded_file = download_image(media_url, output_file_name)
    if downloaded_file is None or not os.path.exists(downloaded_file):
        return jsonify({"error": "Failed to download image."}), 400
        # return redirect(url_for('reddit_feed_importer.index', subreddit=subreddit, sort_method=sort_method))

    # try to upload without downloading.
    image_record = ImageDb(url=media_url, title=post.title, description=body)
    image_record.save()

    media_upload = upload_file_to_cloud(downloaded_file, image=image_record)

    if media_upload is None:
        return jsonify({"error": "Failed to upload image."}), 400

    os.remove(downloaded_file)  # remove downloaded file

    social_media_post = SocialMediaPost(None, platforms=platforms,
                                        post_time=get_maya_time(postWhen).datetime(to_timezone='UTC'),
                                        media_upload=media_upload, hashtags=tags, title=post.title,
                                        description=body)

    success, api_key, status_code, response_text = post_to_social(
        platforms.split(',') if (',' in platforms and isinstance(platforms, str)) else [platforms],
        social_media_post)  # all that's required for an image post.

    social_media_post.api_id = api_key

    social_media_post.save(commit=True)
    if not success:
        return jsonify({"error": f"Failed to post to social media. {response_text}"}), 400

    # todo implement source platform & check if it's reddit / facebook / etc.

    # return json for UI display.
    reddit_repost = RedditRepost.query.filter_by(post_id=post.id).first()
    if reddit_repost is None:
        reddit_repost = RedditRepost(post_id=post.id, title=post.title, url=post.url)
    reddit_repost.save(commit=True)
    return jsonify({"status": "success", "message": f"Post scheduled {postWhen}"}), 200


@cross_origin()
@feed_importer.route('/load/', methods=['POST', 'OPTIONS'])
def load(subreddit=None, sort_method=None, limit=100):
    if request.method == "OPTIONS":
        return build_cors_preflight_response()

    _json = request.get_json(force=True)
    subreddit_string = _json['subreddit']
    sort_method_selected = _json['sortType']
    limit = _json.get('limit', 500)

    posts = _get_posts(subreddit_string, sort_method_selected, limit)

    response = jsonify({'posts': posts})

    return response


def build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Access-Control-Allow-Headers', "*")
    response.headers.add('Access-Control-Allow-Methods', "*")
    return response
