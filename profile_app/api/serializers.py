"""Serializers for profile API endpoints."""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from profile_app.models import Profile

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profiles.
    Returns complete profile information including user data.
    """
    
    # Read-only fields from related User model
    user = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    type = serializers.CharField(source='user.type', read_only=True)
    
    # Profile picture with proper URL handling
    file = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = Profile
        fields = [
            'user',
            'username',
            'first_name',
            'last_name',
            'file',
            'location',
            'tel',
            'description',
            'working_hours',
            'type',
            'email',
            'created_at'
        ]
        read_only_fields = ['user', 'username', 'email', 'type', 'created_at']
    
    def to_representation(self, instance):
        """
        Override to ensure empty strings instead of null for required fields.
        """
        representation = super().to_representation(instance)
        
        # Fields that must not be null - replace None with empty string
        string_fields = ['first_name', 'last_name', 'location', 'tel', 'description', 'working_hours']
        
        for field in string_fields:
            if representation.get(field) is None:
                representation[field] = ''
        
        # Handle file field - return filename or empty string
        if representation.get('file'):
            # Return just the filename or full URL depending on your needs
            representation['file'] = instance.file.name if instance.file else ''
        else:
            representation['file'] = ''
        
        return representation



