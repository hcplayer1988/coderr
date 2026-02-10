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
    
    features = serializers.JSONField()
    
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


class OfferDetailSingleSerializer(serializers.ModelSerializer):
    """
    Serializer for single OfferDetail retrieval (GET /api/offerdetails/{id}/).
    Returns features as array and price as integer per specification.
    """
    
    features = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    
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
    
    def get_features(self, obj):
        """Convert features string to array."""
        if obj.features:
            return [f.strip() for f in obj.features.split(',') if f.strip()]
        return []
    
    def get_price(self, obj):
        """Return price as integer."""
        return int(obj.price)


class OfferDetailResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for OfferDetail in PATCH responses.
    Returns features as array and price as integer per specification.
    """
    
    features = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    
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
    
    def get_features(self, obj):
        """Convert features string to array."""
        if obj.features:
            return [f.strip() for f in obj.features.split(',') if f.strip()]
        return []
    
    def get_price(self, obj):
        """Return price as integer."""
        return int(obj.price)


class OfferDetailUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating OfferDetail objects.
    Uses explicit field definitions to ensure id is properly handled.
    Accepts features as either string or array.
    """
    
    id = serializers.IntegerField(required=False, allow_null=True)
    title = serializers.CharField(max_length=200, required=False)
    revisions = serializers.IntegerField(required=False)
    delivery_time_in_days = serializers.IntegerField(required=False)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    features = serializers.JSONField(required=False)
    offer_type = serializers.CharField(max_length=50, required=False)
    
    def validate_price(self, value):
        """Validate that price is not negative."""
        if value is not None and value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value
    
    def validate_delivery_time_in_days(self, value):
        """Validate that delivery time is positive."""
        if value is not None and value <= 0:
            raise serializers.ValidationError("Delivery time must be positive.")
        return value
    
    def validate_revisions(self, value):
        """Validate that revisions is not negative."""
        if value is not None and value < 0:
            raise serializers.ValidationError("Revisions cannot be negative.")
        return value
    
    def validate_features(self, value):
        """Convert features array to comma-separated string for storage."""
        if isinstance(value, list):
            return ', '.join(value)
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
                url = f'/api/offerdetails/{detail.id}/'
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
        
        offer = Offer.objects.create(**validated_data)
        
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
        
        details_queryset = instance.details.all()
        representation['details'] = OfferDetailSerializer(details_queryset, many=True).data
        
        if representation.get('image'):
            representation['image'] = instance.image.name if instance.image else None
        else:
            representation['image'] = None
        
        return representation


class OfferUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating offers via PATCH.
    Accepts partial updates for offer and nested details.
    
    Response format matches specification exactly:
    - Only returns: id, title, image, description, details
    - features is returned as array
    - price is returned as integer
    """
    
    details = OfferDetailUpdateSerializer(many=True, required=False)
    
    class Meta:
        model = Offer
        fields = [
            'id',
            'title',
            'image',
            'description',
            'details',
        ]
        read_only_fields = ['id']
    
    def update(self, instance, validated_data):
        """
        Update offer and nested details.
        Only updates fields that are provided in the request.
        """
        details_data = validated_data.pop('details', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if details_data is not None:
            for detail_data in details_data:
                detail_id = detail_data.get('id')
                
                if detail_id:
                    try:
                        detail = OfferDetail.objects.get(id=detail_id, offer=instance)
                        
                        for attr, value in detail_data.items():
                            if attr != 'id':
                                setattr(detail, attr, value)
                        detail.save()
                        
                    except OfferDetail.DoesNotExist:
                        raise serializers.ValidationError({
                            'details': f"OfferDetail with id {detail_id} does not exist for this offer."
                        })
                else:
                    OfferDetail.objects.create(offer=instance, **detail_data)
        
        instance.refresh_from_db()
        
        return instance
    
    def to_representation(self, instance):
        """
        Return response matching specification exactly.
        Only: id, title, image, description, details
        With features as array and price as integer.
        """
        instance.refresh_from_db()
        
        details_queryset = OfferDetail.objects.filter(offer=instance)
        
        return {
            'id': instance.id,
            'title': instance.title,
            'image': instance.image.name if instance.image else None,
            'description': instance.description,
            'details': OfferDetailResponseSerializer(details_queryset, many=True).data
        }
    

    