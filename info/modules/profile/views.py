from flask import current_app
from flask import g, jsonify
from flask import render_template
from flask import request
from flask import session
from flask import url_for

from info import constants
from info import db
from info.models import News, Category
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

@profile_bp.route('/pass_info', methods=['GET', 'POST'])
@login_user_info
def pass_info():
    user = g.user
    # 检查用户是否登录
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')

    if request.method == 'GET':
        return render_template('user/user_pass_info.html', data={'user_info': user.to_dict()})

    # 获取参数
    params_dict = request.json
    old_password = params_dict.get('old_password')
    new_password_1 = params_dict.get('new_password_1')
    new_password_2 = params_dict.get('new_password_2')

    # 参数校验
    if not all([old_password, new_password_1, new_password_2]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不足')
    if new_password_1 != new_password_2:
        return jsonify(errno=RET.PARAMERR, errmsg='新密码两次输入不一致')
    if not user.check_passowrd(old_password):
        return jsonify(errno=RET.PARAMERR, errmsg='旧密码输入错误')

    user.password = new_password_1
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库修改密码失败')

    return jsonify(errno=RET.OK, errmsg='修改密码成功', data={'user_info': user.to_dict()})

@profile_bp.route('/collection')
@login_user_info
def user_collection():
    user = g.user
    # 检查用户是否登录
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
    # 获取参数
    p = request.args.get('p', 1)

    # 参数校验
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1

    # 查询收藏新闻列表
    try:
        paginate = user.collection_news.paginate(p, constants.USER_COLLECTION_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)

    # 组织返回值
    news_list = paginate.items
    total_page = paginate.pages
    current_page = paginate.page

    data = {
        'collections': news_list,
        'total_page': total_page,
        'current_page': current_page
    }

    return render_template('user/user_collection.html', data=data)

@profile_bp.route('/news_release', methods=['GET', 'POST'])
@login_user_info
def news_release():
    user = g.user
    # 检查用户是否登录
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')

    if request.method == 'GET':
        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
        category_dict_list = []
        for category in categories if categories else []:
            category_dict_list.append(category.to_dict())
        category_dict_list.pop(0)
        return render_template('user/user_news_release.html', data={'categories': category_dict_list})

    # 获取参数
    title = request.form.get('title')
    category_id = request.form.get('category_id')
    digest = request.form.get('digest')
    content = request.form.get('content')
    index_image = request.files.get('index_image')
    source = '个人发布'
    print(request.form)
    # 校验参数
    if not all([title, category_id, digest, content, index_image]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不足')
    try:
        category_id = int(category_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='新闻类别格式错误')

    index_image = index_image.read()
    # 保存图片到七牛云
    try:
        index_image_url = qiniu_image_store(index_image)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='七牛云上传图片失败')

    # 创建新闻模型
    news = News()
    news.title = title
    news.digest = digest
    news.category_id = category_id
    news.index_image_url = constants.QINIU_DOMIN_PREFIX + index_image_url
    news.content = content
    news.status = 0
    news.source = source
    # 买什么涨什么
    try:
        db.session.add(news)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存新闻到数据库失败')

    return jsonify(errno=RET.OK, errmsg='新闻发布成功')