"""Serializers for order API endpoints."""
from rest_framework import serializers
from order_app.models import Order
from offer_app.models import OfferDetail
import json


class OrderListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing orders.
    Returns orders that the authenticated user is involved in (as customer or business).
    """
    
    features = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id',
            'customer_user',
            'business_user',
            'title',
            'revisions',
            'delivery_time_in_days',
            'price',
            'features',
            'offer_type',
            'status',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_features(self, obj):
        """Ensure features is returned as a list."""
        features = obj.features
        
        # If it's already a list, return it
        if isinstance(features, list):
            return features
        
        # If it's a string, we need to handle it
        if isinstance(features, str):
            # Check if it's a string representation of a Python list (e.g., "['item1', 'item2']")
            if features.startswith('[') and features.endswith(']'):
                try:
                    # Use ast.literal_eval for safe evaluation of Python literals
                    import ast
                    return ast.literal_eval(features)
                except (ValueError, SyntaxError):
                    pass
            
            # Try JSON parsing
            try:
                parsed = json.loads(features)
                if isinstance(parsed, list):
                    return parsed
                elif isinstance(parsed, str):
                    # Double-stringified - try again
                    return json.loads(parsed)
                else:
                    return [parsed]
            except (json.JSONDecodeError, TypeError, ValueError):
                return [features]
        
        # Default: return empty list
        return []


class OrderCreateSerializer(serializers.Serializer):
    """
    Serializer for creating orders from an OfferDetail.
    Only requires offer_detail_id.
    """
    
    offer_detail_id = serializers.IntegerField(required=True)
    
    def validate_offer_detail_id(self, value):
        """Validate that the offer_detail exists."""
        try:
            offer_detail = OfferDetail.objects.select_related('offer__user').get(id=value)
            # Store for later use in create()
            self.offer_detail = offer_detail
            return value
        except OfferDetail.DoesNotExist:
            raise serializers.ValidationError("Offer detail not found.")
    
    def create(self, validated_data):
        """Create order from offer detail."""
        offer_detail = self.offer_detail
        customer_user = self.context['request'].user
        business_user = offer_detail.offer.user
        
        # Create order with data from offer_detail
        order = Order.objects.create(
            customer_user=customer_user,
            business_user=business_user,
            title=offer_detail.title,
            revisions=offer_detail.revisions,
            delivery_time_in_days=offer_detail.delivery_time_in_days,
            price=offer_detail.price,
            features=offer_detail.features,
            offer_type=offer_detail.offer_type,
            status='in_progress'
        )
        
        return order
    
    def to_representation(self, instance):
        """Return full order data using OrderListSerializer."""
        return OrderListSerializer(instance).data

