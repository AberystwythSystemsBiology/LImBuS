from __future__ import absolute_import

from .database import db

from flask import Flask

from .commands import cmd_setup as cmd_setup_blueprint
from .api import api as api_blueprint
from .setup import setup as setup_blueprint
from .misc import misc as misc_blueprint
from .auth import auth as auth_blueprint
from .attribute import attribute as attribute_blueprint
from .document import document as document_blueprint
from .consent import consent as consent_blueprint
from .protocol import protocol as protocol_blueprint
from .sample import sample as sample_attribute

from app.errors import error_handlers

from .extensions import register_extensions, register_apispec

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_pyfile("config.py")

    register_extensions(app)
    register_blueprints(app)
    register_error_handlers(app)
    register_apispec(app)

    return app

def register_error_handlers(app):
    for error_handler in error_handlers:
        app.register_error_handler(
            error_handler["code_or_exception"], error_handler["func"]
        )


def register_blueprints(app):
    app.register_blueprint(cmd_setup_blueprint)
    app.register_blueprint(api_blueprint, url_prefix="/api")
    app.register_blueprint(setup_blueprint, url_prefix="/setup")
    app.register_blueprint(misc_blueprint)
    app.register_blueprint(auth_blueprint, url_prefix="/auth")
    app.register_blueprint(attribute_blueprint, url_prefix="/attribute")
    app.register_blueprint(document_blueprint, url_prefix="/document")
    app.register_blueprint(consent_blueprint, url_prefix="/consent")
    app.register_blueprint(protocol_blueprint, url_prefix="/protocol")
    app.register_blueprint(sample_attribute, url_prefix="/sample")

def setup_database(app):
    with app.app_context():
        db.create_all()
