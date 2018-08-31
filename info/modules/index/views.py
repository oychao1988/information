from flask import current_app, jsonify
from flask import g
from flask import render_template
from flask import request

from info import constants
from info.models import News, Category
from info.utils.common import login_user_info
from info.utils.response_code import RET
from . import index_bp


@index_bp.route('/')
@login_user_info
def index():
    user = g.user
    # 查询新闻点击排行数据
    try:
        news_model_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)
        news_model_list = []
    news_dict_list = []
    for news in news_model_list:
        news_dict_list.append(news.to_dict())

    # 查询分类导航
    try:
        categories = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)

    categories_dict_list = []
    for category in categories if categories else []:
        categories_dict_list.append(category.to_dict())

    data = {
        'user_info': user.to_dict() if user else [],
        'newsClicksList': news_dict_list,
        'categories': categories_dict_list,
    }
    return render_template('index.html', data=data)

@index_bp.route('/news_list')
def get_news_list():
    cid = request.args.get('cid')
    page = request.args.get('page', 1)
    per_page = request.args.get('per_page', constants.HOME_PAGE_MAX_NEWS)

    try:
        cid = int(cid)
        page = int(page)
        per_page = int(per_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    filters = []
    # print('cid=', cid)
    if cid != 1:
        filters.append(News.category_id == cid)
    # print('filters:', filters)

    try:
        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page, per_page, False)
        items = paginate.items
        total_page = paginate.pages
        current_page = paginate.page
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.OK, errmsg='数据库查询新闻列表失败')

    news_dict_list = []
    for news in items:
        news_dict_list.append(news.to_dict())

    data = {
        'newsList': news_dict_list,
        'current_page': current_page,
        'total_page': total_page
           }
    # print('current_page', current_page)
    # print('total_page', total_page)
    # print('news_dict_list:', len(news_dict_list))
    return jsonify(errno=RET.OK, errmsg='查询新闻列表', data=data)

@index_bp.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')
