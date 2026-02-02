"""URL configuration for profile API endpoints."""
from django.urls import path
from .views import ProfileDetailUpdateView

urlpatterns = [
    path('profile/<int:pk>/', ProfileDetailUpdateView.as_view(), name='profile-detail'),
]