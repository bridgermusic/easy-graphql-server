"""
    Settings for Django test application used to ensure compatibility
    with ``easy_graphql_server``.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = 1

AUTH_USER_MODEL = "testapp.Person"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

INSTALLED_APPS = [
    "tests.testapp.apps.TestAppConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
]

ROOT_URLCONF = "tests.testapp.urls"

SECRET_KEY = "SecretKeySoThatTestsCanBePerformedOnHttpRequests"

DEFAULT_USER_PASSWORD = "ABC123456xyz!"

PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)
