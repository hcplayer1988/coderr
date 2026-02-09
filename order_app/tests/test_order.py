"""Tests for order list endpoint (GET /api/orders/)."""
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from order_app.models import Order
from offer_app.models import Offer, OfferDetail
from decimal import Decimal

User = get_user_model()


class OrderListTests(APITestCase):
    """Test cases for order list endpoint."""
    
    def setUp(self):
        """Set up test client and test data."""
        self.client = APIClient()
        
        # Create customer user
        self.customer_user = User.objects.create_user(
            username='customer1',
            email='customer1@test.com',
            password='TestPass123!',
            type='customer'
        )
        self.customer_token = Token.objects.create(user=self.customer_user)
        
        # Create business user 1
        self.business_user1 = User.objects.create_user(
            username='business1',
            email='business1@test.com',
            password='TestPass123!',
            type='business'
        )
        self.business_token1 = Token.objects.create(user=self.business_user1)
        
        # Create business user 2
        self.business_user2 = User.objects.create_user(
            username='business2',
            email='business2@test.com',
            password='TestPass123!',
            type='business'
        )
        self.business_token2 = Token.objects.create(user=self.business_user2)
        
        # Create orders for customer1 with business1
        self.order1 = Order.objects.create(
            customer_user=self.customer_user,
            business_user=self.business_user1,
            title='Logo Design',
            revisions=3,
            delivery_time_in_days=5,
            price=Decimal('150.00'),
            features=['Logo Design', 'Visitenkarten'],
            offer_type='basic',
            status='in_progress'
        )
        
        self.order2 = Order.objects.create(
            customer_user=self.customer_user,
            business_user=self.business_user1,
            title='Website Development',
            revisions=5,
            delivery_time_in_days=14,
            price=Decimal('500.00'),
            features=['Website', 'SEO'],
            offer_type='premium',
            status='completed'
        )
        
        # Create order with business2 (should not be visible to customer1 or business1)
        self.order3 = Order.objects.create(
            customer_user=self.customer_user,
            business_user=self.business_user2,
            title='Mobile App',
            revisions=10,
            delivery_time_in_days=30,
            price=Decimal('2000.00'),
            features=['iOS App', 'Android App'],
            offer_type='premium',
            status='in_progress'
        )
    
    def test_list_orders_success_customer(self):
        """Test listing orders as customer user."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = reverse('order-list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # Customer sees all 3 orders
    
    def test_list_orders_success_business(self):
        """Test listing orders as business user."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token1.key}')
        url = reverse('order-list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Business1 sees only their 2 orders
    
    def test_list_orders_unauthenticated(self):
        """Test that unauthenticated users cannot list orders."""
        url = reverse('order-list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_orders_has_required_fields(self):
        """Test that each order has all required fields."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = reverse('order-list')
        
        response = self.client.get(url)
        
        required_fields = [
            'id', 'customer_user', 'business_user', 'title',
            'revisions', 'delivery_time_in_days', 'price',
            'features', 'offer_type', 'status',
            'created_at', 'updated_at'
        ]
        
        for order in response.data:
            for field in required_fields:
                self.assertIn(field, order)
    
    def test_list_orders_correct_data(self):
        """Test that order data is correct."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = reverse('order-list')
        
        response = self.client.get(url)
        
        # Find order1 in response
        order1_data = next(o for o in response.data if o['id'] == self.order1.id)
        
        self.assertEqual(order1_data['title'], 'Logo Design')
        self.assertEqual(order1_data['customer_user'], self.customer_user.id)
        self.assertEqual(order1_data['business_user'], self.business_user1.id)
        self.assertEqual(order1_data['revisions'], 3)
        self.assertEqual(order1_data['delivery_time_in_days'], 5)
        self.assertEqual(float(order1_data['price']), 150.00)
        self.assertEqual(order1_data['features'], ['Logo Design', 'Visitenkarten'])
        self.assertEqual(order1_data['offer_type'], 'basic')
        self.assertEqual(order1_data['status'], 'in_progress')
    
    def test_list_orders_filtered_by_user(self):
        """Test that users only see their own orders."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token2.key}')
        url = reverse('order-list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Business2 sees only their 1 order
        self.assertEqual(response.data[0]['id'], self.order3.id)
    
    def test_list_orders_empty_for_new_user(self):
        """Test that new user with no orders gets empty list."""
        new_user = User.objects.create_user(
            username='newuser',
            email='new@test.com',
            password='TestPass123!',
            type='customer'
        )
        new_token = Token.objects.create(user=new_user)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {new_token.key}')
        url = reverse('order-list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
    
    def test_list_orders_ordering(self):
        """Test that orders are ordered by created_at (newest first)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = reverse('order-list')
        
        response = self.client.get(url)
        
        # Order3 was created last, so it should be first
        self.assertEqual(response.data[0]['id'], self.order3.id)


class OrderCreateTests(APITestCase):
    """Test cases for order create endpoint."""
    
    def setUp(self):
        """Set up test client and test data."""
        self.client = APIClient()
        
        # Create customer user
        self.customer_user = User.objects.create_user(
            username='customer1',
            email='customer1@test.com',
            password='TestPass123!',
            type='customer'
        )
        self.customer_token = Token.objects.create(user=self.customer_user)
        
        # Create business user
        self.business_user = User.objects.create_user(
            username='business1',
            email='business1@test.com',
            password='TestPass123!',
            type='business'
        )
        self.business_token = Token.objects.create(user=self.business_user)
        
        # Create offer
        self.offer = Offer.objects.create(
            user=self.business_user,
            title='Logo Design Package',
            description='Professional logo design'
        )
        
        # Create offer detail
        self.offer_detail = OfferDetail.objects.create(
            offer=self.offer,
            title='Basic Package',
            revisions=3,
            delivery_time_in_days=5,
            price=Decimal('150.00'),
            features=['Logo Design', 'Visitenkarten'],
            offer_type='basic'
        )
    
    def test_create_order_success(self):
        """Test successful order creation."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = reverse('order-list')
        
        data = {
            'offer_detail_id': self.offer_detail.id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['customer_user'], self.customer_user.id)
        self.assertEqual(response.data['business_user'], self.business_user.id)
        self.assertEqual(response.data['title'], 'Basic Package')
        self.assertEqual(response.data['revisions'], 3)
        self.assertEqual(response.data['delivery_time_in_days'], 5)
        self.assertEqual(float(response.data['price']), 150.00)
        
        # Features should be a list after serializer processing
        self.assertIsInstance(response.data['features'], list)
        self.assertEqual(response.data['features'], ['Logo Design', 'Visitenkarten'])
        
        self.assertEqual(response.data['offer_type'], 'basic')
        self.assertEqual(response.data['status'], 'in_progress')
    
    def test_create_order_unauthenticated(self):
        """Test that unauthenticated users cannot create orders."""
        url = reverse('order-list')
        
        data = {
            'offer_detail_id': self.offer_detail.id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_order_business_user_forbidden(self):
        """Test that business users cannot create orders."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('order-list')
        
        data = {
            'offer_detail_id': self.offer_detail.id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('customer', response.data['detail'].lower())
    
    def test_create_order_missing_offer_detail_id(self):
        """Test validation error when offer_detail_id is missing."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = reverse('order-list')
        
        data = {}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('offer_detail_id', response.data)
    
    def test_create_order_invalid_offer_detail_id(self):
        """Test validation error when offer_detail_id is invalid."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = reverse('order-list')
        
        data = {
            'offer_detail_id': 99999
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('offer_detail_id', response.data)
    
    def test_create_order_response_has_all_fields(self):
        """Test that response contains all required fields."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = reverse('order-list')
        
        data = {
            'offer_detail_id': self.offer_detail.id
        }
        
        response = self.client.post(url, data, format='json')
        
        required_fields = [
            'id', 'customer_user', 'business_user', 'title',
            'revisions', 'delivery_time_in_days', 'price',
            'features', 'offer_type', 'status', 'created_at', 'updated_at'
        ]
        
        for field in required_fields:
            self.assertIn(field, response.data)
    
    def test_create_order_increments_count(self):
        """Test that creating an order increments the order count."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = reverse('order-list')
        
        initial_count = Order.objects.count()
        
        data = {
            'offer_detail_id': self.offer_detail.id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), initial_count + 1)
        


