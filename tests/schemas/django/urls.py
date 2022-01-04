from django.urls import path

from .graphql import schema


urlpatterns = [
    path('graphql', schema.as_django_view()),
]
