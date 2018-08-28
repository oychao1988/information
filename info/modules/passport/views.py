import datetime
import re
from flask import abort, jsonify
from flask import current_app
from flask import make_response
from flask import request
from flask import session

from info.utils.response_code import RET
from . import passport_bp
from info import redis_store
from info.utils.captcha.captcha import captcha
from info import constants
from info.models import User
from info.lib.yuntongxun.sms import CCP
import random
from info import db

@passport_bp.route('/image_code')
def get_imagecode():
    # 获取编码
    imageCodeId = request.args.get('imageCodeId')
    # 校验编码
    if not imageCodeId:
        abort(404)
    # 逻辑处理.
    name, text, image = captcha.generate_captcha()
    redis_store.set('imageCodeId_%s' % imageCodeId, text, ex=constants.IMAGE_CODE_REDIS_EXPIRES)
    #  返回图片
    response = make_response(image)
    response.headers['Content-Type'] = 'image/jpeg'
    return response

@passport_bp.route('/sms_code', methods=['POST'])
def send_sms():
    param_dict = request.json
    mobile = param_dict.get('mobile')
    image_code_id = param_dict.get('image_code_id')
    image_code = param_dict.get('image_code')
    if not all([mobile, image_code_id, image_code]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不足')
    if not re.match(r'^1[345678][0-9]{9}$', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='手机号格式错误')
    print('params =', param_dict)
    try:
        real_image_code = redis_store.get('imageCodeId_%s' % image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询失败')

    if real_image_code:
        try:
            redis_store.delete('imageCodeId_%s' % image_code_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='数据库查询失败')
    else:
        return jsonify(errno=RET.NODATA, errmsg='验证码已过期')

    if real_image_code.lower() != image_code.lower():
        return jsonify(errno=RET.DATAERR, errmsg='验证码错误')

    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询失败')

    if user:
        return jsonify(errno=RET.DATAEXIST, errmsg='手机号已注册')

    sms_code = random.randint(0, 999999)
    sms_code = '%06d' % sms_code
    print('sms_code =', sms_code)

    try:
        redis_store.set('SMS_%s' % mobile, sms_code, ex=constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库添加短信验证码失败')

    # result = CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES], 1)
    # if result == 0:
    #     try:
    #         redis_store.set('SMS_%s' % mobile, sms_code, ex=constants.SMS_CODE_REDIS_EXPIRES)
    #     except Exception as e:
    #         current_app.logger.error(e)
    #         return jsonify(errno=RET.DBERR, errmsg='数据库添加短信验证码失败')
    # else:
    #     return jsonify(errno=RET.THIRDERR, errmsg='发送短信验证码失败')
    return jsonify(errno=RET.OK, errmsg='发送短信验证成功')

@passport_bp.route('/register', methods=['POST'])
def register():
    # 获取参数
    param_dict = request.json
    mobile = param_dict.get('mobile')
    sms_code = param_dict.get('smsCode')
    password = param_dict.get('password')
    # 验证参数
    if not all([mobile, sms_code, password]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不足')
    if not re.match(r'^1[3456789][0-9]{9}$', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='手机号码格式错误')
    # 逻辑处理
    try:
        real_sms_code = redis_store.get('SMS_%s' % mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询短信验证码失败')
    if not real_sms_code:
        return jsonify(errno=RET.NODATA, errmsg='短信验证码已过期')
    if real_sms_code != sms_code:
        return jsonify(errno=RET.DATAERR, errmsg='短信验证码错误')
    try:
        redis_store.delete('SMS_%s' % mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库删除短信验证码失败')
    user = User()
    user.mobile = mobile
    user.nick_name = mobile
    user.last_login = datetime.datetime.now()
    user.password = password
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库添加用户失败')
    session['user_id'] = user.id
    session['mobile'] = user.mobile
    session['nick_name'] = user.nick_name
    # 返回值处理
    return jsonify(errno=RET.OK, errmsg='注册成功')

@passport_bp.route('/login', methods=['POST'])
def login():
    # 获取参数
    params_dict = request.json
    mobile = params_dict.get('mobile')
    password = params_dict.get('password')
    # 验证参数
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不足')
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询用户出错')
    if not user:
        return jsonify(errno=RET.NODATA, errmsg='用户不存在')
    if not user.check_passowrd(password):
        return jsonify(errno=RET.DATAERR, errmsg='密码错误')
    user.last_login = datetime.datetime.now()
    session['user_id'] = user.id
    session['mobile'] = user.mobile
    session['nick_name'] = user.nick_name
    # 逻辑处理
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库数据提交失败')
    # 返回值处理
    return jsonify(errno=RET.OK, errmsg='登录成功')

@passport_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id')
    session.pop('mobile')
    session.pop('nick_name')
    return jsonify(errno=RET.OK, errmsg='登出成功')