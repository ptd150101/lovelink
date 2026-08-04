import logging
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

def exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is not None:
        return response
    logger.exception("Unhandled API exception", exc_info=exc)
    return Response({"detail": "Đã xảy ra lỗi. Vui lòng thử lại.", "code": "internal_error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
