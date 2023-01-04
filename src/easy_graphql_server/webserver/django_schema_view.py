"""
    Definition of `DjangoSchemaView` class
"""

from django.http import HttpResponse, JsonResponse
import django.contrib.auth
from ._schema_view import SchemaView


class DjangoSchemaView(SchemaView):

    """
        Django schema view. Used when calling `Schema.as_django_view()`.
    """

    def view(self, request):
        """
            Django view to compute GraphQL request
        """
        # compute result
        result = self.compute_response(
            method = request.method,
            headers = request.headers,
            body = request.body,
            query = dict(request.GET.items()),
            authenticated_user = request.user,
        )
        # return response
        if isinstance(result, str):
            return HttpResponse(result)
        return JsonResponse(result[0], status=result[1])
