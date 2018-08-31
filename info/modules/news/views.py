from flask import abort, jsonify
from flask import current_app
from flask import g
from flask import redirect
from flask import render_template
from flask import request

from info import constants, db
from info.models import News, tb_user_collection
from info.utils.common import login_user_info
from info.utils.response_code import RET
from . import news_bp

@news_bp.route('/<int:news_id>')
@login_user_info
def detail(news_id):
    user = g.user

    # 查询新闻详情
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
    if not news:
        return abort(404)
    news.clicks += 1
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)

    # 查询新闻点击排行数据
    try:
        news_model_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)
        news_model_list = []
    news_dict_list = []
    for news_rank in news_model_list:
        news_dict_list.append(news_rank.to_dict())

    is_collected = False
    if user and (news in user.collection_news):
        is_collected = True

    data = {
        'user_info': user.to_dict() if user else [],
        'newsClicksList': news_dict_list,
        'news': news.to_dict(),
        'is_collected': is_collected,
    }
    return render_template('news/detail.html', data=data)

@news_bp.route('/news_collect', methods=['POST'])
@login_user_info
def news_collect():
    # 获取参数
    params_dict = request.json
    news_id = params_dict.get('news_id')
    action = params_dict.get('action')
    user = g.user

    # 检查用户是否登录
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')

    # 参数校验
    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不足')
    if not action in ['collect', 'cancel_collect']:
        return jsonify(errno=RET.PARAMERR, errmsg='参数格式错误')

    # 检查新闻是否存在
    news = None
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询新闻失败')
    if not news:
        return jsonify(errno=RET.NODATA, errmsg='该新闻不存在')

    if action == 'collect':
        user.collection_news.append(news)
    else:
        user.collection_news.remove(news)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库收藏操作失败')
    #返回值处理
    return jsonify(errno=RET.OK, errmsg='操作成功')