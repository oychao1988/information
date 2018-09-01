from flask import Blueprint

profile_bp = Blueprint('profile_bp', __name__, url_prefix='/user')

from .views import *