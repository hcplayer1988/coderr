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
        
        OfferDetail.objects.create(
            offer=self.offer2,
            title='Standard Package',
            revisions=3,
            delivery_time_in_days=5,
            price=Decimal('150.00'),
            features='Standard features',
            offer_type='standard'
        )
        
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
        
        offer1_data = next(o for o in response.data['results'] if o['id'] == self.offer1.id)
        
        self.assertEqual(float(offer1_data['min_price']), 100.00)
    
    def test_list_offers_min_delivery_time_calculation(self):
        """Test that min_delivery_time is calculated correctly."""
        url = reverse('offer-list')
        
        response = self.client.get(url)
        
        offer1_data = next(o for o in response.data['results'] if o['id'] == self.offer1.id)
        
        self.assertEqual(offer1_data['min_delivery_time'], 7)
    
    def test_filter_by_creator_id(self):
        """Test filtering offers by creator_id."""
        url = reverse('offer-list')
        
        response = self.client.get(url, {'creator_id': self.business1.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        
        for offer in response.data['results']:
            self.assertEqual(offer['user_details']['id'], self.business1.id)
    
    def test_filter_by_min_price(self):
        """Test filtering offers by minimum price."""
        url = reverse('offer-list')
        
        response = self.client.get(url, {'min_price': 200})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 2)
    
    def test_filter_by_max_delivery_time(self):
        """Test filtering offers by maximum delivery time."""
        url = reverse('offer-list')
        
        response = self.client.get(url, {'max_delivery_time': 10})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 2)
    
    def test_search_by_title(self):
        """Test searching offers by title."""
        url = reverse('offer-list')
        
        response = self.client.get(url, {'search': 'Website'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 1)
        
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
        
        results = response.data['results']
        if len(results) > 1:
            self.assertLessEqual(results[0]['updated_at'], results[1]['updated_at'])
    
    def test_ordering_by_updated_at_desc(self):
        """Test ordering offers by updated_at descending."""
        url = reverse('offer-list')
        
        response = self.client.get(url, {'ordering': '-updated_at'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
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
        
        response1 = self.client.get(url, {'page_size': 2, 'page': 1})
        
        response2 = self.client.get(url, {'page_size': 2, 'page': 2})
        
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
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
    
    def test_details_urls_in_response(self):
        """Test that details contain id and url fields."""
        url = reverse('offer-list')
        
        response = self.client.get(url)
        
        first_offer = response.data['results'][0]
        self.assertIsInstance(first_offer['details'], list)
        
        if len(first_offer['details']) > 0:
            self.assertIn('id', first_offer['details'][0])
            self.assertIn('url', first_offer['details'][0])


class OfferCreateTests(APITestCase):
    """Test cases for offer create endpoint (POST)."""
    
    def setUp(self):
        """Set up test client and test users."""
        self.client = APIClient()
        
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
        
        self.customer_user = User.objects.create_user(
            username='customer1',
            email='customer1@test.com',
            password='TestPass123!',
            type='customer'
        )
        self.customer_token = Token.objects.create(user=self.customer_user)
        
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
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data['image'])


class OfferDetailViewTests(APITestCase):
    """Test cases for single offer detail endpoint."""
    
    def setUp(self):
        """Set up test client and test data."""
        self.client = APIClient()
        
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
        
        self.customer_user = User.objects.create_user(
            username='customer1',
            email='customer1@test.com',
            password='TestPass123!',
            type='customer'
        )
        self.customer_token = Token.objects.create(user=self.customer_user)
        
        self.offer = Offer.objects.create(
            user=self.business_user,
            title='Grafikdesign-Paket',
            description='Ein umfassendes Grafikdesign-Paket für Unternehmen'
        )
        
        self.detail1 = OfferDetail.objects.create(
            offer=self.offer,
            title='Basic Package',
            revisions=2,
            delivery_time_in_days=5,
            price=Decimal('50.00'),
            features='Basic design',
            offer_type='basic'
        )
        
        self.detail2 = OfferDetail.objects.create(
            offer=self.offer,
            title='Premium Package',
            revisions=5,
            delivery_time_in_days=10,
            price=Decimal('200.00'),
            features='Premium design',
            offer_type='premium'
        )
        
        self.detail3 = OfferDetail.objects.create(
            offer=self.offer,
            title='Enterprise Package',
            revisions=10,
            delivery_time_in_days=15,
            price=Decimal('201.00'),
            features='Enterprise design',
            offer_type='enterprise'
        )
    
    def test_get_offer_detail_success(self):
        """Test successfully retrieving a single offer."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.offer.id)
        self.assertEqual(response.data['title'], 'Grafikdesign-Paket')
        self.assertEqual(response.data['user'], self.business_user.id)
    
    def test_get_offer_detail_has_all_fields(self):
        """Test that response contains all required fields."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        
        response = self.client.get(url)
        
        required_fields = [
            'id', 'user', 'title', 'image', 'description',
            'created_at', 'updated_at', 'details',
            'min_price', 'min_delivery_time'
        ]
        
        for field in required_fields:
            self.assertIn(field, response.data, f"Field '{field}' missing")
    
    def test_get_offer_detail_has_details_array(self):
        """Test that details array contains id and url."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        
        response = self.client.get(url)
        
        self.assertIsInstance(response.data['details'], list)
        self.assertEqual(len(response.data['details']), 3)
        
        for detail in response.data['details']:
            self.assertIn('id', detail)
            self.assertIn('url', detail)
    
    def test_get_offer_detail_min_values(self):
        """Test that min_price and min_delivery_time are calculated correctly."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        
        response = self.client.get(url)
        
        self.assertEqual(float(response.data['min_price']), 50.00)
        self.assertEqual(response.data['min_delivery_time'], 5)
    
    def test_get_offer_detail_unauthenticated(self):
        """Test that unauthenticated users cannot access offer details."""
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_offer_detail_not_found(self):
        """Test 404 response for non-existent offer."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': 99999})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_offer_detail_customer_can_view(self):
        """Test that customer users can view offer details."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.offer.id)
    
    def test_get_offer_detail_another_business_can_view(self):
        """Test that other business users can view offers."""
        other_business = User.objects.create_user(
            username='business2',
            email='business2@test.com',
            password='TestPass123!',
            type='business'
        )
        other_token = Token.objects.create(user=other_business)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {other_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class OfferUpdateTests(APITestCase):
    """Test cases for offer update endpoint (PATCH)."""
    
    def setUp(self):
        """Set up test client and test data."""
        self.client = APIClient()
        
        # Business user (owner)
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
        
        # Another business user (not owner)
        self.other_business = User.objects.create_user(
            username='business2',
            email='business2@test.com',
            password='TestPass123!',
            type='business'
        )
        self.other_business_token = Token.objects.create(user=self.other_business)
        
        # Customer user
        self.customer_user = User.objects.create_user(
            username='customer1',
            email='customer1@test.com',
            password='TestPass123!',
            type='customer'
        )
        self.customer_token = Token.objects.create(user=self.customer_user)
        
        # Create offer with details
        self.offer = Offer.objects.create(
            user=self.business_user,
            title='Grafikdesign-Paket',
            description='Ein umfassendes Grafikdesign-Paket für Unternehmen'
        )
        
        self.detail1 = OfferDetail.objects.create(
            offer=self.offer,
            title='Basic Design',
            revisions=3,
            delivery_time_in_days=6,
            price=Decimal('120.00'),
            features='Logo Design, Flyer',
            offer_type='basic'
        )
        
        self.detail2 = OfferDetail.objects.create(
            offer=self.offer,
            title='Standard Design',
            revisions=5,
            delivery_time_in_days=10,
            price=Decimal('120.00'),
            features='Logo Design, Visitenkarte, Briefpapier',
            offer_type='standard'
        )
        
        self.detail3 = OfferDetail.objects.create(
            offer=self.offer,
            title='Premium Design',
            revisions=10,
            delivery_time_in_days=10,
            price=Decimal('150.00'),
            features='Logo Design, Visitenkarte, Briefpapier, Flyer',
            offer_type='premium'
        )
    
    def test_update_offer_title_success(self):
        """Test successfully updating only offer title."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        
        data = {
            'title': 'Updated Grafikdesign-Paket'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Grafikdesign-Paket')
        self.assertEqual(response.data['description'], self.offer.description)
        
        # Verify in database
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.title, 'Updated Grafikdesign-Paket')
    
    def test_update_offer_description_success(self):
        """Test successfully updating only offer description."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        
        data = {
            'description': 'Updated description'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Updated description')
        self.assertEqual(response.data['title'], self.offer.title)
    
    def test_update_offer_title_and_description(self):
        """Test updating both title and description."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        
        data = {
            'title': 'New Title',
            'description': 'New Description'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'New Title')
        self.assertEqual(response.data['description'], 'New Description')
    
    def test_update_single_detail_field(self):
        """Test updating a single field in one detail."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        
        data = {
            'title': 'Updated Grafikdesign-Paket',
            'details': [
                {
                    'id': self.detail1.id,
                    'title': 'Basic Design Updated',
                    'revisions': 3,
                    'delivery_time_in_days': 6,
                    'price': '120.00',
                    'features': 'Logo Design, Flyer',
                    'offer_type': 'basic'
                }
            ]
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Grafikdesign-Paket')
        
        # Find updated detail
        updated_detail = next(d for d in response.data['details'] if d['id'] == self.detail1.id)
        self.assertEqual(updated_detail['title'], 'Basic Design Updated')
        
        # Verify other details unchanged
        self.assertEqual(len(response.data['details']), 3)
    
    def test_update_multiple_details(self):
        """Test updating multiple details at once."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        
        data = {
            'details': [
                {
                    'id': self.detail1.id,
                    'title': 'Basic Design Updated',
                    'revisions': 5,
                    'delivery_time_in_days': 8,
                    'price': '150.00',
                    'features': 'Logo Design, Flyer, Poster',
                    'offer_type': 'basic'
                },
                {
                    'id': self.detail2.id,
                    'title': 'Standard Design Updated',
                    'revisions': 7,
                    'delivery_time_in_days': 12,
                    'price': '200.00',
                    'features': 'Logo Design, Visitenkarte, Briefpapier, Flyer',
                    'offer_type': 'standard'
                }
            ]
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Find updated details
        detail1 = next(d for d in response.data['details'] if d['id'] == self.detail1.id)
        detail2 = next(d for d in response.data['details'] if d['id'] == self.detail2.id)
        
        self.assertEqual(detail1['title'], 'Basic Design Updated')
        self.assertEqual(detail1['revisions'], 5)
        self.assertEqual(detail2['title'], 'Standard Design Updated')
        self.assertEqual(detail2['revisions'], 7)
    
    def test_update_offer_response_structure(self):
        """Test that response has correct structure."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        
        data = {'title': 'Updated Title'}
        
        response = self.client.patch(url, data, format='json')
        
        required_fields = [
            'id', 'user', 'title', 'image', 'description',
            'created_at', 'updated_at', 'details',
            'min_price', 'min_delivery_time', 'user_details'
        ]
        
        for field in required_fields:
            self.assertIn(field, response.data, f"Field '{field}' missing")
    
    def test_update_offer_min_values_recalculated(self):
        """Test that min_price and min_delivery_time are recalculated after update."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        
        data = {
            'details': [
                {
                    'id': self.detail1.id,
                    'title': 'Basic Design',
                    'revisions': 3,
                    'delivery_time_in_days': 3,
                    'price': '50.00',
                    'features': 'Logo Design',
                    'offer_type': 'basic'
                }
            ]
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['min_price']), 50.00)
        self.assertEqual(response.data['min_delivery_time'], 3)
    
    def test_update_offer_unauthenticated(self):
        """Test that unauthenticated users cannot update offers."""
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        
        data = {'title': 'Updated Title'}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_update_offer_not_owner_forbidden(self):
        """Test that non-owners cannot update offers."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.other_business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        
        data = {'title': 'Updated Title'}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_update_offer_customer_forbidden(self):
        """Test that customer users cannot update offers."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        
        data = {'title': 'Updated Title'}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_update_offer_not_found(self):
        """Test 404 response for non-existent offer."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': 99999})
        
        data = {'title': 'Updated Title'}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_detail_with_invalid_id(self):
        """Test error when trying to update detail with non-existent id."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        
        data = {
            'details': [
                {
                    'id': 99999,
                    'title': 'Invalid Detail',
                    'revisions': 3,
                    'delivery_time_in_days': 5,
                    'price': '100.00',
                    'features': 'Test',
                    'offer_type': 'basic'
                }
            ]
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('details', response.data)
    
    def test_update_offer_empty_title(self):
        """Test validation error for empty title."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        
        data = {'title': ''}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_update_detail_negative_price(self):
        """Test validation error for negative price in detail."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        
        data = {
            'details': [
                {
                    'id': self.detail1.id,
                    'title': 'Basic Design',
                    'revisions': 3,
                    'delivery_time_in_days': 6,
                    'price': '-50.00',
                    'features': 'Logo Design',
                    'offer_type': 'basic'
                }
            ]
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_update_detail_zero_delivery_time(self):
        """Test validation error for zero delivery time."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        
        data = {
            'details': [
                {
                    'id': self.detail1.id,
                    'title': 'Basic Design',
                    'revisions': 3,
                    'delivery_time_in_days': 0,
                    'price': '100.00',
                    'features': 'Logo Design',
                    'offer_type': 'basic'
                }
            ]
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_update_offer_user_field_ignored(self):
        """Test that user field cannot be changed."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        
        data = {
            'title': 'Updated Title',
            'user': self.other_business.id
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user'], self.business_user.id)
        
        # Verify in database
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.user.id, self.business_user.id)
    
    def test_update_offer_details_unchanged_when_not_provided(self):
        """Test that details remain unchanged when not provided in update."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        
        # Get initial details count
        initial_details_count = OfferDetail.objects.filter(offer=self.offer).count()
        
        data = {'title': 'Updated Title Only'}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['details']), initial_details_count)
        self.assertEqual(OfferDetail.objects.filter(offer=self.offer).count(), initial_details_count)
        
