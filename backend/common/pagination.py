from rest_framework.pagination import CursorPagination as DRFCursorPagination

class CursorPagination(DRFCursorPagination):
    page_size = 24
    ordering = "-created_at"
    cursor_query_param = "cursor"
