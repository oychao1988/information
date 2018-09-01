from flask import current_app
from flask import g, jsonify
from flask import render_template
from flask import request
from flask import session
from flask import url_for

from info import db
from info.utlis.common import login_user_info
from info.utlis.image_storage import qiniu_image_store
from info.utlis.response_code import RET
from . import profile_bp

@profile_bp.route('')
@login_user_info
def user_info():
    user = g.user
    data = {
        'user_info': user.to_dict() if user else []
    }
    return render_template('user/user.html', data=data)

@profile_bp.route('/base_info', methods=['GET', 'POST'])
@login_user_info
def base_info():
    user = g.user
    # 检查用户是否登录
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')

    if request.method == 'GET':
        return render_template('user/user_base_info.html', data={'user_info': user.to_dict()})

    # 获取参数
    params_dict = request.json
    signature = params_dict.get('signature')
    nick_name = params_dict.get('nick_name')
    gender = params_dict.get('gender')
    print(params_dict)
    if not signature and not nick_name and not gender:
        return jsonify(errno=RET.PARAMERR, errmsg='参数不足')

    if signature:
        user.signature = signature
    if nick_name:
        user.nick_name = nick_name
    if gender in ['MAN', 'WOMAN']:
        user.gender = gender
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库修改用户资料失败')
    session['nick_name'] = user.nick_name
    return jsonify(errno=RET.OK, errmsg='修改用户资料成功', data={'user_info': user.to_dict()})


@profile_bp.route('/pic_info', methods=['GET', 'POST'])
@login_user_info
def pic_info():
    user = g.user
    # 检查用户是否登录
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')

    if request.method == 'GET':
        return render_template('user/user_pic_info.html', data={'user_info': user.to_dict()})

    pic_data = request.files.get('avatar').read()
    if not pic_data:
        return jsonify(errno=RET.PARAMERR, errmsg='图片数据为空')
    try:
        image_name = qiniu_image_store(pic_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='七牛云上传图片失败')
    if not image_name:
        return jsonify(errno=RET.PARAMERR, errmsg='图片数据为空')
    user.avatar_url = image_name
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库保存图片数据失败')
    return jsonify(errno=RET.OK, errmsg='上传图片成功', data={'user_info': user.to_dict()})