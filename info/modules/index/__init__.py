from flask import Blueprint

index_bp = Blueprint('index_bp', __name__)


from .views import index_bp