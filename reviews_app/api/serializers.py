"""Serializers for reviews API endpoints."""
from rest_framework import serializers
from django.contrib.auth import get_user_model

from reviews_app.models import Review

User = get_user_model()


class ReviewListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing reviews.

    Used for GET /api/reviews/
    """

    class Meta:
        model = Review
        fields = [
            'id',
            'business_user',
            'reviewer',
            'rating',
            'description',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ReviewCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating reviews.

    Used for POST /api/reviews/
    """

    class Meta:
        model = Review
        fields = [
            'id',
            'business_user',
            'rating',
            'description',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_rating(self, value):
        """Validate that rating is between 1 and 5."""
        if value < 1 or value > 5:
            raise serializers.ValidationError(
                "Rating must be between 1 and 5."
            )
        return value

    def validate_business_user(self, value):
        """Validate that business_user exists and is a business type."""
        if not value:
            raise serializers.ValidationError("Business user is required.")

        if value.type != 'business':
            raise serializers.ValidationError(
                "You can only review business users."
            )

        return value

    def validate(self, data):
        """
        Validate reviewer constraints.

        - User must have a customer profile
        - User cannot review themselves
        - User cannot submit duplicate reviews
        """
        request = self.context.get('request')

        if request and request.user.type != 'customer':
            raise serializers.ValidationError(
                "Only users with a customer profile can create reviews."
            )

        if request and request.user == data.get('business_user'):
            raise serializers.ValidationError(
                "You cannot review yourself."
            )

        if request:
            existing_review = Review.objects.filter(
                business_user=data.get('business_user'),
                reviewer=request.user
            ).exists()

            if existing_review:
                raise serializers.ValidationError(
                    "You have already reviewed this business user. "
                    "You can only submit one review per business profile."
                )

        return data

    def create(self, validated_data):
        """Create review with reviewer set to current user."""
        request = self.context.get('request')
        validated_data['reviewer'] = request.user
        return super().create(validated_data)

    def to_representation(self, instance):
        """Return full review data including reviewer."""
        return ReviewListSerializer(instance).data


class ReviewUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating reviews.

    Used for PATCH /api/reviews/{id}/
    Only rating and description can be updated.
    """

    class Meta:
        model = Review
        fields = [
            'id',
            'business_user',
            'reviewer',
            'rating',
            'description',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'business_user',
            'reviewer',
            'created_at',
            'updated_at'
        ]

    def validate_rating(self, value):
        """Validate that rating is between 1 and 5."""
        if value < 1 or value > 5:
            raise serializers.ValidationError(
                "Rating must be between 1 and 5."
            )
        return value
    
