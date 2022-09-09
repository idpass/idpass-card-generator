from collections import OrderedDict
from typing import Any

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.routers import APIRootView
from rest_framework_extensions.routers import (
    ExtendedDefaultRouter,
    ExtendedSimpleRouter,
)


class ExtraPathRouter:
    """A mixin that supports registering extra API views to a router."""

    def __init__(self, *args, **kwargs):
        self.extra_paths = []
        super().__init__(*args, **kwargs)

    def add_path(self, path):
        self.extra_paths.append(path)

    def get_urls(self):
        return super().get_urls() + self.extra_paths


class ExtraPathAPIRootView(APIRootView):
    extra_paths = None

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Add extra URLs to the response of the root API view."""
        response = super().get(request, *args, **kwargs)
        namespace = self.request.resolver_match.namespace
        if self.extra_paths:
            for extra_path in self.extra_paths:
                name = extra_path.name
                url_name = name
                if namespace:
                    url_name = namespace + ":" + name
                response.data[name] = reverse(
                    url_name,
                    args=args,
                    kwargs=kwargs,
                    request=request,
                    format=kwargs.get("format", None),
                )
        return response


class DefaultRouter(ExtraPathRouter, ExtendedDefaultRouter):
    """A default router that supports adding extra API views to its namespace."""

    APIRootView = ExtraPathAPIRootView

    def get_api_root_view(self, api_urls=None):
        api_root_dict = OrderedDict()
        list_name = self.routes[0].name
        for prefix, viewset, basename in self.registry:
            api_root_dict[prefix] = list_name.format(basename=basename)

        return self.APIRootView.as_view(
            api_root_dict=api_root_dict, extra_paths=self.extra_paths
        )


class SimpleRouter(ExtraPathRouter, ExtendedSimpleRouter):
    pass
