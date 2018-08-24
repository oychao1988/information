from flask import Flask
from flask import session
from flask_script import Manager
from flask_sqlalchemy import SQLAlchemy
import redis
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from flask_migrate import Migrate, MigrateCommand
from config import config
app = Flask(__name__)


app.config.from_object(config['develepment'])

manager = Manager(app)
db = SQLAlchemy(app)
Migrate(app, db)
manager.add_command('db', MigrateCommand)
redis_store = redis.StrictRedis(host=config['develepment'].REDIS_HOST, port=config['develepment'].REDIS_PORT, db=config['develepment'].REIDS_NUM)
csrf = CSRFProtect(app)
Session(app)


@app.route('/')
def index():
    session['name'] = 'oychao'
    return 'index'


if __name__ == '__main__':
    manager.run()
