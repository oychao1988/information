import datetime
import random

from info import db
from info.models import User
from manage import app


def add_test_users():
    users = []
    now = datetime.datetime.now()
    for num in range(0, 10000):
        try:
            user = User()
            user.mobile = user.nick_name = "1%d%09d" % (random.randint(3, 9), num)
            user.password = ''.join([str(random.randint(0, 10)) for i in range(6)])
            user.last_login = now - datetime.timedelta(seconds=random.randint(0, 2678400))
            users.append(user)
        except Exception as e:
            print(e)
    with app.app_context():
        try:
            db.session.add_all(users)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(e)
    print('OK')
add_test_users()