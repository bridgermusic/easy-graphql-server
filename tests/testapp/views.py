from django.http import HttpResponse
from django.views.generic.base import View


class TestView(View):
    # pylint: disable = W0613
    def get(self, request, **kwargs):
        return HttpResponse(
            "Implementation not found", content_type="text/plain", status=400
        )
