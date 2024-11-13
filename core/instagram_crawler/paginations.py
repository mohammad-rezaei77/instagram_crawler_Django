from urllib.parse import urlparse, urlunparse

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class DefaultPagination(PageNumberPagination):
    page_size_query_param = "pagesize"
    default_page_size = 50  # تعیین مقدار پیش‌فرض

    def get_page_size(self, request):
        page_size = super().get_page_size(request)
        return page_size if page_size else self.default_page_size

    def get_next_link(self):
        if not self.page.has_next():
            return None
        url_parts = list(urlparse(super().get_next_link()))
        url_parts[0] = "https"  # Set the scheme to https
        return urlunparse(url_parts)

    def get_previous_link(self):
        if not self.page.has_previous():
            return None
        url_parts = list(urlparse(super().get_previous_link()))
        url_parts[0] = "https"  # Set the scheme to https
        return urlunparse(url_parts)

    def get_paginated_response(self, data):

        return Response(
            {
                "links": {
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                },
                "total_items": self.page.paginator.count,
                "total_pages": self.page.paginator.num_pages,
                "current_page": self.page.number,
                "page_size": self.request.query_params.get(self.page_size_query_param),
                "results": data,
            }
        )
