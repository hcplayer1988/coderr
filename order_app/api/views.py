"""Views for order API endpoints."""
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q
from django.http import Http404
from order_app.models import Order
from .serializers import OrderListSerializer, OrderCreateSerializer, OrderUpdateSerializer
from .permissions import IsBusinessUserOfOrder, IsAdminUser


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


class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint to update and delete orders.
    
    PATCH /api/orders/{id}/ - Update order status (business user only)
    DELETE /api/orders/{id}/ - Delete order (admin only)
    """
    
    queryset = Order.objects.all()
    lookup_field = 'id'
    http_method_names = ['patch', 'delete', 'options', 'head']
    
    def get_permissions(self):
        """
        PATCH requires IsAuthenticated + IsBusinessUserOfOrder.
        DELETE requires IsAuthenticated + IsAdminUser.
        """
        if self.request.method == 'DELETE':
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated(), IsBusinessUserOfOrder()]
    
    def get_serializer_class(self):
        """Use OrderUpdateSerializer for PATCH."""
        return OrderUpdateSerializer
    
    def update(self, request, *args, **kwargs):
        """
        Update order status (partial update only).
        
        Returns:
            200: Order successfully updated
            400: Validation errors (invalid status)
            401: User not authenticated
            403: User is not the business user of this order
            404: Order not found
            500: Internal server error
        """
        try:
            instance = self.get_object()
            
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except PermissionDenied:
            return Response(
                {'detail': 'You do not have permission to perform this action.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        except Http404:
            return Response(
                {'detail': 'Order not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        except Exception as e:
            return Response(
                {'error': 'Internal server error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete an order.
        
        Returns:
            204: Order successfully deleted (no content)
            401: User not authenticated
            403: User is not admin/staff
            404: Order not found
            500: Internal server error
        """
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        except PermissionDenied:
            return Response(
                {'detail': 'You do not have permission to perform this action.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        except Http404:
            return Response(
                {'detail': 'Order not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        except Exception as e:
            return Response(
                {'error': 'Internal server error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OrderCountView(generics.GenericAPIView):
    """
    API endpoint to get count of in_progress orders for a business user.
    
    GET /api/order-count/{business_user_id}/
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, business_user_id):
        """
        Get count of in_progress orders for a business user.
        
        Returns:
            200: Order count
            401: User not authenticated
            404: Business user not found
            500: Internal server error
        """
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            try:
                business_user = User.objects.get(id=business_user_id)
            except User.DoesNotExist:
                return Response(
                    {'detail': 'Business user not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            order_count = Order.objects.filter(
                business_user_id=business_user_id,
                status='in_progress'
            ).count()
            
            return Response(
                {'order_count': order_count},
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            return Response(
                {'error': 'Internal server error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CompletedOrderCountView(generics.GenericAPIView):
    """
    API endpoint to get count of completed orders for a business user.
    
    GET /api/completed-order-count/{business_user_id}/
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, business_user_id):
        """
        Get count of completed orders for a business user.
        
        Returns:
            200: Completed order count
            401: User not authenticated
            404: Business user not found
            500: Internal server error
        """
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            try:
                business_user = User.objects.get(id=business_user_id)
            except User.DoesNotExist:
                return Response(
                    {'detail': 'Business user not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            completed_order_count = Order.objects.filter(
                business_user_id=business_user_id,
                status='completed'
            ).count()
            
            return Response(
                {'completed_order_count': completed_order_count},
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            return Response(
                {'error': 'Internal server error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )




