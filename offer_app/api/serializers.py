"""Serializers for offer API endpoints."""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from offer_app.models import Offer, OfferDetail

User = get_user_model()


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for user details in offer responses.
    Returns minimal user information from User and Profile.
    """
    
    first_name = serializers.CharField(source='profile.first_name', read_only=True)
    last_name = serializers.CharField(source='profile.last_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username']


class OfferDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for OfferDetail objects.
    Used for creating and displaying offer details.
    """
    
    class Meta:
        model = OfferDetail
        fields = [
            'id',
            'title',
            'revisions',
            'delivery_time_in_days',
            'price',
            'features',
            'offer_type'
        ]
        read_only_fields = ['id']
    
    def validate_price(self, value):
        """Validate that price is not negative."""
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value
    
    def validate_delivery_time_in_days(self, value):
        """Validate that delivery time is positive."""
        if value <= 0:
            raise serializers.ValidationError("Delivery time must be positive.")
        return value
    
    def validate_revisions(self, value):
        """Validate that revisions is not negative."""
        if value < 0:
            raise serializers.ValidationError("Revisions cannot be negative.")
        return value


class OfferListSerializer(serializers.ModelSerializer):
    """
    Serializer for offer list view.
    Returns paginated list with minimal details and computed min values.
    """
    
    user = serializers.IntegerField(source='user.id', read_only=True)
    details = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()
    user_details = UserDetailSerializer(source='user', read_only=True)
    
    class Meta:
        model = Offer
        fields = [
            'id',
            'user',
            'title',
            'image',
            'description',
            'created_at',
            'updated_at',
            'details',
            'min_price',
            'min_delivery_time',
            'user_details'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_details(self, obj):
        """Return list of details with id and url."""
        request = self.context.get('request')
        details_list = []
        for detail in obj.details.all():
            if request:
                url = request.build_absolute_uri(f'/api/offerdetails/{detail.id}/')
            else:
                url = f'/offerdetails/{detail.id}/'
            details_list.append({
                'id': detail.id,
                'url': url
            })
        return details_list
    
    def get_min_price(self, obj):
        """Get minimum price from offer details."""
        details = obj.details.all()
        if details.exists():
            return float(min(detail.price for detail in details))
        return 0
    
    def get_min_delivery_time(self, obj):
        """Get minimum delivery time from offer details."""
        details = obj.details.all()
        if details.exists():
            return min(detail.delivery_time_in_days for detail in details)
        return 0
    
    def to_representation(self, instance):
        """Override to handle image field."""
        representation = super().to_representation(instance)
        
        # Handle image field
        if representation.get('image'):
            representation['image'] = instance.image.name if instance.image else None
        else:
            representation['image'] = None
        
        return representation


class OfferCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating offers.
    Accepts nested offer details and creates them together with the offer.
    """
    
    details = OfferDetailSerializer(many=True, write_only=True)
    
    # Read-only fields for response
    user = serializers.IntegerField(source='user.id', read_only=True)
    user_details = UserDetailSerializer(source='user', read_only=True)
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()
    
    class Meta:
        model = Offer
        fields = [
            'id',
            'user',
            'title',
            'image',
            'description',
            'created_at',
            'updated_at',
            'details',
            'min_price',
            'min_delivery_time',
            'user_details'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'user_details']
    
    def validate_details(self, value):
        """Validate that at least one detail is provided."""
        if not value:
            raise serializers.ValidationError("At least one offer detail is required.")
        return value
    
    def create(self, validated_data):
        """Create offer with nested details."""
        details_data = validated_data.pop('details')
        
        # Create the offer
        offer = Offer.objects.create(**validated_data)
        
        # Create offer details
        for detail_data in details_data:
            OfferDetail.objects.create(offer=offer, **detail_data)
        
        return offer
    
    def get_min_price(self, obj):
        """Get minimum price from offer details."""
        details = obj.details.all()
        if details.exists():
            return float(min(detail.price for detail in details))
        return 0
    
    def get_min_delivery_time(self, obj):
        """Get minimum delivery time from offer details."""
        details = obj.details.all()
        if details.exists():
            return min(detail.delivery_time_in_days for detail in details)
        return 0
    
    def to_representation(self, instance):
        """Return full offer data with complete details in response."""
        representation = super().to_representation(instance)
        
        # Replace details with full OfferDetail serializer
        details_queryset = instance.details.all()
        representation['details'] = OfferDetailSerializer(details_queryset, many=True).data
        
        # Handle image field
        if representation.get('image'):
            representation['image'] = instance.image.name if instance.image else None
        else:
            representation['image'] = None
        
        return representation
    
    
    