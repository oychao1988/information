from flask import abort, jsonify
from flask import current_app
from flask import g
from flask import redirect
from flask import render_template
from flask import request

from info import constants, db
from info.models import News, tb_user_collection, Comment, CommentLike, User
from info.utlis.common import login_user_info
from info.utlis.response_code import RET
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

    # 查询关注信息
    is_followed = False
    followed_list = []
    if user:
        try:
            followed_list = user.followed.all()
        except Exception as e:
            current_app.logger.error(e)
        if news.user in followed_list:
            is_followed = True
    # print('followed_list =', followed_list)
    # print('is_followed =', is_followed)

    # 查询评论信息
    comments = None
    try:
        comments = Comment.query.filter(Comment.news_id==news_id).order_by(Comment.create_time.desc())
    except Exception as e:
        current_app.logger.error(e)
    comment_dict_list = []
    for comment in comments if comments else []:
        comment_dict_list.append(comment.to_dict())


    if user:
        # 查询点赞信息
        commentLike_id = []
        # 在这条新闻内的评论
        comment_id = [comment.id for comment in comments]
        # 这个用户的点赞
        commentLike = CommentLike.query.filter(CommentLike.comment_id.in_(comment_id),
                                           CommentLike.user_id==user.id).all()
        commentLike_id = [liked.comment_id for liked in commentLike if commentLike]

        # 将点赞信息附加到评论字典中
        for comment in comment_dict_list:
            if comment['id'] in commentLike_id:
                comment['is_liked'] = True
    data = {
        'user_info': user.to_dict() if user else [],
        'newsClicksList': news_dict_list,
        'news': news.to_dict(),
        'is_collected': is_collected,
        'comments': comment_dict_list,
        'comment_count': len(comment_dict_list),
        'is_followed': is_followed
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

    # 判断是否收藏
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


@news_bp.route('/news_comment', methods=['POST'])
@login_user_info
def news_comment():
    user = g.user
    # 获取参数
    params_dict = request.json
    news_id = params_dict.get('news_id')
    content = params_dict.get('comment')
    parent_id = params_dict.get('parent_id')
    # print(params_dict)
    # 验证用户是否登录
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')

    # 参数校验
    if not all([news_id, content]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不足')

    # 检查新闻是否存在
    news = None
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询新闻失败')
    if not news:
        return jsonify(errno=RET.NODATA, errmsg='该新闻不存在')

    # 添加评论
    comment = Comment()
    comment.user_id = user.id
    comment.news_id = news.id
    comment.content = content
    if parent_id:
        comment.parent_id = parent_id
    try:
        db.session.add(comment)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库添加评论失败')

    # 组织返回数据
    data = comment.to_dict()
    data['user'] = user.to_dict()
    return jsonify(errno=RET.OK, errmsg='评论成功', data=data)

@news_bp.route('/comment_like', methods=['POST'])
@login_user_info
def comment_like():
    params_dict = request.json
    comment_id = params_dict.get('comment_id')
    action = params_dict.get('action')
    user = g.user

    # 检查用户是否登录
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')

    # 检查评论是否存在
    comment = None
    try:
        comment = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询评论失败')
    if not comment:
        return jsonify(errno=RET.NODATA, errmsg='该评论不存在')

    # 参数校验
    if not all([comment_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不足')
    if action not in ['like', 'unlike']:
        return jsonify(errno=RET.PARAMERR, errmsg='参数格式错误')

    # 点赞与取消点赞操作
    if action == 'like':
        commentLike = CommentLike()
        commentLike.comment_id = comment_id
        commentLike.user_id = user.id
        comment.like_count += 1
        db.session.add(commentLike)
    else:
        commentLike = CommentLike.query.filter(CommentLike.user_id==user.id,
                                               CommentLike.comment_id==comment_id).first()
        db.session.delete(commentLike)
        comment.like_count -= 1

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库操作点赞数据失败')

    return jsonify(errno=RET.OK, errmsg='操作成功')


@news_bp.route('/follow_user', methods=['POST'])
@login_user_info
def follow_user():
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
    # 获取参数
    params_dict = request.json
    author_id = params_dict.get('author_id')
    action = params_dict.get('action')
    # 参数校验
    if not all([author_id, action]):
        return  jsonify(errno=RET.PARAMERR, errmsg='参数不足')
    if action not in ['follow', 'unfollow']:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    try:
        author = User.query.get(author_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询新闻作者失败')
    if not author:
        return jsonify(errno=RET.NODATA, errmsg='该作者不存在')

    followed_list = []
    try:
        followed_list = user.followed.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询关注信息失败')

    is_followed = False
    if action == 'follow':
        if user not in followed_list:
            user.followed.append(author)
            is_followed = True
    else:
        user.followed.remove(author)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库修改关注信息失败')

    data = {
        'is_followed': is_followed,
    }
    return jsonify(errno=RET.OK, errmsg='操作成功', data=data)
