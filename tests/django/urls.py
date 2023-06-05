from django.urls import path

from ..methods.schema1 import schema as methods_schema
from .schema1 import schema as orm_schema

urlpatterns = [
    path("graphql", orm_schema.as_django_view()),
    path("graphql-methods", methods_schema.as_django_view()),
]
