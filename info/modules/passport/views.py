from flask import abort
from flask import make_response
from flask import request
from . import passport_bp
from info import redis_store
from info.utils.captcha.captcha import captcha
from info import constants

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