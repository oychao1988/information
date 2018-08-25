from flask import current_app
from flask import render_template
from flask import session
from . import index_bp


@index_bp.route('/')
def index():
    session['name'] = 'oychao'
    return render_template('index.html')

@index_bp.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('/news/favicon.ico')