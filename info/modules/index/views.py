from flask import session
from . import index_bp


@index_bp.route('/')
def index():
    session['name'] = 'oychao'
    return 'index'