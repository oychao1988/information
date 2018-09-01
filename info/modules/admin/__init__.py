from flask import Blueprint

admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')

from .views import *

@admin_bp.before_request
def before_request():
    if request.url.endswith(url_for('admin_bp.admin_index')):
        user_id = session.get('user_id')
        is_admin = session.get('is_admin')
        if not user_id or not is_admin:
            return redirect('/')