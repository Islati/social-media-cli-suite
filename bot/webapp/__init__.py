import datetime
import os

import maya
import pytz
from flask import Flask, current_app, render_template, after_this_request, make_response, request, Request, \
    send_from_directory
from bot.webapp.blueprints.post_calendar import post_calendar
from bot.webapp.config import ProductionConfig
from bot.webapp.extensions import db, migrations, mail, caching, cors

from bot.webapp.blueprints.reddit_feed_importer import feed_importer as feed_importer_blueprint

from flask import current_app


def debug(message):
    """
    Print debug message to logger
    :param message:
    :return:
    """
    current_app.logger.debug(message)


def create_app(configuration=None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(configuration)

    app.config['CORS_HEADERS'] = 'Content-Type'

    db.init_app(app=app)
    migrations.init_app(app=app, db=db)
    mail.init_app(app=app)
    caching.init_app(app=app)
    cors.init_app(app=app,
                  resources={r"*": {"origins": "*"}},
                  headers="Content-Type")
    print("Cors initialized")

    from bot.webapp import models
    app.app_context().push()

    @app.shell_context_processor
    def shell_context():
        return {
            'db': db,
            'app': app,
            'mail': mail
        }

    # only create the admin panel out of production
    if not isinstance(configuration, ProductionConfig):
        print("Initializing Blueprints for the admin panel.")

        app.register_blueprint(feed_importer_blueprint)
        app.register_blueprint(post_calendar)



    return app
