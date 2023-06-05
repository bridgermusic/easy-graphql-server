from flask_login import UserMixin

users = []


class User(UserMixin):
    def __init__(self, id, username, is_staff=False, is_superuser=False):
        self.id = id
        self.username = username
        self.is_staff = is_staff
        self.is_superuser = is_superuser


def add_user(**kwargs):
    user = User(len(users) + 1, **kwargs)
    users.append(user)
    return user


def get_user(username):
    for user in users:
        if user.username == username:
            return user
