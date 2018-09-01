from flask import g
from flask import render_template

from info.utils.common import login_user_info
from . import profile_bp

@profile_bp.route('/info')
@login_user_info
def user_info():
    user = g.user
    data = {
        'user': user.to_dict() if user else []
    }
    return render_template('user/user.html', data=data)