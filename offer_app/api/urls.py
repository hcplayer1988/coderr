"""URL configuration for offer API endpoints."""
from django.urls import path
from .views import (
    OfferListCreateView,
    OfferDetailUpdateView,
    OfferDetailSingleView
)

urlpatterns = [
    path('offers/', OfferListCreateView.as_view(), name='offer-list'),
    path(
        'offers/<int:id>/',
        OfferDetailUpdateView.as_view(),
        name='offer-detail'
    ),
    path(
        'offerdetails/<int:id>/',
        OfferDetailSingleView.as_view(),
        name='offerdetail-single'
    ),
]
