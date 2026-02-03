"""Serializers for offer API endpoints."""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from offer_app.models import Offer, OfferDetail

User = get_user_model()


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for user details in offer responses.
    Returns minimal user information.
    """
    
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username']


class OfferDetailURLSerializer(serializers.Serializer):
    """
    Serializer for offer detail URLs.
    Returns just the URL to the detail endpoint.
    """
    url = serializers.SerializerMethodField()
    
    def get_url(self, obj):
        """Generate URL for offer detail."""
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/api/offerdetails/{obj.id}/')
        return f'/offerdetails/{obj.id}/'


class OfferListSerializer(serializers.ModelSerializer):
    """
    Serializer for offer list view.
    Returns paginated list with minimal details and computed min values.
    """
    
    details = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()
    user_details = UserDetailSerializer(source='user', read_only=True)
    
    class Meta:
        model = Offer
        fields = [
            'id',
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
        """Return list of detail URLs."""
        request = self.context.get('request')
        details_list = []
        for detail in obj.details.all():
            if request:
                url = request.build_absolute_uri(f'/api/offerdetails/{detail.id}/')
            else:
                url = f'/offerdetails/{detail.id}/'
            details_list.append({'url': url})
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