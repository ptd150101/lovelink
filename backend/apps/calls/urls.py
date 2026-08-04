from django.urls import path
from .views import *
urlpatterns=[path("calls",CallCreateView.as_view()),path("calls/<uuid:pk>",CallDetailView.as_view()),path("calls/<uuid:pk>/accept",CallAcceptView.as_view()),path("calls/<uuid:pk>/token",CallTokenView.as_view()),path("calls/<uuid:pk>/decline",CallDeclineView.as_view()),path("calls/<uuid:pk>/cancel",CallCancelView.as_view()),path("calls/<uuid:pk>/end",CallEndView.as_view()),path("webhooks/livekit",LiveKitWebhookView.as_view())]
