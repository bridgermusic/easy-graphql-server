import unittest

from . import db


class BaseSqlalchemyTest(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        db.init()

    def get_or_create_user(self, username):
        return
        # data = {'username': username}
        # if 'staff' in username:
        #     data['is_staff'] = True
        # if 'admin' in username:
        #     data['is_superuser'] = True
        # user_model = django.contrib.auth.get_user_model()
        # try:
        #     user = user_model.objects.get(username = username)
        # except user_model.DoesNotExist:
        #     user, created = django.contrib.auth.get_user_model().objects.get_or_create(**data)
        #     user.set_password(settings.DEFAULT_USER_PASSWORD)
        #     user.save()
        # return user
