from flask import abort
from flask import current_app
from flask import g
from flask import redirect
from flask import render_template

from info import constants, db
from info.models import News
from info.utils.common import login_user_info
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

    data = {
        'user': user.to_dict() if user else [],
        'newsClicksList': news_dict_list,
        'news': news.to_dict(),
    }
    return render_template('news/detail.html', data=data)