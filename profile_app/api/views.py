"""Views for profile API endpoints."""
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.http import Http404
from profile_app.models import Profile
from .serializers import ProfileSerializer, ProfileUpdateSerializer
from .permissions import IsOwnerOrReadOnly

User = get_user_model()

class ProfileDetailUpdateView(generics.RetrieveUpdateAPIView):
    """
    API endpoint to retrieve and update a user's profile.
    
    GET /api/profile/{pk}/ - Anyone authenticated can view
    PATCH /api/profile/{pk}/ - Only owner can update
    """
    
    queryset = Profile.objects.select_related('user').all()
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field = 'user__id'
    lookup_url_kwarg = 'pk'
    http_method_names = ['get', 'patch', 'options', 'head']
    
    def get_serializer_class(self):
        """Use different serializers for GET and PATCH."""
        if self.request.method == 'PATCH':
            return ProfileUpdateSerializer
        return ProfileSerializer
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve profile by user ID.
        
        GET /api/profile/{pk}/
        
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
    
    def update(self, request, *args, **kwargs):
        """
        Update profile fields (partial update).
        
        PATCH /api/profile/{pk}/
        
        Returns:
            200: Profile successfully updated
            401: User not authenticated
            403: User is not the owner of this profile
            404: Profile not found
            500: Internal server error
        """
        try:
            instance = self.get_object()
            
            self.check_object_permissions(request, instance)
            
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




