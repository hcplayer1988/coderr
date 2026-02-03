"""URL configuration for offer API endpoints."""
from django.urls import path
from .views import OfferListView

urlpatterns = [
    path('offers/', OfferListView.as_view(), name='offer-list'),
]
