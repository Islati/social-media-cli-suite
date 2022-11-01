from flask import Blueprint, jsonify, current_app

feed_blueprint = Blueprint("skreet_repost_feed", __name__, url_prefix="/feed")

__DEFAULT_FEED_PAGE_SIZE = 200


@feed_blueprint.route('/')
def index():
    return page(1)


@feed_blueprint.route('/page/<page>')
def page(page):
    page_size = current_app.config.get('FEED_PAGE_SIZE', __DEFAULT_FEED_PAGE_SIZE)

    return jsonify()
