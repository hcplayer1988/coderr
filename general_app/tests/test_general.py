"""Tests for general API endpoints."""
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from reviews_app.models import Review
from offer_app.models import Offer, OfferDetail
from decimal import Decimal

User = get_user_model()


class BaseInfoTests(APITestCase):
    """Test GET /api/base-info/ endpoint."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data."""
        cls.business1 = User.objects.create_user(
            username='business1',
            email='business1@test.com',
            password='TestPass123!',
            type='business'
        )
        
        cls.business2 = User.objects.create_user(
            username='business2',
            email='business2@test.com',
            password='TestPass123!',
            type='business'
        )
        
        cls.business3 = User.objects.create_user(
            username='business3',
            email='business3@test.com',
            password='TestPass123!',
            type='business'
        )
        
        cls.customer1 = User.objects.create_user(
            username='customer1',
            email='customer1@test.com',
            password='TestPass123!',
            type='customer'
        )
        
        cls.customer2 = User.objects.create_user(
            username='customer2',
            email='customer2@test.com',
            password='TestPass123!',
            type='customer'
        )
        
        Review.objects.create(
            business_user=cls.business1,
            reviewer=cls.customer1,
            rating=5,
            description='Excellent!'
        )
        
        Review.objects.create(
            business_user=cls.business1,
            reviewer=cls.customer2,
            rating=4,
            description='Very good'
        )
        
        Review.objects.create(
            business_user=cls.business2,
            reviewer=cls.customer1,
            rating=5,
            description='Great work'
        )
        
        offer1 = Offer.objects.create(
            user=cls.business1,
            title='Web Development',
            description='Professional web development services'
        )
        
        OfferDetail.objects.create(
            offer=offer1,
            title='Basic Package',
            revisions=3,
            delivery_time_in_days=7,
            price=Decimal('299.99'),
            features=['Responsive Design', 'SEO'],
            offer_type='basic'
        )
        
        offer2 = Offer.objects.create(
            user=cls.business2,
            title='Logo Design',
            description='Creative logo design'
        )
        
        OfferDetail.objects.create(
            offer=offer2,
            title='Standard Package',
            revisions=5,
            delivery_time_in_days=5,
            price=Decimal('199.99'),
            features=['Logo', 'Business Card'],
            offer_type='standard'
        )
    
    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
    
    def test_base_info_success(self):
        """Test getting base info successfully."""
        response = self.client.get(reverse('base-info'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['review_count'], 3)
        self.assertEqual(float(response.data['average_rating']), 4.7)
        self.assertEqual(response.data['business_profile_count'], 3)
        self.assertEqual(response.data['offer_count'], 2)
    
    def test_base_info_no_authentication_required(self):
        """Test that no authentication is required."""
        response = self.client.get(reverse('base-info'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('review_count', response.data)
    
    def test_base_info_has_all_fields(self):
        """Test that response contains all required fields."""
        response = self.client.get(reverse('base-info'))
        
        required_fields = [
            'review_count',
            'average_rating',
            'business_profile_count',
            'offer_count'
        ]
        
        for field in required_fields:
            self.assertIn(field, response.data)
    
    def test_base_info_average_rating_rounded(self):
        """Test that average rating is rounded to 1 decimal place."""
        response = self.client.get(reverse('base-info'))
        
        self.assertEqual(float(response.data['average_rating']), 4.7)
    
    def test_base_info_empty_database(self):
        """Test base info when database is empty."""
        Review.objects.all().delete()
        Offer.objects.all().delete()
        User.objects.filter(type='business').delete()
        
        response = self.client.get(reverse('base-info'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['review_count'], 0)
        self.assertEqual(float(response.data['average_rating']), 0.0)
        self.assertEqual(response.data['business_profile_count'], 0)
        self.assertEqual(response.data['offer_count'], 0)
    
    def test_base_info_field_types(self):
        """Test that fields have correct data types."""
        response = self.client.get(reverse('base-info'))
        
        self.assertIsInstance(response.data['review_count'], int)
        self.assertIsInstance(response.data['business_profile_count'], int)
        self.assertIsInstance(response.data['offer_count'], int)
        self.assertIsInstance(response.data['average_rating'], float)
        

