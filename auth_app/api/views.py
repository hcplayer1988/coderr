"""Views for authentication API endpoints."""
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from .serializers import RegistrationSerializer, LoginSerializer

User = get_user_model()


class RegistrationView(generics.GenericAPIView):
    """
    API endpoint for user registration.

    Creates a new user (customer or business) and returns authentication token.

    POST /api/registration/
    """

    permission_classes = [AllowAny]
    serializer_class = RegistrationSerializer

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
            serializer = self.get_serializer(data=request.data)

            if serializer.is_valid():
                user = serializer.save()

                token, created = Token.objects.get_or_create(user=user)

                response_data = {
                    'token': token.key,
                    'username': user.username,
                    'email': user.email,
                    'user_id': user.id
                }

                return Response(
                    response_data,
                    status=status.HTTP_201_CREATED
                )

            else:
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            return Response(
                {'error': 'Internal server error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LoginView(generics.GenericAPIView):
    """
    API endpoint for user login.

    Authenticates user and returns authentication token.

    POST /api/login/
    """

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        """
        Authenticate user and return token.

        Request Body:
            - username: string (required)
            - password: string (required)

        Returns:
            200: Successful authentication with token
            400: Invalid credentials or validation errors
            500: Internal server error
        """
        try:
            serializer = self.get_serializer(data=request.data)

            if serializer.is_valid():
                user = serializer.validated_data['user']

                token, created = Token.objects.get_or_create(user=user)

                response_data = {
                    'token': token.key,
                    'username': user.username,
                    'email': user.email,
                    'user_id': user.id
                }

                return Response(response_data, status=status.HTTP_200_OK)

            else:
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            return Response(
                {'error': 'Internal server error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            

