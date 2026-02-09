"""Views for order API endpoints."""
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from order_app.models import Order
from .serializers import OrderListSerializer, OrderCreateSerializer


class OrderListCreateView(generics.ListCreateAPIView):
    """
    API endpoint to list and create orders.
    
    GET /api/orders/ - List orders (customer or business)
    POST /api/orders/ - Create order (customer only)
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Use different serializers for GET and POST."""
        if self.request.method == 'POST':
            return OrderCreateSerializer
        return OrderListSerializer
    
    def get_queryset(self):
        """
        Get orders where user is either customer or business user.
        """
        user = self.request.user
        return Order.objects.filter(
            Q(customer_user=user) | Q(business_user=user)
        )
    
    def list(self, request, *args, **kwargs):
        """
        List all orders for the authenticated user.
        
        Returns:
            200: List of orders
            401: User not authenticated
            500: Internal server error
        """
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': 'Internal server error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def create(self, request, *args, **kwargs):
        """
        Create a new order from an offer detail.
        Only customer users can create orders.
        
        Returns:
            201: Order successfully created
            400: Validation errors (missing/invalid offer_detail_id)
            401: User not authenticated
            403: User is not a customer
            404: Offer detail not found
            500: Internal server error
        """
        try:
            if request.user.type != 'customer':
                return Response(
                    {'detail': 'Only customer users can create orders.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = self.get_serializer(data=request.data)
            
            if serializer.is_valid():
                order = serializer.save()
                return Response(
                    serializer.to_representation(order),
                    status=status.HTTP_201_CREATED
                )
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response(
                {'error': 'Internal server error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )




