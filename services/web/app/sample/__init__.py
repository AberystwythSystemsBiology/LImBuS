from flask import Blueprint

sample = Blueprint("sample", __name__)

from .routes import *
from .api import *