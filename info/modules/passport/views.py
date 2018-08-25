import re
from flask import abort, jsonify
from flask import current_app
from flask import make_response
from flask import request

from info.utils.response_code import RET
from . import passport_bp
from info import redis_store
from info.utils.captcha.captcha import captcha
from info import constants
from info.models import User
from info.lib.yuntongxun.sms import CCP
import random

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

    result = CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES], 1)
    if result == 0:
        redis_store.set('SMS_%s' % mobile, sms_code, ex=constants.SMS_CODE_REDIS_EXPIRES)
    else:
        return jsonify(errno=RET.THIRDERR, errmsg='发送短信验证码失败')
    return jsonify(errno=RET.OK, errmsg='发送短信验证成功')