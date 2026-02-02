"""Views for profile API endpoints."""
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.http import Http404
from profile_app.models import Profile
from .serializers import ProfileSerializer

User = get_user_model()


class ProfileDetailView(generics.RetrieveAPIView):
    """
    API endpoint to retrieve a user's profile.
    Returns detailed profile information for a specific user.
    
    GET /api/profile/{pk}/
    """
    
    queryset = Profile.objects.select_related('user').all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'user__id'
    lookup_url_kwarg = 'pk'
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve profile by user ID.
        
        URL Parameters:
            - pk: User ID
        
        Returns:
            200: Profile data successfully retrieved
            401: User not authenticated
            404: Profile not found
            500: Internal server error
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Http404:
            return Response(
                {'detail': 'Profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        except Profile.DoesNotExist:
            return Response(
                {'detail': 'Profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        except Exception as e:
            return Response(
                {'error': 'Internal server error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
