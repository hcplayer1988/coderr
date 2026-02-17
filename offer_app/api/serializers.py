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

    first_name = serializers.CharField(
        source='profile.first_name',
        read_only=True
    )
    last_name = serializers.CharField(
        source='profile.last_name',
        read_only=True
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username']


def parse_features(features_value):
    """
    Parse features into a proper Python list.

    Handles: list, JSON string, comma-separated string, single string.
    """
    if isinstance(features_value, list):
        return features_value

    if isinstance(features_value, str):
        stripped = features_value.strip()

        if stripped.startswith('[') and stripped.endswith(']'):
            import json
            try:
                parsed = json.loads(stripped)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
            except (ValueError, TypeError):
                pass

            import ast
            try:
                parsed = ast.literal_eval(stripped)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
            except (ValueError, SyntaxError):
                pass

        if stripped:
            return [f.strip() for f in stripped.split(',') if f.strip()]

    return []


class OfferDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for OfferDetail objects.

    Used for creating and displaying offer details.
    features is always returned as a list.
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
            raise serializers.ValidationError(
                "Delivery time must be positive."
            )
        return value

    def validate_revisions(self, value):
        """Validate that revisions is not negative."""
        if value < 0:
            raise serializers.ValidationError(
                "Revisions cannot be negative."
            )
        return value

    def to_representation(self, instance):
        """Ensure features is always returned as a list."""
        representation = super().to_representation(instance)
        representation['features'] = parse_features(
            representation.get('features')
        )
        representation['price'] = int(instance.price)
        return representation


class OfferDetailSingleSerializer(serializers.ModelSerializer):
    """
    Serializer for single OfferDetail retrieval.

    GET /api/offerdetails/{id}/
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
        """Convert features to list."""
        return parse_features(obj.features)

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
        """Convert features to list."""
        return parse_features(obj.features)

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
    price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False
    )
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
            raise serializers.ValidationError(
                "Delivery time must be positive."
            )
        return value

    def validate_revisions(self, value):
        """Validate that revisions is not negative."""
        if value is not None and value < 0:
            raise serializers.ValidationError(
                "Revisions cannot be negative."
            )
        return value

    def validate_features(self, value):
        """Store features as JSON list."""
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            return parse_features(value)
        return value


class OfferRetrieveSerializer(serializers.ModelSerializer):
    """
    Serializer for GET /api/offers/{id}/.

    Returns: id, user (int), title, image, description,
             created_at, updated_at, details[{id, url}],
             min_price, min_delivery_time.
    NO user_details.
    """

    user = serializers.IntegerField(source='user.id', read_only=True)
    details = serializers.SerializerMethodField()
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
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_details(self, obj):
        """Return list of details with id and url."""
        request = self.context.get('request')
        details_list = []
        for detail in obj.details.all():
            if request:
                url = request.build_absolute_uri(
                    f'/api/offerdetails/{detail.id}/'
                )
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
            representation['image'] = (
                instance.image.name if instance.image else None
            )
        else:
            representation['image'] = None
        return representation


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
                url = request.build_absolute_uri(
                    f'/api/offerdetails/{detail.id}/'
                )
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
            representation['image'] = (
                instance.image.name if instance.image else None
            )
        else:
            representation['image'] = None

        return representation


class OfferCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating offers.

    POST response matches specification exactly:
    - Only returns: id, title, image, description, details
    - features returned as list
    - price returned as integer
    """

    details = OfferDetailSerializer(many=True, write_only=True)

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

    def validate_details(self, value):
        """Validate that at least one detail is provided."""
        if not value:
            raise serializers.ValidationError(
                "At least one offer detail is required."
            )
        return value

    def create(self, validated_data):
        """Create offer with nested details."""
        details_data = validated_data.pop('details')

        offer = Offer.objects.create(**validated_data)

        for detail_data in details_data:
            if 'features' in detail_data:
                features = detail_data['features']
                if isinstance(features, str):
                    detail_data['features'] = parse_features(features)

            OfferDetail.objects.create(offer=offer, **detail_data)

        return offer

    def to_representation(self, instance):
        """
        Return response matching specification exactly.

        Only: id, title, image, description, details
        With features as list and price as integer.
        """
        details_queryset = instance.details.all()

        return {
            'id': instance.id,
            'title': instance.title,
            'image': instance.image.name if instance.image else None,
            'description': instance.description,
            'details': OfferDetailSerializer(
                details_queryset,
                many=True
            ).data
        }


class OfferUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating offers via PATCH.

    Response format matches specification exactly:
    - Only returns: id, title, image, description, details
    - features is returned as list
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

        Matches existing details by offer_type (basic/standard/premium).
        Never creates a 4th package — max 3 details allowed.
        """
        details_data = validated_data.pop('details', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if details_data is not None:
            allowed_types = ['basic', 'standard', 'premium']

            for detail_data in details_data:
                offer_type = detail_data.get('offer_type')
                detail_id = detail_data.get('id')

                if not offer_type:
                    raise serializers.ValidationError({
                        'details': (
                            "Each detail must include 'offer_type' "
                            "(basic, standard or premium)."
                        )
                    })

                if offer_type not in allowed_types:
                    raise serializers.ValidationError({
                        'details': (
                            f"Invalid offer_type '{offer_type}'. "
                            f"Must be one of: {', '.join(allowed_types)}."
                        )
                    })

                existing_detail = None

                if detail_id:
                    try:
                        existing_detail = OfferDetail.objects.get(
                            id=detail_id,
                            offer=instance
                        )
                    except OfferDetail.DoesNotExist:
                        pass

                if existing_detail is None:
                    try:
                        existing_detail = OfferDetail.objects.get(
                            offer=instance,
                            offer_type=offer_type
                        )
                    except OfferDetail.DoesNotExist:
                        pass

                if existing_detail is not None:
                    for attr, value in detail_data.items():
                        if attr != 'id':
                            setattr(existing_detail, attr, value)
                    existing_detail.save()
                else:
                    current_count = OfferDetail.objects.filter(
                        offer=instance
                    ).count()
                    if current_count >= 3:
                        raise serializers.ValidationError({
                            'details': (
                                "An offer can have at most 3 details "
                                "(basic, standard, premium). "
                                f"Offer already has {current_count} details."
                            )
                        })
                    detail_data_clean = {
                        k: v for k, v in detail_data.items() if k != 'id'
                    }
                    OfferDetail.objects.create(
                        offer=instance,
                        **detail_data_clean
                    )

        instance.refresh_from_db()

        return instance

    def to_representation(self, instance):
        """
        Return response matching specification exactly.

        Only: id, title, image, description, details
        With features as list and price as integer.
        """
        instance.refresh_from_db()

        details_queryset = OfferDetail.objects.filter(offer=instance)

        return {
            'id': instance.id,
            'title': instance.title,
            'image': instance.image.name if instance.image else None,
            'description': instance.description,
            'details': OfferDetailResponseSerializer(
                details_queryset,
                many=True
            ).data
        }
    

    