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
        
        if isinstance(features, list):
            return features
        
        if isinstance(features, str):
            if features.startswith('[') and features.endswith(']'):
                try:
                    import ast
                    return ast.literal_eval(features)
                except (ValueError, SyntaxError):
                    pass
            
            try:
                parsed = json.loads(features)
                if isinstance(parsed, list):
                    return parsed
                elif isinstance(parsed, str):
                    return json.loads(parsed)
                else:
                    return [parsed]
            except (json.JSONDecodeError, TypeError, ValueError):
                return [features]
        
        return []


class OrderUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating order status.
    Only allows updating the status field.
    Returns updated order with updated_at timestamp.
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
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'customer_user',
            'business_user',
            'title',
            'revisions',
            'delivery_time_in_days',
            'price',
            'features',
            'offer_type',
            'created_at',
            'updated_at'
        ]
    
    def get_features(self, obj):
        """Ensure features is returned as a list."""
        features = obj.features
        
        if isinstance(features, list):
            return features
        
        if isinstance(features, str):
            if features.startswith('[') and features.endswith(']'):
                try:
                    import ast
                    return ast.literal_eval(features)
                except (ValueError, SyntaxError):
                    pass
            
            try:
                parsed = json.loads(features)
                if isinstance(parsed, list):
                    return parsed
                elif isinstance(parsed, str):
                    return json.loads(parsed)
                else:
                    return [parsed]
            except (json.JSONDecodeError, TypeError, ValueError):
                return [features]
        
        return []
    
    def validate_status(self, value):
        """Validate that status is one of the allowed choices."""
        allowed_statuses = ['in_progress', 'completed', 'cancelled']
        if value not in allowed_statuses:
            raise serializers.ValidationError(
                f"Invalid status. Must be one of: {', '.join(allowed_statuses)}"
            )
        return value


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
            self.offer_detail = offer_detail
            return value
        except OfferDetail.DoesNotExist:
            raise serializers.ValidationError("Offer detail not found.")
    
    def create(self, validated_data):
        """Create order from offer detail."""
        offer_detail = self.offer_detail
        customer_user = self.context['request'].user
        business_user = offer_detail.offer.user
        
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


