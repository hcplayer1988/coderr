"""Views for offer API endpoints."""
from rest_framework import generics, status, filters, serializers
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import PermissionDenied
from django.db.models import Min
from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend

from offer_app.models import Offer, OfferDetail
from .serializers import (
    OfferListSerializer,
    OfferRetrieveSerializer,
    OfferCreateSerializer,
    OfferUpdateSerializer,
    OfferDetailSingleSerializer
)
from .permissions import IsOfferOwner


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

    queryset = Offer.objects.select_related('user').prefetch_related(
        'details'
    ).all()
    pagination_class = OfferPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    search_fields = ['title', 'description']
    ordering_fields = ['updated_at', 'created_at']
    ordering = ['-created_at']

    def get_permissions(self):
        """GET requests don't need authentication, POST does."""
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
        queryset = Offer.objects.select_related('user').prefetch_related(
            'details'
        ).all()

        creator_id = self.request.query_params.get('creator_id', None)
        if creator_id:
            queryset = queryset.filter(user_id=creator_id)

        min_price = self.request.query_params.get('min_price', None)
        if min_price:
            try:
                min_price_value = float(min_price)
                queryset = queryset.filter(
                    details__price__gte=min_price_value
                ).distinct()
            except (ValueError, TypeError):
                pass

        max_delivery_time = self.request.query_params.get(
            'max_delivery_time',
            None
        )
        if max_delivery_time:
            try:
                max_time_value = int(max_delivery_time)
                queryset = queryset.filter(
                    details__delivery_time_in_days__lte=max_time_value
                ).distinct()
            except (ValueError, TypeError):
                pass

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
            elif ordering in [
                'updated_at',
                '-updated_at',
                'created_at',
                '-created_at'
            ]:
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
            if request.user.type != 'business':
                return Response(
                    {'detail': 'Only business users can create offers.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = self.get_serializer(data=request.data)

            if serializer.is_valid():
                serializer.save(user=request.user)
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {'error': 'Internal server error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OfferDetailUpdateView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint to retrieve, update, and delete a single offer.

    GET /api/offers/{id}/    - Retrieve offer (authenticated users)
    PATCH /api/offers/{id}/  - Update offer (owner only)
    DELETE /api/offers/{id}/ - Delete offer (owner only)
    """

    queryset = Offer.objects.select_related('user').prefetch_related(
        'details'
    ).all()
    lookup_field = 'id'

    def get_permissions(self):
        """GET needs authentication. PATCH/DELETE need ownership."""
        if self.request.method in ['PATCH', 'DELETE']:
            return [IsAuthenticated(), IsOfferOwner()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        """
        Use different serializers per method.

        GET    → OfferRetrieveSerializer (no user_details)
        PATCH  → OfferUpdateSerializer
        """
        if self.request.method == 'PATCH':
            return OfferUpdateSerializer
        return OfferRetrieveSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a single offer by ID.

        Response fields: id, user, title, image, description,
                         created_at, updated_at, details[{id,url}],
                         min_price, min_delivery_time

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

    def update(self, request, *args, **kwargs):
        """
        Update an existing offer (partial update).

        Response fields: id, title, image, description,
                         details[vollständige Objekte]

        Returns:
            200: Offer successfully updated
            400: Validation errors or invalid detail IDs
            401: User not authenticated
            403: User is not the owner
            404: Offer not found
            500: Internal server error
        """
        try:
            instance = self.get_object()

            serializer = self.get_serializer(
                instance,
                data=request.data,
                partial=True
            )

            if serializer.is_valid():
                self.perform_update(serializer)
                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        except PermissionDenied:
            return Response(
                {
                    'detail': 'You do not have permission to perform '
                              'this action.'
                },
                status=status.HTTP_403_FORBIDDEN
            )

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

    def destroy(self, request, *args, **kwargs):
        """
        Delete an existing offer.

        Returns:
            204: Offer successfully deleted (no content)
            401: User not authenticated
            403: User is not the owner
            404: Offer not found
            500: Internal server error
        """
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)

        except PermissionDenied:
            return Response(
                {
                    'detail': 'You do not have permission to perform '
                              'this action.'
                },
                status=status.HTTP_403_FORBIDDEN
            )

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


class OfferDetailSingleView(generics.RetrieveAPIView):
    """
    API endpoint to retrieve a single offer detail.

    GET /api/offerdetails/{id}/ - Retrieve offer detail (authenticated users)
    """

    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSingleSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a single offer detail by ID.

        Response fields: id, title, revisions, delivery_time_in_days,
                         price (int), features (list), offer_type

        Returns:
            200: Offer detail data
            401: User not authenticated
            404: Offer detail not found
            500: Internal server error
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Http404:
            return Response(
                {'detail': 'Offer detail not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return Response(
                {'error': 'Internal server error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



