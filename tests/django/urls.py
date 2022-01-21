from django.urls import path

from .schema1 import schema


urlpatterns = [
    path('graphql', schema.as_django_view()),
]
