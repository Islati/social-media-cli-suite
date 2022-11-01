import json
import pprint

import requests
from flask import Blueprint, current_app, jsonify, request
from flask_cors import cross_origin

from bot import utils
from bot.webapp.blueprints.reddit_feed_importer import build_cors_preflight_response

post_calendar = Blueprint('post_calendar', __name__, url_prefix='/scheduled-posts')


@post_calendar.route('/', methods=['GET', 'OPTIONS'])
@cross_origin()
def index():
    if request.method == "OPTIONS":
        return build_cors_preflight_response()
    resp = requests.get('https://app.ayrshare.com/api/history',
                        headers={'Authorization': f'Bearer {current_app.config.get("AYRSHARE_API_KEY")}'})

    print(resp)
    _post_history = json.loads(resp.text)

    _events = []
    for post in _post_history:
        print(pprint.pformat(post))
        # type scheduled

        status = post.get('status', None)
        if status is None or status == 'error':
            # Only show successful posts.
            # (Error posts can be fixed before shown on schedule)
            continue

        post_type = post.get('type', None)
        post_time_utc = post['scheduleDate']['utc']
        video = post.get('isVideo', None)
        if video == 'True':
            video = True

        _events.append(dict(
            id=post.get('id', None),
            status=post['status'],
            type=post['type'],
            platforms=post['platforms'],
            media=post['mediaUrls'],
            post=post['post'],
            video=video,
            time=post_time_utc
        ))

    return jsonify({'posts': _events})
