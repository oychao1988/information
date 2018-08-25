from flask import Blueprint

passport_bp = Blueprint('passport_bp', __name__, url_prefix='/passport')

from .views import *