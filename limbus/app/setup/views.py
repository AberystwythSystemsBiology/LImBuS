from flask import redirect, render_template, url_for

from ..auth.models import User

from . import setup
from .. import db
from ..auth.forms import RegistrationForm

@setup.route("/")
def index():
    return render_template("setup/index.html")
