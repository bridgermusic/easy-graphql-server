"""
    Definition of `DjangoSchemaView` class
"""

from django.http import HttpResponse, JsonResponse
from ._schema_view import SchemaView


class DjangoSchemaView(SchemaView):

    """
        Django schema view. Used when calling `Schema.as_django_view()`.
    """

    def view(self, request):
        """
            Django view to compute GraphQL request
        """
        # extract user
        if request.user and request.user.is_authenticated and not request.user.is_anonymous:
            authenticated_user = request.user
        else:
            authenticated_user = None
        # compute result
        result = self.compute_response(
            method = request.method,
            headers = request.headers,
            body = request.body,
            query = dict(request.GET.items()),
            authenticated_user = authenticated_user,
        )
        # return response
        if isinstance(result, str):
            return HttpResponse(result)
        return JsonResponse(result[0], status=result[1])
