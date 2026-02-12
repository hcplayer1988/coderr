"""Views for general API endpoints."""
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Avg
from reviews_app.models import Review
from offer_app.models import Offer
from .serializers import BaseInfoSerializer

User = get_user_model()


class BaseInfoView(generics.GenericAPIView):
    """
    API endpoint to get base platform information.
    
    GET /api/base-info/
    Returns statistics about the platform (reviews, ratings, users, offers).
    No authentication required.
    """
    
    serializer_class = BaseInfoSerializer
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        Get base platform information.
        
        Returns:
            200: Platform statistics
            500: Internal server error
        """
        try:
            review_count = Review.objects.count()
            
            avg_rating = Review.objects.aggregate(Avg('rating'))['rating__avg']
            average_rating = round(avg_rating, 1) if avg_rating else 0.0
            
            business_profile_count = User.objects.filter(type='business').count()
            
            offer_count = Offer.objects.count()
            
            data = {
                'review_count': review_count,
                'average_rating': average_rating,
                'business_profile_count': business_profile_count,
                'offer_count': offer_count
            }
            
            serializer = self.get_serializer(data)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': 'Internal server error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
