import os

from flask import Flask, g, render_template
from config import app_config
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_continuum import make_versioned
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_admin import Admin

db = SQLAlchemy()
login_manager = LoginManager()
app_admin = Admin(name="Administrator Panel", template_mode="bootstrap3")

# blueprint imports
from .misc import misc as misc_blueprint
from .setup import setup as setup_blueprint
from .auth import auth as auth_blueprint
from .document import document as doc_blueprint
from .sample import sample as sample_blueprint
from .donor import donor as donor_blueprint
from .api import api as api_blueprint
from .patientconsentform import pcf as pcf_blueprint
from .processing import processing as processing_blueprint
from .storage import storage as storage_blueprint


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_object(app_config[os.getenv("FLASK_CONFIG")])
    app.config.from_pyfile("config.py")

    make_versioned(user_cls=None)

    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    migrate = Migrate(app, db)

    app_admin.init_app(app)

    # Load in models here
    from app.auth import models as auth_models
    from app.misc import models as misc_models
    from app.document import models as doc_models
    from app.sample import models as sample_models
    from app.patientconsentform import models as pcf_models
    from app.processing import models as processing_models
    from app.storage import models as storage_models

    app.register_blueprint(misc_blueprint)
    app.register_blueprint(setup_blueprint, url_prefix="/setup")
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(processing_blueprint, url_prefix="/processing")
    app.register_blueprint(doc_blueprint, url_prefix="/documents")
    app.register_blueprint(sample_blueprint, url_prefix="/samples")
    app.register_blueprint(donor_blueprint, url_prefix="/donors")
    app.register_blueprint(api_blueprint, url_prefix="/api")
    app.register_blueprint(pcf_blueprint, url_prefix="/pcf")
    app.register_blueprint(storage_blueprint, url_prefix="/storage")

    from app.admin import add_admin_views

    add_admin_views()

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("misc/404.html"), 404

    return app
