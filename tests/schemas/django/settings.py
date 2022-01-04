from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = 1

DATABASES = {
  'default': {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': ':memory:',
  }
}

INSTALLED_APPS = [
    'tests.schemas.django',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
]

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
]

ROOT_URLCONF = 'tests.schemas.django.urls'

SECRET_KEY = 'SecretKeySoThatTestsCanBePerformedOnHttpRequests'
