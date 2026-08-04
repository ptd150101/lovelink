from django.urls import path
from .views import *
urlpatterns=[path("conversations",ConversationListView.as_view()),path("conversations/<uuid:pk>",ConversationDetailView.as_view()),path("conversations/<uuid:pk>/messages",MessageListView.as_view()),path("conversations/<uuid:pk>/messages/send",MessageCreateView.as_view()),path("conversations/<uuid:pk>/read",ConversationReadView.as_view())]
