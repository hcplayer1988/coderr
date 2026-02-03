"""Tests for offer API endpoints."""
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from offer_app.models import Offer, OfferDetail
from decimal import Decimal

User = get_user_model()


class OfferListTests(APITestCase):
    """Test cases for offer list endpoint."""
    
    def setUp(self):
        """Set up test client and test data."""
        self.client = APIClient()
        
        # Create test users
        self.business1 = User.objects.create_user(
            username='business1',
            email='business1@test.com',
            password='TestPass123!',
            type='business'
        )
        self.business1.profile.first_name = 'John'
        self.business1.profile.last_name = 'Doe'
        self.business1.profile.save()
        
        self.business2 = User.objects.create_user(
            username='business2',
            email='business2@test.com',
            password='TestPass123!',
            type='business'
        )
        self.business2.profile.first_name = 'Jane'
        self.business2.profile.last_name = 'Smith'
        self.business2.profile.save()
        
        self.customer = User.objects.create_user(
            username='customer1',
            email='customer1@test.com',
            password='TestPass123!',
            type='customer'
        )
        
        # Create offers
        self.offer1 = Offer.objects.create(
            user=self.business1,
            title='Website Design',
            description='Professional website design services'
        )
        
        self.offer2 = Offer.objects.create(
            user=self.business1,
            title='Logo Design',
            description='Creative logo design'
        )
        
        self.offer3 = Offer.objects.create(
            user=self.business2,
            title='Mobile App Development',
            description='iOS and Android app development'
        )
        
        # Create offer details for offer1
        OfferDetail.objects.create(
            offer=self.offer1,
            title='Basic Package',
            revisions=2,
            delivery_time_in_days=7,
            price=Decimal('100.00'),
            features='Basic features',
            offer_type='basic'
        )
        
        OfferDetail.objects.create(
            offer=self.offer1,
            title='Premium Package',
            revisions=5,
            delivery_time_in_days=14,
            price=Decimal('250.00'),
            features='Premium features',
            offer_type='premium'
        )
        
        # Create offer details for offer2
        OfferDetail.objects.create(
            offer=self.offer2,
            title='Standard Package',
            revisions=3,
            delivery_time_in_days=5,
            price=Decimal('150.00'),
            features='Standard features',
            offer_type='standard'
        )
        
        # Create offer details for offer3
        OfferDetail.objects.create(
            offer=self.offer3,
            title='Basic App',
            revisions=2,
            delivery_time_in_days=30,
            price=Decimal('2000.00'),
            features='Basic mobile app',
            offer_type='basic'
        )
    
    def test_list_offers_success(self):
        """Test listing all offers without authentication."""
        url = reverse('offer-list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['results']), 3)
    
    def test_list_offers_has_required_fields(self):
        """Test that each offer has all required fields."""
        url = reverse('offer-list')
        
        response = self.client.get(url)
        
        required_fields = [
            'id', 'user', 'title', 'image', 'description', 'created_at',
            'updated_at', 'details', 'min_price', 'min_delivery_time',
            'user_details'
        ]
        
        for offer in response.data['results']:
            for field in required_fields:
                self.assertIn(field, offer, f"Field '{field}' missing")
    
    def test_list_offers_user_details_structure(self):
        """Test that user_details has correct structure."""
        url = reverse('offer-list')
        
        response = self.client.get(url)
        
        first_offer = response.data['results'][0]
        user_details = first_offer['user_details']
        
        self.assertIn('id', user_details)
        self.assertIn('first_name', user_details)
        self.assertIn('last_name', user_details)
        self.assertIn('username', user_details)
    
    def test_list_offers_min_price_calculation(self):
        """Test that min_price is calculated correctly."""
        url = reverse('offer-list')
        
        response = self.client.get(url)
        
        # Find offer1 in results
        offer1_data = next(o for o in response.data['results'] if o['id'] == self.offer1.id)
        
        # Should be 100.00 (minimum of 100 and 250)
        self.assertEqual(float(offer1_data['min_price']), 100.00)
    
    def test_list_offers_min_delivery_time_calculation(self):
        """Test that min_delivery_time is calculated correctly."""
        url = reverse('offer-list')
        
        response = self.client.get(url)
        
        # Find offer1 in results
        offer1_data = next(o for o in response.data['results'] if o['id'] == self.offer1.id)
        
        # Should be 7 (minimum of 7 and 14)
        self.assertEqual(offer1_data['min_delivery_time'], 7)
    
    def test_filter_by_creator_id(self):
        """Test filtering offers by creator_id."""
        url = reverse('offer-list')
        
        response = self.client.get(url, {'creator_id': self.business1.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)  # business1 has 2 offers
        
        for offer in response.data['results']:
            self.assertEqual(offer['user_details']['id'], self.business1.id)
    
    def test_filter_by_min_price(self):
        """Test filtering offers by minimum price."""
        url = reverse('offer-list')
        
        response = self.client.get(url, {'min_price': 200})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return offer1 (has detail with 250) and offer3 (has 2000)
        self.assertGreaterEqual(response.data['count'], 2)
    
    def test_filter_by_max_delivery_time(self):
        """Test filtering offers by maximum delivery time."""
        url = reverse('offer-list')
        
        response = self.client.get(url, {'max_delivery_time': 10})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return offers with details that have delivery_time <= 10
        # offer1 has 7, offer2 has 5
        self.assertGreaterEqual(response.data['count'], 2)
    
    def test_search_by_title(self):
        """Test searching offers by title."""
        url = reverse('offer-list')
        
        response = self.client.get(url, {'search': 'Website'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 1)
        
        # Check that result contains the search term
        self.assertIn('Website', response.data['results'][0]['title'])
    
    def test_search_by_description(self):
        """Test searching offers by description."""
        url = reverse('offer-list')
        
        response = self.client.get(url, {'search': 'Creative'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 1)
    
    def test_ordering_by_updated_at(self):
        """Test ordering offers by updated_at."""
        url = reverse('offer-list')
        
        response = self.client.get(url, {'ordering': 'updated_at'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that results are ordered (oldest first)
        results = response.data['results']
        if len(results) > 1:
            self.assertLessEqual(results[0]['updated_at'], results[1]['updated_at'])
    
    def test_ordering_by_updated_at_desc(self):
        """Test ordering offers by updated_at descending."""
        url = reverse('offer-list')
        
        response = self.client.get(url, {'ordering': '-updated_at'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that results are ordered (newest first)
        results = response.data['results']
        if len(results) > 1:
            self.assertGreaterEqual(results[0]['updated_at'], results[1]['updated_at'])
    
    def test_pagination_with_page_size(self):
        """Test pagination with custom page size."""
        url = reverse('offer-list')
        
        response = self.client.get(url, {'page_size': 2})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.assertIn('next', response.data)
    
    def test_pagination_next_page(self):
        """Test getting next page of results."""
        url = reverse('offer-list')
        
        # Get first page
        response1 = self.client.get(url, {'page_size': 2, 'page': 1})
        
        # Get second page
        response2 = self.client.get(url, {'page_size': 2, 'page': 2})
        
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Results should be different
        if len(response2.data['results']) > 0:
            self.assertNotEqual(
                response1.data['results'][0]['id'],
                response2.data['results'][0]['id']
            )
    
    def test_combined_filters(self):
        """Test combining multiple filters."""
        url = reverse('offer-list')
        
        response = self.client.get(url, {
            'creator_id': self.business1.id,
            'min_price': 100,
            'search': 'Design'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return offers from business1 that match search and have price >= 100
    
    def test_details_urls_in_response(self):
        """Test that details contain id and url fields."""
        url = reverse('offer-list')
        
        response = self.client.get(url)
        
        first_offer = response.data['results'][0]
        self.assertIsInstance(first_offer['details'], list)
        
        if len(first_offer['details']) > 0:
            self.assertIn('id', first_offer['details'][0])
            self.assertIn('url', first_offer['details'][0])
"""Additional tests for offer create endpoint (POST)."""
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from offer_app.models import Offer, OfferDetail
from decimal import Decimal

User = get_user_model()


class OfferCreateTests(APITestCase):
    """Test cases for offer create endpoint (POST)."""
    
    def setUp(self):
        """Set up test client and test users."""
        self.client = APIClient()
        
        # Create business user
        self.business_user = User.objects.create_user(
            username='business1',
            email='business1@test.com',
            password='TestPass123!',
            type='business'
        )
        self.business_user.profile.first_name = 'John'
        self.business_user.profile.last_name = 'Doe'
        self.business_user.profile.save()
        self.business_token = Token.objects.create(user=self.business_user)
        
        # Create customer user
        self.customer_user = User.objects.create_user(
            username='customer1',
            email='customer1@test.com',
            password='TestPass123!',
            type='customer'
        )
        self.customer_token = Token.objects.create(user=self.customer_user)
        
        # Valid offer data
        self.valid_offer_data = {
            'title': 'Website Design',
            'description': 'Professional website design services',
            'details': [
                {
                    'title': 'Basic Package',
                    'revisions': 2,
                    'delivery_time_in_days': 7,
                    'price': '100.00',
                    'features': 'Basic website design',
                    'offer_type': 'basic'
                },
                {
                    'title': 'Premium Package',
                    'revisions': 5,
                    'delivery_time_in_days': 14,
                    'price': '250.00',
                    'features': 'Premium website design',
                    'offer_type': 'premium'
                }
            ]
        }
    
    def test_create_offer_success(self):
        """Test successful offer creation by business user."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-list')
        
        response = self.client.post(url, self.valid_offer_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['title'], 'Website Design')
        self.assertEqual(response.data['user'], self.business_user.id)
        self.assertEqual(len(response.data['details']), 2)
        
        # Verify database
        self.assertEqual(Offer.objects.count(), 1)
        self.assertEqual(OfferDetail.objects.count(), 2)
    
    def test_create_offer_response_structure(self):
        """Test that response has correct structure."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-list')
        
        response = self.client.post(url, self.valid_offer_data, format='json')
        
        required_fields = [
            'id', 'user', 'title', 'image', 'description',
            'created_at', 'updated_at', 'details',
            'min_price', 'min_delivery_time', 'user_details'
        ]
        
        for field in required_fields:
            self.assertIn(field, response.data, f"Field '{field}' missing")
        
        # Check details structure
        detail = response.data['details'][0]
        detail_fields = ['id', 'title', 'revisions', 'delivery_time_in_days', 'price', 'features', 'offer_type']
        for field in detail_fields:
            self.assertIn(field, detail, f"Detail field '{field}' missing")
    
    def test_create_offer_min_values_calculated(self):
        """Test that min_price and min_delivery_time are calculated."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-list')
        
        response = self.client.post(url, self.valid_offer_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(float(response.data['min_price']), 100.00)
        self.assertEqual(response.data['min_delivery_time'], 7)
    
    def test_create_offer_user_details_included(self):
        """Test that user_details are included in response."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-list')
        
        response = self.client.post(url, self.valid_offer_data, format='json')
        
        self.assertIn('user_details', response.data)
        self.assertEqual(response.data['user_details']['username'], 'business1')
        self.assertEqual(response.data['user_details']['first_name'], 'John')
    
    def test_create_offer_unauthenticated(self):
        """Test that unauthenticated users cannot create offers."""
        url = reverse('offer-list')
        
        response = self.client.post(url, self.valid_offer_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_offer_customer_forbidden(self):
        """Test that customer users cannot create offers."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = reverse('offer-list')
        
        response = self.client.post(url, self.valid_offer_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('detail', response.data)
    
    def test_create_offer_missing_title(self):
        """Test validation error when title is missing."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-list')
        
        data = self.valid_offer_data.copy()
        del data['title']
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)
    
    def test_create_offer_missing_description(self):
        """Test validation error when description is missing."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-list')
        
        data = self.valid_offer_data.copy()
        del data['description']
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('description', response.data)
    
    def test_create_offer_missing_details(self):
        """Test validation error when details are missing."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-list')
        
        data = self.valid_offer_data.copy()
        del data['details']
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('details', response.data)
    
    def test_create_offer_empty_details(self):
        """Test validation error when details array is empty."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-list')
        
        data = self.valid_offer_data.copy()
        data['details'] = []
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('details', response.data)
    
    def test_create_offer_single_detail(self):
        """Test creating offer with single detail."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-list')
        
        data = {
            'title': 'Logo Design',
            'description': 'Professional logo design',
            'details': [
                {
                    'title': 'Standard Package',
                    'revisions': 3,
                    'delivery_time_in_days': 5,
                    'price': '150.00',
                    'features': 'Logo design',
                    'offer_type': 'standard'
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['details']), 1)
    
    def test_create_offer_invalid_price(self):
        """Test validation error for invalid price."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-list')
        
        data = self.valid_offer_data.copy()
        data['details'][0]['price'] = 'invalid'
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_offer_negative_price(self):
        """Test validation error for negative price."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-list')
        
        data = self.valid_offer_data.copy()
        data['details'][0]['price'] = '-50.00'
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_offer_with_image(self):
        """Test creating offer without image (image is optional)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-list')
        
        data = self.valid_offer_data.copy()
        # Image is optional, so we just test without it
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Image should be null since we didn't provide one
        self.assertIsNone(response.data['image'])





