from flask import Flask
from flask import session
from flask_script import Manager
from flask_sqlalchemy import SQLAlchemy
import redis
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from flask_migrate import Migrate, MigrateCommand

app = Flask(__name__)
class Config(object):
    DEBUG = True

    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1:3306/'
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379
    REIDS_NUM = 1

    SECRET_KEY = 'oychao'

    SESSION_TYPE = 'redis'
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    SESSION_USE_SIGNER = True
    SESSION_PERMANENT = 86400 * 2

app.config.from_object(Config)

manager = Manager(app)
db = SQLAlchemy(app)
Migrate(app, db)
manager.add_command('db', MigrateCommand)
redis_store = redis.StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=Config.REIDS_NUM)
csrf = CSRFProtect(app)
Session(app)


@app.route('/')
def index():
    session['name'] = 'oychao'
    return 'index'


if __name__ == '__main__':
    manager.run()
