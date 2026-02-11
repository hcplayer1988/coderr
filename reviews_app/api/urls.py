"""URL configuration for reviews API endpoints."""
from django.urls import path
from .views import ReviewListCreateView, ReviewDetailView

urlpatterns = [
    path('reviews/', ReviewListCreateView.as_view(), name='review-list'),
    path('reviews/<int:id>/', ReviewDetailView.as_view(), name='review-detail'),
]
