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

    def __init__(self, *args, **kwargs):
        self.compute_user = kwargs.pop('compute_user', True)
        super().__init__(*args, **kwargs)

    def view(self, request):
        """
            Django view to compute GraphQL request
        """
        # compute user when requested and not present
        authenticated_user = request.user
        if self.compute_user:
            if not authenticated_user or not authenticated_user.is_authenticated or authenticated_user.is_anonymous:
                try:
                    authenticated_user = django.contrib.auth.authenticate(request)
                except Exception: # pylint: disable=broad-except
                    pass
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
