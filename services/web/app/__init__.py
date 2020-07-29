from __future__ import absolute_import
import os

from flask import Flask, g, render_template

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_marshmallow import Marshmallow

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_continuum import make_versioned
from sqlalchemy_continuum.plugins import FlaskPlugin
from sqlalchemy_continuum.plugins import PropertyModTrackerPlugin


from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin

db = SQLAlchemy()
ma = Marshmallow()

# Create an APISpec
spec = APISpec(
    title="LImBuS API Documentation",
    version="20.08",
    openapi_version="3.0.2",
    plugins=[FlaskPlugin(), MarshmallowPlugin()],
)


from .base import BaseModel as BM

Base = declarative_base(cls=BM)
Base.query = db.session.query_property()

login_manager = LoginManager()
from .auth.models import UserAccount

make_versioned(
    user_cls=UserAccount, plugins=[FlaskPlugin(), PropertyModTrackerPlugin()]
)

# Blueprint imports:
from .misc import misc as misc_blueprint
from .setup import setup as setup_blueprint
from .auth import auth as auth_blueprint
from .api import api as api_blueprint

# Flask-manage imports:
from .commands import cmd_setup as cmd_setup_blueprint


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_pyfile("config.py")

    db.init_app(app)
    ma.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Blueprint Registers
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(misc_blueprint)
    app.register_blueprint(setup_blueprint, url_prefix="/setup")

    # API blueprint
    app.register_blueprint(api_blueprint, url_prefix="/api")
    ## Specific to CMD.
    app.register_blueprint(cmd_setup_blueprint)

    from app.errors import error_handlers

    for error_handler in error_handlers:
        app.register_error_handler(
            error_handler["code_or_exception"], error_handler["func"]
        )

    from app.auth.api import auth_new_user

    # Register the path and the entities within it
    with app.test_request_context():
        spec.path(view=auth_new_user)

    return app
