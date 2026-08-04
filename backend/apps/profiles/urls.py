from django.urls import path
from .views import (
    ReferenceDataView, MyProfileView, ProfilePublishView, ProfileHideView,
    PhotoPresignView, PhotoCompleteView, PhotoReorderView, PhotoPrimaryView,
    PhotoDeleteView, DiscoverView, PublicProfileDetailView, DiscoveryPreferenceView,
)

urlpatterns = [
    path("reference-data", ReferenceDataView.as_view()),
    path("me/profile", MyProfileView.as_view()),
    path("me/profile/publish", ProfilePublishView.as_view()),
    path("me/profile/hide", ProfileHideView.as_view()),
    path("me/photos/presign", PhotoPresignView.as_view()),
    path("me/photos/complete", PhotoCompleteView.as_view()),
    path("me/photos/reorder", PhotoReorderView.as_view()),
    path("me/photos/<uuid:pk>/primary", PhotoPrimaryView.as_view()),
    path("me/photos/<uuid:pk>", PhotoDeleteView.as_view()),
    path("me/discovery-preferences", DiscoveryPreferenceView.as_view()),
    path("discover", DiscoverView.as_view()),
    path("profiles/<uuid:public_id>", PublicProfileDetailView.as_view()),
]
