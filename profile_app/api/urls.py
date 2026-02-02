"""URL configuration for profile API endpoints."""
from django.urls import path
from .views import ProfileDetailView

urlpatterns = [
    path('profile/<int:pk>/', ProfileDetailView.as_view(), name='profile-detail'),
    # path('profile/<int:pk>/', ProfileUpdateView.as_view(), name='profile-update'),  # PATCH - coming next
    # path('profiles/business/', BusinessProfileListView.as_view(), name='business-profiles'),
    # path('profiles/customer/', CustomerProfileListView.as_view(), name='customer-profiles'),
]
