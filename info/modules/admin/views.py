import datetime
import time
from flask import current_app, jsonify
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for

from info import constants
from info.models import User
from info.utlis.common import login_user_info
from info.utlis.response_code import RET
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
            user_id = session.get('user_id')
            is_admin = session.get('is_admin')

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

@admin_bp.route('/index', methods=['GET', 'POST'])
@login_user_info
def admin_index():
    user = g.user
    return render_template('admin/index.html', data={'user_info': user.to_dict() if user else []})

@admin_bp.route('/user_count')
@login_user_info
def user_count():
    total_count = 0
    # 查询总人数
    try:
        total_count = User.query.filter(User.is_admin == False).count()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询总人数失败')

    #　查询月新增
    month_count = 0
    now = time.localtime()
    month_begin = '%d-%02d-01' % (now.tm_year, now.tm_mon)
    month_begin_date = datetime.datetime.strptime(month_begin, '%Y-%m-%d')
    try:
        month_count = User.query.filter(User.is_admin==False, User.create_time>=month_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询月新增人数失败')
    # 查询日新增
    day_count = 0
    day_begin = '%d-%02d-%02d' % (now.tm_year, now.tm_mon, now.tm_mday)
    day_begin_date = datetime.datetime.strptime(day_begin, '%Y-%m-%d')
    try:
        day_count = User.query.filter(User.is_admin == False, User.create_time >= day_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询日新增人数失败')

    # 查询图表信息
    # 获取到当天00:00:00时间

    now_date = datetime.datetime.now()
    # 定义空数组，保存数据
    active_date = []
    active_count = []

    # 依次添加数据，再反转
    for i in range(0, 31):
        begin_date = now_date - datetime.timedelta(days=i)
        end_date = begin_date + datetime.timedelta(1)
        active_date.append(begin_date.strftime('%Y-%m-%d'))
        count = 0
        try:
            count = User.query.filter(User.is_admin == False, User.last_login >= begin_date,
                                      User.last_login < end_date).count()
        except Exception as e:
            current_app.logger.error(e)
        active_count.append(count)

    active_date.reverse()
    active_count.reverse()

    data = {
        'total_count': total_count,
        'month_count': month_count,
        'day_count': day_count,
        'active_date': active_date,
        'active_count': active_count
    }
    return render_template('admin/user_count.html', data=data)

@admin_bp.route('/user_list')
@login_user_info
def user_list():
    user = g.user
    if not user:
        return render_template('admin/user_list.html', data=None)
    p = request.args.get('p', 1)

    if not p:
        return render_template('admin/user_list.html', data=None)

    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        return render_template('admin/user_list.html', data=None)

    paginate = None
    try:
        paginate = User.query.filter(User.is_admin==False).paginate(p, constants.ADMIN_USER_PAGE_MAX_COUNT, False)
    except Exception as e:
        current_app.logger.error(e)

    user_list = []
    current_page = 1
    total_page = 1

    if paginate:
        user_list = paginate.items
        current_page = paginate.page
        total_page = paginate.pages

    data = {
        'current_page': current_page,
        'total_page': total_page,
        'user_list': user_list
    }
    return render_template('admin/user_list.html', data=data)