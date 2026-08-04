from .context import request_context

class RequestAuditContextMiddleware:
    def __init__(self, get_response): self.get_response = get_response
    def __call__(self, request):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
        token = request_context.set({
            "ip_address": forwarded or request.META.get("REMOTE_ADDR"),
            "user_agent": request.META.get("HTTP_USER_AGENT", "")[:1000],
        })
        try: return self.get_response(request)
        finally: request_context.reset(token)
