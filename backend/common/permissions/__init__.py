from rest_framework.permissions import BasePermission

class IsActiveAuthenticated(BasePermission):
    message = "Tài khoản không có quyền truy cập."
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.status == "active" and user.is_active)

class IsReviewer(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.has_perm("verification.review_verificationrequest"))

class IsModerator(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.has_perm("moderation.review_report"))
