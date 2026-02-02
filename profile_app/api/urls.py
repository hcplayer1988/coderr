"""URL configuration for profile API endpoints."""
from django.urls import path
from .views import ProfileDetailUpdateView, BusinessProfileListView, CustomerProfileListView

urlpatterns = [
    path('profile/<int:pk>/', ProfileDetailUpdateView.as_view(), name='profile-detail'),
    path('profiles/business/', BusinessProfileListView.as_view(), name='business-profiles'),
    path('profiles/customer/', CustomerProfileListView.as_view(), name='customer-profiles'),
]