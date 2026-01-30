"""Views for authentication API endpoints."""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from .serializers import RegistrationSerializer

User = get_user_model()


class RegistrationView(APIView):
    """
    API endpoint for user registration.
    Creates a new user (customer or business) and returns authentication token.
    
    POST /api/registration/
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Register a new user.
        
        Request Body:
            - username: string (required, unique)
            - email: string (required, unique, valid email)
            - password: string (required)
            - repeated_password: string (required, must match password)
            - type: string (required, either "customer" or "business")
        
        Returns:
            201: User successfully created with token
            400: Invalid data (validation errors)
            500: Internal server error
        """
        try:
            serializer = RegistrationSerializer(data=request.data)
            
            if serializer.is_valid():
                # Create user
                user = serializer.save()
                
                # Generate or get token for the user
                token, created = Token.objects.get_or_create(user=user)
                
                # Prepare success response
                response_data = {
                    'token': token.key,
                    'username': user.username,
                    'email': user.email,
                    'user_id': user.id
                }
                
                return Response(response_data, status=status.HTTP_201_CREATED)
            
            else:
                # Return validation errors
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            # Handle unexpected errors
            return Response(
                {'error': 'Internal server error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )