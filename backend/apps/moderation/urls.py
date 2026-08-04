from django.urls import path
from .views import *
urlpatterns=[path("blocks",BlockListView.as_view()),path("users/<uuid:public_id>/block",BlockView.as_view()),path("reports",ReportCreateView.as_view()),path("staff/reports",StaffReportListView.as_view()),path("staff/reports/<uuid:pk>/action",StaffReportActionView.as_view()),path("staff/reports/<uuid:pk>/dismiss",StaffReportDismissView.as_view())]
