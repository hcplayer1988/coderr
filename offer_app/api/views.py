"""Views for offer API endpoints."""
from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Min, Q
from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from offer_app.models import Offer, OfferDetail
from .serializers import OfferListSerializer, OfferCreateSerializer


class OfferPagination(PageNumberPagination):
    """
    Custom pagination for offers.
    Allows client to set page size via page_size query parameter.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class OfferListCreateView(generics.ListCreateAPIView):
    """
    API endpoint to list and create offers.
    
    GET /api/offers/ - List all offers (no authentication required)
    POST /api/offers/ - Create offer (business users only)
    """
    
    queryset = Offer.objects.select_related('user').prefetch_related('details').all()
    pagination_class = OfferPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Search configuration
    search_fields = ['title', 'description']
    
    # Ordering configuration
    ordering_fields = ['updated_at', 'created_at']
    ordering = ['-created_at']
    
    def get_permissions(self):
        """
        GET requests don't need authentication.
        POST requests need authentication.
        """
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]
    
    def get_serializer_class(self):
        """Use different serializers for GET and POST."""
        if self.request.method == 'POST':
            return OfferCreateSerializer
        return OfferListSerializer
    
    def get_queryset(self):
        """Get queryset with filtering applied."""
        queryset = Offer.objects.select_related('user').prefetch_related('details').all()
        
        # Filter by creator_id
        creator_id = self.request.query_params.get('creator_id', None)
        if creator_id:
            queryset = queryset.filter(user_id=creator_id)
        
        # Filter by min_price
        min_price = self.request.query_params.get('min_price', None)
        if min_price:
            try:
                min_price_value = float(min_price)
                queryset = queryset.filter(details__price__gte=min_price_value).distinct()
            except (ValueError, TypeError):
                pass
        
        # Filter by max_delivery_time
        max_delivery_time = self.request.query_params.get('max_delivery_time', None)
        if max_delivery_time:
            try:
                max_time_value = int(max_delivery_time)
                queryset = queryset.filter(details__delivery_time_in_days__lte=max_time_value).distinct()
            except (ValueError, TypeError):
                pass
        
        # Handle custom ordering by min_price
        ordering = self.request.query_params.get('ordering', None)
        if ordering:
            if 'min_price' in ordering:
                queryset = queryset.annotate(
                    min_offer_price=Min('details__price')
                )
                if ordering.startswith('-'):
                    queryset = queryset.order_by('-min_offer_price')
                else:
                    queryset = queryset.order_by('min_offer_price')
            elif ordering in ['updated_at', '-updated_at', 'created_at', '-created_at']:
                queryset = queryset.order_by(ordering)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """
        List all offers with pagination.
        
        Returns:
            200: Paginated list of offers
            500: Internal server error
        """
        try:
            queryset = self.filter_queryset(self.get_queryset())
            
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': 'Internal server error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def create(self, request, *args, **kwargs):
        """
        Create a new offer with nested details.
        
        Returns:
            201: Offer successfully created
            400: Validation errors
            401: User not authenticated
            403: User is not a business user
            500: Internal server error
        """
        try:
            # Check if user is business type
            if request.user.type != 'business':
                return Response(
                    {'detail': 'Only business users can create offers.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = self.get_serializer(data=request.data)
            
            if serializer.is_valid():
                offer = serializer.save(user=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response(
                {'error': 'Internal server error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OfferDetailView(generics.RetrieveAPIView):
    """
    API endpoint to retrieve a single offer by ID.
    
    GET /api/offers/{id}/
    """
    
    serializer_class = OfferListSerializer
    permission_classes = [IsAuthenticated]
    queryset = Offer.objects.select_related('user').prefetch_related('details').all()
    lookup_field = 'id'
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a single offer by ID.
        
        Returns:
            200: Offer details
            401: User not authenticated
            404: Offer not found
            500: Internal server error
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Http404:
            return Response(
                {'detail': 'Offer not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        except Exception as e:
            return Response(
                {'error': 'Internal server error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



