from django.urls import path
from .views import *
urlpatterns=[path("connections/requests",ConnectionCreateView.as_view()),path("connections/received",ReceivedListView.as_view()),path("connections/sent",SentListView.as_view()),path("connections/accepted",AcceptedListView.as_view()),path("connections/<uuid:pk>/accept",ConnectionAcceptView.as_view()),path("connections/<uuid:pk>/decline",ConnectionDeclineView.as_view()),path("connections/<uuid:pk>/cancel",ConnectionCancelView.as_view()),path("connections/<uuid:pk>",ConnectionDeleteView.as_view())]
