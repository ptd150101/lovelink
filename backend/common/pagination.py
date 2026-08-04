from rest_framework.pagination import CursorPagination as DRFCursorPagination

class CursorPagination(DRFCursorPagination):
    page_size = 24
    ordering = "-created_at"
    cursor_query_param = "cursor"

    def get_ordering(self, request, queryset, view):
        return getattr(view, "pagination_ordering", super().get_ordering(request, queryset, view))
