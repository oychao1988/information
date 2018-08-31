from flask import Blueprint

news_bp = Blueprint('news_bp', __name__, url_prefix='/news')

from .views import *