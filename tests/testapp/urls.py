from django.urls import path

from ..methods.schema1 import schema as methods_schema
from . import views
from .schema1 import schema as orm_schema

urlpatterns = [
    path("graphql", orm_schema.as_django_view()),
    path("graphql-methods", methods_schema.as_django_view()),
    path("api/v1", views.TestView.as_view(), name="reverse_test_view"),
]
