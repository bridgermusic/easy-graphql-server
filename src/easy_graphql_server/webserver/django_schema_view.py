import json
from django.http import JsonResponse
from ._schema_view import SchemaView


class DjangoSchemaView(SchemaView):

    def view(self, request):
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
            query = request.GET,
            authenticated_user = authenticated_user,
        )
        # return response
        return JsonResponse(result[0], status=result[1])
