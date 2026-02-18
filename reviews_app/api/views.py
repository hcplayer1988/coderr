"""Views for reviews API endpoints."""
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.http import Http404

from reviews_app.models import Review
from .serializers import (
    ReviewListSerializer,
    ReviewCreateSerializer,
    ReviewUpdateSerializer
)
from .permissions import IsReviewOwner


class ReviewListCreateView(generics.ListCreateAPIView):
    """
    API endpoint to list and create reviews.

    GET /api/reviews/ - List all reviews with optional filters
    POST /api/reviews/ - Create a new review
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on request method."""
        if self.request.method == 'POST':
            return ReviewCreateSerializer
        return ReviewListSerializer

    def get_queryset(self):
        """
        Get reviews with optional filtering.

        Query parameters:
            business_user_id: Filter by business user
            reviewer_id: Filter by reviewer
            ordering: Sort by 'updated_at' or 'rating'
        """
        queryset = Review.objects.all()

        business_user_id = self.request.query_params.get('business_user_id')
        if business_user_id:
            queryset = queryset.filter(business_user_id=business_user_id)

        reviewer_id = self.request.query_params.get('reviewer_id')
        if reviewer_id:
            queryset = queryset.filter(reviewer_id=reviewer_id)

        ordering = self.request.query_params.get('ordering')
        if ordering == 'updated_at':
            queryset = queryset.order_by('-updated_at')
        elif ordering == 'rating':
            queryset = queryset.order_by('-rating')
        else:
            queryset = queryset.order_by('-updated_at')

        return queryset

    def create(self, request, *args, **kwargs):
        """
        Create a new review.

        Returns:
            201: Review created successfully
            400: Validation errors
            401: User not authenticated
            403: User is not a customer (business users forbidden)
            500: Internal server error
        """
        try:
            if request.user.type != 'customer':
                return Response(
                    {
                        'detail': 'Only users with a customer profile can '
                                  'create reviews.'
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = self.get_serializer(
                data=request.data,
                context={'request': request}
            )

            if serializer.is_valid():
                review = serializer.save()
                return Response(
                    serializer.to_representation(review),
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


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint to update and delete reviews.

    PATCH /api/reviews/{id}/ - Update review (owner only)
    DELETE /api/reviews/{id}/ - Delete review (owner only)
    """

    queryset = Review.objects.all()
    lookup_field = 'id'
    http_method_names = ['patch', 'delete', 'options', 'head']

    def get_permissions(self):
        """Both PATCH and DELETE require IsAuthenticated + IsReviewOwner."""
        return [IsAuthenticated(), IsReviewOwner()]

    def get_serializer_class(self):
        """Use ReviewUpdateSerializer for PATCH."""
        return ReviewUpdateSerializer

    def update(self, request, *args, **kwargs):
        """
        Update review (rating and/or description).

        Returns:
            200: Review updated successfully
            400: Validation errors
            401: User not authenticated
            403: User is not the review owner
            404: Review not found
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
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

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
                {'detail': 'Review not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return Response(
                {'error': 'Internal server error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        """
        Delete review.

        Returns:
            204: Review deleted successfully
            401: User not authenticated
            403: User is not the review owner
            404: Review not found
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
                {'detail': 'Review not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return Response(
                {'error': 'Internal server error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            


