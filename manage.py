from flask import session
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import create_app, db


app = create_app('development')
manager = Manager(app)
Migrate(app, db)
manager.add_command('db', MigrateCommand)


@app.route('/')
def index():
    session['name'] = 'oychao'
    return 'index'


if __name__ == '__main__':
    manager.run()
