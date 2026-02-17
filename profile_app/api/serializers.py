"""Serializers for profile API endpoints."""
from rest_framework import serializers
from django.contrib.auth import get_user_model

from profile_app.models import Profile

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profiles (detail view).

    Returns complete profile information including user data.
    """

    user = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    type = serializers.CharField(source='user.type', read_only=True)

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
        """Override to ensure empty strings instead of null for fields."""
        representation = super().to_representation(instance)

        string_fields = [
            'first_name',
            'last_name',
            'location',
            'tel',
            'description',
            'working_hours'
        ]

        for field in string_fields:
            if representation.get(field) is None:
                representation[field] = ''

        if representation.get('file'):
            representation['file'] = (
                instance.file.name if instance.file else ''
            )
        else:
            representation['file'] = ''

        return representation


class ProfileListSerializer(serializers.ModelSerializer):
    """
    Serializer for profile list views.

    Returns profile information WITHOUT email and created_at.
    Used for /api/profiles/business/ and /api/profiles/customer/
    """

    user = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    type = serializers.CharField(source='user.type', read_only=True)

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
            'type'
        ]
        read_only_fields = ['user', 'username', 'type']

    def to_representation(self, instance):
        """Override to ensure empty strings instead of null for fields."""
        representation = super().to_representation(instance)

        string_fields = [
            'first_name',
            'last_name',
            'location',
            'tel',
            'description',
            'working_hours'
        ]

        for field in string_fields:
            if representation.get(field) is None:
                representation[field] = ''

        if representation.get('file'):
            representation['file'] = (
                instance.file.name if instance.file else ''
            )
        else:
            representation['file'] = ''

        return representation


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating profile information.

    Allows partial updates of profile fields.
    Also allows updating the user's email.
    """

    email = serializers.EmailField(required=False)

    user = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    type = serializers.CharField(source='user.type', read_only=True)

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
        read_only_fields = ['user', 'username', 'type', 'created_at']

    def update(self, instance, validated_data):
        """Update profile and user email if provided."""
        email = validated_data.pop('email', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if email is not None:
            instance.user.email = email
            instance.user.save()

        return instance

    def to_representation(self, instance):
        """Override to ensure empty strings instead of null for fields."""
        representation = super().to_representation(instance)

        representation['email'] = instance.user.email

        string_fields = [
            'first_name',
            'last_name',
            'location',
            'tel',
            'description',
            'working_hours'
        ]

        for field in string_fields:
            if representation.get(field) is None:
                representation[field] = ''

        if representation.get('file'):
            representation['file'] = (
                instance.file.name if instance.file else ''
            )
        else:
            representation['file'] = ''

        return representation
    
    
    