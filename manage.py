from flask import current_app
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import create_app, db
from info.models import User

app = create_app('development')
manager = Manager(app)
Migrate(app, db)
manager.add_command('db', MigrateCommand)

@manager.option('-n', '-name', dest='name')
@manager.option('-p', '-password', dest='password')
def createSuperUser(name, password):
    if not all([name, password]):
        return '参数不足'
    user = User()
    user.nick_name = name
    user.is_admin = True
    user.password = password
    user.mobile = name

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        print('数据库创建管理员失败')
    print('管理员创建成功')

if __name__ == '__main__':
    # print(app.url_map)
    manager.run()
