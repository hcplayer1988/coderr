"""Tests for order API endpoints."""
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from order_app.models import Order
from offer_app.models import Offer, OfferDetail
from decimal import Decimal

User = get_user_model()


class OrderAPITestCase(APITestCase):
    """Shared setup for all order API tests."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all tests."""
        # Create users
        cls.customer_user = User.objects.create_user(
            username='customer',
            email='customer@test.com',
            password='TestPass123!',
            type='customer'
        )
        
        cls.business_user1 = User.objects.create_user(
            username='business1',
            email='business1@test.com',
            password='TestPass123!',
            type='business'
        )
        
        cls.business_user2 = User.objects.create_user(
            username='business2',
            email='business2@test.com',
            password='TestPass123!',
            type='business'
        )
        
        cls.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='TestPass123!',
            type='business',
            is_staff=True
        )
        
        # Create tokens
        cls.customer_token = Token.objects.create(user=cls.customer_user)
        cls.business_token1 = Token.objects.create(user=cls.business_user1)
        cls.business_token2 = Token.objects.create(user=cls.business_user2)
        cls.admin_token = Token.objects.create(user=cls.admin_user)
        
        # Create offer and offer detail for order creation
        cls.offer = Offer.objects.create(
            user=cls.business_user1,
            title='Test Offer',
            description='Test Description'
        )
        
        cls.offer_detail = OfferDetail.objects.create(
            offer=cls.offer,
            title='Basic Package',
            revisions=3,
            delivery_time_in_days=5,
            price=Decimal('150.00'),
            features=['Logo Design', 'Visitenkarten'],
            offer_type='basic'
        )
    
    def setUp(self):
        """Set up test client for each test."""
        self.client = APIClient()


class OrderListTests(OrderAPITestCase):
    """Test GET /api/orders/ endpoint."""
    
    @classmethod
    def setUpTestData(cls):
        """Create test orders."""
        super().setUpTestData()
        
        # Create test orders
        cls.order1 = Order.objects.create(
            customer_user=cls.customer_user,
            business_user=cls.business_user1,
            title='Logo Design',
            revisions=3,
            delivery_time_in_days=5,
            price=Decimal('150.00'),
            features=['Logo Design', 'Visitenkarten'],
            offer_type='basic',
            status='in_progress'
        )
        
        cls.order2 = Order.objects.create(
            customer_user=cls.customer_user,
            business_user=cls.business_user1,
            title='Website Development',
            revisions=5,
            delivery_time_in_days=14,
            price=Decimal('500.00'),
            features=['Website', 'SEO'],
            offer_type='premium',
            status='completed'
        )
        
        cls.order3 = Order.objects.create(
            customer_user=cls.customer_user,
            business_user=cls.business_user2,
            title='Mobile App',
            revisions=10,
            delivery_time_in_days=30,
            price=Decimal('2000.00'),
            features=['iOS App', 'Android App'],
            offer_type='premium',
            status='in_progress'
        )
    
    def test_list_orders_as_customer(self):
        """Customer sees all their orders."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        response = self.client.get(reverse('order-list'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
    
    def test_list_orders_as_business(self):
        """Business user sees only their orders."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token1.key}')
        response = self.client.get(reverse('order-list'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_list_orders_unauthenticated(self):
        """Unauthenticated request returns 401."""
        response = self.client.get(reverse('order-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_orders_has_required_fields(self):
        """Each order has all required fields."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        response = self.client.get(reverse('order-list'))
        
        required_fields = [
            'id', 'customer_user', 'business_user', 'title',
            'revisions', 'delivery_time_in_days', 'price',
            'features', 'offer_type', 'status', 'created_at'
        ]
        
        for order in response.data:
            for field in required_fields:
                self.assertIn(field, order)
    
    def test_list_orders_ordering(self):
        """Orders are ordered by created_at descending."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        response = self.client.get(reverse('order-list'))
        
        # order3 was created last, should be first
        self.assertEqual(response.data[0]['id'], self.order3.id)


class OrderCreateTests(OrderAPITestCase):
    """Test POST /api/orders/ endpoint."""
    
    def test_create_order_success(self):
        """Customer can create order from offer detail."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        data = {'offer_detail_id': self.offer_detail.id}
        
        response = self.client.post(reverse('order-list'), data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Basic Package')
        self.assertEqual(response.data['customer_user'], self.customer_user.id)
        self.assertEqual(response.data['business_user'], self.business_user1.id)
        self.assertEqual(response.data['status'], 'in_progress')
    
    def test_create_order_unauthenticated(self):
        """Unauthenticated request returns 401."""
        data = {'offer_detail_id': self.offer_detail.id}
        response = self.client.post(reverse('order-list'), data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_order_business_forbidden(self):
        """Business user cannot create orders."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token1.key}')
        data = {'offer_detail_id': self.offer_detail.id}
        
        response = self.client.post(reverse('order-list'), data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_order_missing_offer_detail_id(self):
        """Missing offer_detail_id returns 400."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        response = self.client.post(reverse('order-list'), {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('offer_detail_id', response.data)
    
    def test_create_order_invalid_offer_detail_id(self):
        """Invalid offer_detail_id returns 400."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        data = {'offer_detail_id': 99999}
        
        response = self.client.post(reverse('order-list'), data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class OrderUpdateTests(OrderAPITestCase):
    """Test PATCH /api/orders/{id}/ endpoint."""
    
    @classmethod
    def setUpTestData(cls):
        """Create test order."""
        super().setUpTestData()
        
        cls.order = Order.objects.create(
            customer_user=cls.customer_user,
            business_user=cls.business_user1,
            title='Test Order',
            revisions=3,
            delivery_time_in_days=5,
            price=Decimal('150.00'),
            features=['Feature'],
            offer_type='basic',
            status='in_progress'
        )
    
    def test_update_status_success(self):
        """Business user can update their order status."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token1.key}')
        url = reverse('order-detail', kwargs={'id': self.order.id})
        data = {'status': 'completed'}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')
        self.assertIn('updated_at', response.data)
    
    def test_update_unauthenticated(self):
        """Unauthenticated request returns 401."""
        url = reverse('order-detail', kwargs={'id': self.order.id})
        data = {'status': 'completed'}
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_update_customer_forbidden(self):
        """Customer cannot update order status."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = reverse('order-detail', kwargs={'id': self.order.id})
        data = {'status': 'completed'}
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_update_wrong_business_user_forbidden(self):
        """Wrong business user cannot update order."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token2.key}')
        url = reverse('order-detail', kwargs={'id': self.order.id})
        data = {'status': 'completed'}
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_update_invalid_status(self):
        """Invalid status value returns 400."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token1.key}')
        url = reverse('order-detail', kwargs={'id': self.order.id})
        data = {'status': 'invalid_status'}
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_update_not_found(self):
        """Non-existent order returns 404."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token1.key}')
        url = reverse('order-detail', kwargs={'id': 99999})
        data = {'status': 'completed'}
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_read_only_fields(self):
        """Read-only fields cannot be changed."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token1.key}')
        url = reverse('order-detail', kwargs={'id': self.order.id})
        data = {
            'status': 'completed',
            'title': 'Changed Title',
            'price': '999.99'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')
        self.assertEqual(response.data['title'], 'Test Order')
        self.assertEqual(float(response.data['price']), 150.00)


class OrderDeleteTests(OrderAPITestCase):
    """Test DELETE /api/orders/{id}/ endpoint."""
    
    def test_delete_success_as_admin(self):
        """Admin can delete orders."""
        order = Order.objects.create(
            customer_user=self.customer_user,
            business_user=self.business_user1,
            title='To Delete',
            revisions=3,
            delivery_time_in_days=5,
            price=Decimal('150.00'),
            features=['Feature'],
            offer_type='basic',
            status='in_progress'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        url = reverse('order-detail', kwargs={'id': order.id})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Order.objects.filter(id=order.id).exists())
    
    def test_delete_unauthenticated(self):
        """Unauthenticated request returns 401."""
        order = Order.objects.create(
            customer_user=self.customer_user,
            business_user=self.business_user1,
            title='Test',
            revisions=3,
            delivery_time_in_days=5,
            price=Decimal('150.00'),
            features=['Feature'],
            offer_type='basic',
            status='in_progress'
        )
        
        url = reverse('order-detail', kwargs={'id': order.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(Order.objects.filter(id=order.id).exists())
    
    def test_delete_customer_forbidden(self):
        """Customer cannot delete orders."""
        order = Order.objects.create(
            customer_user=self.customer_user,
            business_user=self.business_user1,
            title='Test',
            revisions=3,
            delivery_time_in_days=5,
            price=Decimal('150.00'),
            features=['Feature'],
            offer_type='basic',
            status='in_progress'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = reverse('order-detail', kwargs={'id': order.id})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Order.objects.filter(id=order.id).exists())
    
    def test_delete_business_forbidden(self):
        """Business user cannot delete orders."""
        order = Order.objects.create(
            customer_user=self.customer_user,
            business_user=self.business_user1,
            title='Test',
            revisions=3,
            delivery_time_in_days=5,
            price=Decimal('150.00'),
            features=['Feature'],
            offer_type='basic',
            status='in_progress'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token1.key}')
        url = reverse('order-detail', kwargs={'id': order.id})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Order.objects.filter(id=order.id).exists())
    
    def test_delete_not_found(self):
        """Non-existent order returns 404."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        url = reverse('order-detail', kwargs={'id': 99999})
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class OrderCountTests(OrderAPITestCase):
    """Test GET /api/order-count/{business_user_id}/ endpoint."""
    
    @classmethod
    def setUpTestData(cls):
        """Create test orders."""
        super().setUpTestData()
        
        # 3 in_progress orders for business_user1
        for i in range(3):
            Order.objects.create(
                customer_user=cls.customer_user,
                business_user=cls.business_user1,
                title=f'Order {i+1}',
                revisions=3,
                delivery_time_in_days=5,
                price=Decimal('150.00'),
                features=['Feature'],
                offer_type='basic',
                status='in_progress'
            )
        
        # 2 completed orders (should NOT be counted)
        for i in range(2):
            Order.objects.create(
                customer_user=cls.customer_user,
                business_user=cls.business_user1,
                title=f'Completed {i+1}',
                revisions=3,
                delivery_time_in_days=5,
                price=Decimal('150.00'),
                features=['Feature'],
                offer_type='basic',
                status='completed'
            )
    
    def test_order_count_success(self):
        """Get count of in_progress orders."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = reverse('order-count', kwargs={'business_user_id': self.business_user1.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order_count'], 3)
    
    def test_order_count_zero(self):
        """Business user with no in_progress orders returns 0."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = reverse('order-count', kwargs={'business_user_id': self.business_user2.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order_count'], 0)
    
    def test_order_count_unauthenticated(self):
        """Unauthenticated request returns 401."""
        url = reverse('order-count', kwargs={'business_user_id': self.business_user1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_order_count_user_not_found(self):
        """Non-existent user returns 404."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = reverse('order-count', kwargs={'business_user_id': 99999})
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        


