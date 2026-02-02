"""Serializers for authentication API endpoints."""
from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from rest_framework.authtoken.models import Token

User = get_user_model()


class RegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    Handles validation of username, email, passwords and user type.
    """
    
    repeated_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    type = serializers.ChoiceField(
        choices=['customer', 'business'],
        required=True
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'repeated_password', 'type']
        extra_kwargs = {
            'email': {'required': True},
        }
    
    def validate_username(self, value):
        """Validate that username is unique."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value
    
    def validate_email(self, value):
        """Validate that email is unique and properly formatted."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate(self, data):
        """Validate that passwords match."""
        password = data.get('password')
        repeated_password = data.get('repeated_password')
        
        if password != repeated_password:
            raise serializers.ValidationError({
                "repeated_password": "Passwords do not match."
            })
        
        return data
    
    def create(self, validated_data):
        """Create new user with hashed password."""
        # Remove repeated_password as it's not part of the User model
        validated_data.pop('repeated_password')
        
        # Create user with create_user method to properly hash password
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            type=validated_data['type']
        )
        
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    Authenticates user with username and password.
    """
    
    username = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, data):
        """
        Validate username and password.
        Authenticate user and attach user object to validated_data.
        """
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            raise serializers.ValidationError({
                'detail': 'Username and password are required.'
            })
        
        # Authenticate user
        user = authenticate(username=username, password=password)
        
        if user is None:
            raise serializers.ValidationError({
                'detail': 'Invalid credentials.'
            })
        
        if not user.is_active:
            raise serializers.ValidationError({
                'detail': 'User account is disabled.'
            })
        
        # Attach user to validated data for use in view
        data['user'] = user
        return data