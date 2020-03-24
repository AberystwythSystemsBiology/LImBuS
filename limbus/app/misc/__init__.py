from flask import Blueprint, render_template
from flask_login import current_user

misc = Blueprint("misc", __name__)

from .models import BiobankInformation

from .. import db


@misc.route("/")
def index() -> str:
    if current_user.is_authenticated:
        biobank = db.session.query(BiobankInformation).first()
        return render_template("misc/panel.html", biobank=biobank)
    else:
        return render_template("misc/index.html")


@misc.route("/license")
def license() -> str:
    return render_template("misc/license.html")


@misc.route("/team")
def team() -> str:
    return render_template("misc/team.html")
