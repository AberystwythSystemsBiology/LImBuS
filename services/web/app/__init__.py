import os

from flask import Flask, g, render_template
from config import app_config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

import sqlalchemy as sa

from sqlalchemy_continuum import make_versioned



db = SQLAlchemy()
login_manager = LoginManager()

# blueprint imports
from .admin import admin as admin_blueprint
from .misc import misc as misc_blueprint
from .attribute import attribute as attribute_blueprint
from .setup import setup as setup_blueprint
from .auth import auth as auth_blueprint
from .document import document as doc_blueprint
from .sample import sample as sample_blueprint
from .donor import donor as donor_blueprint
from .patientconsentform import pcf as pcf_blueprint
from .processing import processing as processing_blueprint
from .storage import storage as storage_blueprint


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_object(app_config[os.environ["FLASK_CONFIG"]])
    app.config.from_pyfile("config.py")

    make_versioned(user_cls=None)

    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    migrate = Migrate(app, db)

    # Load in models here
    from app.auth import models as auth_models
    from app.misc import models as misc_models
    from app.document import models as doc_models
    from app.sample import models as sample_models
    from app.patientconsentform import models as pcf_models
    from app.processing import models as processing_models
    from app.storage import models as storage_models
    from app.attribute import models as attribute_models
    from app.donor import models as donor_models

    app.register_blueprint(misc_blueprint)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(setup_blueprint, url_prefix="/setup")
    app.register_blueprint(admin_blueprint, url_prefix="/admin")
    app.register_blueprint(attribute_blueprint, url_prefix="/attributes")
    app.register_blueprint(processing_blueprint, url_prefix="/processing")
    app.register_blueprint(doc_blueprint, url_prefix="/documents")
    app.register_blueprint(sample_blueprint, url_prefix="/samples")
    app.register_blueprint(donor_blueprint, url_prefix="/donors")
    app.register_blueprint(pcf_blueprint, url_prefix="/pcf")
    app.register_blueprint(storage_blueprint, url_prefix="/storage")

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("misc/404.html"), 404

    sa.orm.configure_mappers()
    
    return app
