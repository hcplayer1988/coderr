"""URL configuration for order API endpoints."""
from django.urls import path
from .views import OrderListCreateView, OrderDetailView

urlpatterns = [
    path('orders/', OrderListCreateView.as_view(), name='order-list'),
    path('orders/<int:id>/', OrderDetailView.as_view(), name='order-detail'),
]


