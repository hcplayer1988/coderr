"""URL configuration for offer API endpoints."""
from django.urls import path
from .views import OfferListCreateView

urlpatterns = [
    path('offers/', OfferListCreateView.as_view(), name='offer-list'),
]
