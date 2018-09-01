import functools
from flask import g
from flask import session


def do_index_class(index):
    if index == 1:
        return 'first'
    elif index == 2:
        return 'second'
    elif index == 3:
        return 'third'
    else:
        return ''

def login_user_info(view_func):
    @functools.wraps(view_func)
    def wrapper(*args, **kwargs):
        user_id = session.get('user_id')
        user = None
        if user_id:
            from info.models import User
            user = User.query.get(user_id)
        g.user = user
        return view_func(*args, **kwargs)
    return wrapper
