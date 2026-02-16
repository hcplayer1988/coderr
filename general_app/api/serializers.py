"""Serializers for general API endpoints."""
from rest_framework import serializers


class BaseInfoSerializer(serializers.Serializer):
    """
    Serializer for base platform information.

    Used for GET /api/base-info/
    """

    review_count = serializers.IntegerField(
        help_text='Total number of reviews on the platform'
    )

    average_rating = serializers.FloatField(
        help_text='Average rating across all reviews '
                  '(rounded to 1 decimal place)'
    )

    business_profile_count = serializers.IntegerField(
        help_text='Total number of business user profiles'
    )

    offer_count = serializers.IntegerField(
        help_text='Total number of offers on the platform'
    )
