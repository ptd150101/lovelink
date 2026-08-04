from datetime import timedelta
from django.conf import settings
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.contrib.sessions.models import Session
from django.core import signing
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from common.permissions import IsActiveAuthenticated
from common.throttles import AuthRateThrottle
from apps.audit.services import audit
from .emails import send_password_reset_email, send_verification_email
from .models import User, UserSession, UserPreference
from .serializers import LoginSerializer, PasswordResetConfirmSerializer, RegisterSerializer, UserSerializer, UserPreferenceSerializer, EmailChangeSerializer
from .tokens import load_email_token, load_password_token


def _client_ip(request): return request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", "")).split(",")[0].strip()

def _track_session(request, user):
    if not request.session.session_key: request.session.save()
    UserSession.objects.update_or_create(session_key=request.session.session_key, defaults={"user":user,"user_agent":request.META.get("HTTP_USER_AGENT","")[:1000],"ip_address":_client_ip(request) or None})

class CsrfView(APIView):
    permission_classes=[AllowAny]
    def get(self, request):
        from django.middleware.csrf import get_token
        return Response({"csrfToken":get_token(request)})

class RegisterView(APIView):
    permission_classes=[AllowAny]; throttle_classes=[AuthRateThrottle]
    def post(self, request):
        s=RegisterSerializer(data=request.data); s.is_valid(raise_exception=True)
        with transaction.atomic():
            birth=s.validated_data["birth_date"]
            user=User.objects.create_user(email=s.validated_data["email"], password=s.validated_data["password"])
            from apps.profiles.models import Profile
            Profile.objects.create(user=user, birth_date=birth)
        send_verification_email(user)
        return Response({"detail":"Đã tạo tài khoản. Hãy kiểm tra email để xác minh."}, status=status.HTTP_201_CREATED)

class VerifyEmailView(APIView):
    permission_classes=[AllowAny]; throttle_classes=[AuthRateThrottle]
    def post(self, request):
        try: payload=load_email_token(request.data.get("token",""), settings.EMAIL_VERIFY_MAX_AGE)
        except signing.BadSignature: return Response({"detail":"Liên kết không hợp lệ hoặc đã hết hạn."}, status=400)
        user=User.objects.filter(pk=payload["uid"], email=payload["email"]).first()
        if not user: return Response({"detail":"Liên kết không hợp lệ."}, status=400)
        user.is_email_verified=True
        if user.status == User.Status.PENDING: user.status=User.Status.ACTIVE
        user.save(update_fields=["is_email_verified","status","updated_at"])
        audit(actor=user, action="account.email_verified", target=user)
        return Response({"detail":"Xác minh email thành công."})

class ResendVerificationView(APIView):
    permission_classes=[AllowAny]; throttle_classes=[AuthRateThrottle]
    def post(self, request):
        user=User.objects.filter(email=request.data.get("email","").lower(), is_email_verified=False).first()
        if user: send_verification_email(user)
        return Response({"detail":"Nếu tài khoản tồn tại, email xác minh đã được gửi."})

class LoginView(APIView):
    permission_classes=[AllowAny]; throttle_classes=[AuthRateThrottle]
    def post(self, request):
        s=LoginSerializer(data=request.data, context={"request":request}); s.is_valid(raise_exception=True)
        user=s.validated_data["user"]
        if user.status==User.Status.SCHEDULED_DELETION:
            user.status=User.Status.ACTIVE;user.scheduled_deletion_at=None;user.save(update_fields=["status","scheduled_deletion_at","updated_at"])
        login(request,user)
        request.session.set_expiry(60*60*24*30 if s.validated_data["remember"] else 0)
        _track_session(request,user); audit(actor=user, action="account.login", target=user)
        return Response(UserSerializer(user).data)

class LogoutView(APIView):
    def post(self, request):
        UserSession.objects.filter(session_key=request.session.session_key).delete(); logout(request)
        return Response(status=204)

class MeView(APIView):
    def get(self, request): return Response(UserSerializer(request.user).data)

class ForgotPasswordView(APIView):
    permission_classes=[AllowAny]; throttle_classes=[AuthRateThrottle]
    def post(self, request):
        user=User.objects.filter(email=request.data.get("email","").lower(), status__in=[User.Status.ACTIVE,User.Status.PENDING]).first()
        if user: send_password_reset_email(user)
        return Response({"detail":"Nếu tài khoản tồn tại, hướng dẫn đặt lại mật khẩu đã được gửi."})

class ResetPasswordView(APIView):
    permission_classes=[AllowAny]; throttle_classes=[AuthRateThrottle]
    def post(self, request):
        s=PasswordResetConfirmSerializer(data=request.data); s.is_valid(raise_exception=True)
        try: payload=load_password_token(s.validated_data["token"], settings.PASSWORD_RESET_MAX_AGE)
        except signing.BadSignature: return Response({"detail":"Liên kết không hợp lệ hoặc đã hết hạn."}, status=400)
        user=User.objects.filter(pk=payload["uid"]).first()
        if not user or user.password[-12:] != payload["pwd"]: return Response({"detail":"Liên kết không hợp lệ hoặc đã được sử dụng."}, status=400)
        user.set_password(s.validated_data["password"]); user.save(update_fields=["password","updated_at"])
        Session.objects.filter(session_key__in=UserSession.objects.filter(user=user).values("session_key")).delete(); UserSession.objects.filter(user=user).delete()
        audit(actor=user, action="account.password_reset", target=user)
        return Response({"detail":"Đặt lại mật khẩu thành công."})

class ChangePasswordView(APIView):
    def post(self, request):
        current=request.data.get("current_password",""); new=request.data.get("new_password","")
        if not request.user.check_password(current): return Response({"current_password":["Mật khẩu hiện tại không đúng."]},status=400)
        validate_password(new, request.user); request.user.set_password(new); request.user.save(update_fields=["password","updated_at"])
        update_session_auth_hash(request,request.user); _track_session(request,request.user)
        audit(actor=request.user, action="account.password_changed", target=request.user)
        return Response({"detail":"Đổi mật khẩu thành công."})

class SessionListView(APIView):
    def get(self,request):
        data=[{"id":str(s.id),"current":s.session_key==request.session.session_key,"user_agent":s.user_agent,"ip_address":s.ip_address,"last_seen_at":s.last_seen_at,"created_at":s.created_at} for s in request.user.tracked_sessions.all().order_by("-last_seen_at")]
        return Response(data)

class SessionDeleteView(APIView):
    def delete(self,request,pk):
        from django.shortcuts import get_object_or_404
        tracked=get_object_or_404(UserSession,pk=pk,user=request.user)
        Session.objects.filter(session_key=tracked.session_key).delete(); tracked.delete()
        return Response(status=204)

class DeletionRequestView(APIView):
    def post(self,request):
        if not request.user.check_password(request.data.get("password","")): return Response({"password":["Mật khẩu không đúng."]},status=400)
        user=request.user; user.status=User.Status.SCHEDULED_DELETION; user.scheduled_deletion_at=timezone.now()+timedelta(days=settings.ACCOUNT_DELETION_GRACE_DAYS); user.save(update_fields=["status","scheduled_deletion_at","updated_at"])
        if hasattr(user,"profile"): user.profile.visibility_status="hidden_by_user"; user.profile.save(update_fields=["visibility_status","updated_at"])
        audit(actor=user,action="account.deletion_scheduled",target=user,after={"scheduled_deletion_at":user.scheduled_deletion_at.isoformat()})
        logout(request); return Response({"detail":"Tài khoản đã được lên lịch xóa."})
    def delete(self,request):
        user=request.user
        if user.status != User.Status.SCHEDULED_DELETION: return Response({"detail":"Không có yêu cầu xóa."},status=400)
        user.status=User.Status.ACTIVE; user.scheduled_deletion_at=None; user.save(update_fields=["status","scheduled_deletion_at","updated_at"])
        return Response(status=204)


class UserPreferenceView(APIView):
    def get(self, request):
        obj, _ = UserPreference.objects.get_or_create(user=request.user)
        return Response(UserPreferenceSerializer(obj).data)

    def patch(self, request):
        obj, _ = UserPreference.objects.get_or_create(user=request.user)
        serializer = UserPreferenceSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        audit(actor=request.user, action="account.preferences_updated", target=obj)
        return Response(serializer.data)

class EmailChangeView(APIView):
    def post(self, request):
        serializer = EmailChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not request.user.check_password(serializer.validated_data["password"]):
            return Response({"password": ["Mật khẩu không đúng."]}, status=400)
        request.user.email = serializer.validated_data["new_email"]
        request.user.is_email_verified = False
        request.user.status = User.Status.PENDING
        request.user.save(update_fields=["email", "is_email_verified", "status", "updated_at"])
        send_verification_email(request.user)
        audit(actor=request.user, action="account.email_changed", target=request.user)
        logout(request)
        return Response({"detail": "Email đã được thay đổi. Hãy xác minh email mới để đăng nhập lại."})
