from flask import current_app
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for

from info.models import User
from info.utlis.common import login_user_info
from . import admin_bp

@admin_bp.route('/login', methods=['GET', 'POST'])
@login_user_info
def admin_login():
    # 进入登录页面
    if request.method == 'GET':
        user = g.user
        user_id = None
        is_admin = None

        if user:
            user_id = session['user_id']
            is_admin = session['is_admin']

        if user_id and is_admin:
            return redirect(url_for('admin_bp.admin_index'))
        return render_template('admin/login.html')

    # 提交登录表单
    username = request.form.get('username')
    password = request.form.get('password')

    #　参数校验
    if not all([username, password]):
        return render_template('admin/login.html', errmsg='参数不足')
    try:
        user = User.query.filter(User.mobile==username).first()
    except Exception as e:
        current_app.logger.error(e)
        return render_template('admin/login.html', errmsg='数据库查询失败')

    if not user:
        return render_template('admin/login.html', errmsg='用户不存在')
    if not user.check_passowrd(password):
        return render_template('admin/login.html', errmsg='密码错误')
    if not user.is_admin:
        return render_template('admin/login.html', errmsg='权限错误')

    # 记录登录状态
    session['user_id'] = user.id
    session['mobile'] = user.mobile
    session['nick_name'] = user.nick_name
    session['is_admin'] = True
    return redirect(url_for('admin_bp.admin_index'))

@admin_bp.route('/index')
def admin_index():
    return render_template('admin/index.html')