from django.urls import path

from .views import *

urlpatterns = [
    path("csrf", CsrfView.as_view()),
    path("register", RegisterView.as_view()),
    path("email/verify", VerifyEmailView.as_view()),
    path("email/resend", ResendVerificationView.as_view()),
    path("phone/send", PhoneSendOtpView.as_view()),
    path("phone/verify", PhoneVerifyOtpView.as_view()),
    path("login", LoginView.as_view()),
    path("logout", LogoutView.as_view()),
    path("me", MeView.as_view()),
    path("password/forgot", ForgotPasswordView.as_view()),
    path("password/reset", ResetPasswordView.as_view()),
    path("password/change", ChangePasswordView.as_view()),
    path("sessions", SessionListView.as_view()),
    path("sessions/<uuid:pk>", SessionDeleteView.as_view()),
    path("preferences", UserPreferenceView.as_view()),
    path("email/change", EmailChangeView.as_view()),
    path("deletion-request", DeletionRequestView.as_view()),
]
