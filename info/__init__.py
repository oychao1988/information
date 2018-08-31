import logging
from logging.handlers import RotatingFileHandler

import redis
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_session import Session
from flask import Flask

from config import config
from info.utils.common import do_index_class


db = SQLAlchemy()
redis_store = None

def create_log(config_name):
    # 设置日志的记录等级
    logging.basicConfig(level=config[config_name].LOG_LEVEL)  # 调试debug级
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)
    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


def create_app(config_name):
    create_log(config_name)
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    db.init_app(app)

    global redis_store
    redis_store = redis.StrictRedis(host=config[config_name].REDIS_HOST,
                                    port=config[config_name].REDIS_PORT,
                                    db=config[config_name].REIDS_NUM,
                                    decode_responses=True)
    csrf = CSRFProtect(app)

    @app.after_request
    def set_csrf_token(response):
        csrf_token = generate_csrf()
        response.set_cookie('csrf_token', csrf_token)
        return response

    app.add_template_filter(do_index_class, 'do_index_class')
    Session(app)

    from info.modules.index.views import index_bp
    app.register_blueprint(index_bp)

    from info.modules.passport.views import passport_bp
    app.register_blueprint(passport_bp)


    return app



