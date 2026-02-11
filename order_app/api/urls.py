"""URL configuration for order API endpoints."""
from django.urls import path
from .views import OrderListCreateView, OrderDetailView, OrderCountView

urlpatterns = [
    path('orders/', OrderListCreateView.as_view(), name='order-list'),
    path('orders/<int:id>/', OrderDetailView.as_view(), name='order-detail'),
    path('order-count/<int:business_user_id>/', OrderCountView.as_view(), name='order-count'),
]


