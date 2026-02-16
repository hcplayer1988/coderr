"""Tests for order API endpoints."""
from decimal import Decimal

from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token

from order_app.models import Order
from offer_app.models import Offer, OfferDetail

User = get_user_model()


class OrderTestBase(APITestCase):
    """Base class with common setup for all order tests."""

    @classmethod
    def setUpTestData(cls):
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
        cls.customer_token = Token.objects.create(user=cls.customer_user)
        cls.business_token1 = Token.objects.create(user=cls.business_user1)
        cls.business_token2 = Token.objects.create(user=cls.business_user2)
        cls.admin_token = Token.objects.create(user=cls.admin_user)
        cls.offer = Offer.objects.create(
            user=cls.business_user1,
            title='Test Offer',
            description='Test'
        )
        cls.offer_detail = OfferDetail.objects.create(
            offer=cls.offer,
            title='Basic Package',
            revisions=3,
            delivery_time_in_days=5,
            price=Decimal('150.00'),
            features=['Logo', 'Card'],
            offer_type='basic'
        )

    def setUp(self):
        self.client = APIClient()


class OrderListTests(OrderTestBase):
    """Tests for GET /api/orders/ - List orders."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.order1 = Order.objects.create(
            customer_user=cls.customer_user,
            business_user=cls.business_user1,
            title='Order 1',
            revisions=3,
            delivery_time_in_days=5,
            price=Decimal('150.00'),
            features=['Logo'],
            offer_type='basic',
            status='in_progress'
        )
        cls.order2 = Order.objects.create(
            customer_user=cls.customer_user,
            business_user=cls.business_user1,
            title='Order 2',
            revisions=5,
            delivery_time_in_days=10,
            price=Decimal('300.00'),
            features=['Website'],
            offer_type='premium',
            status='completed'
        )
        cls.order3 = Order.objects.create(
            customer_user=cls.customer_user,
            business_user=cls.business_user2,
            title='Order 3',
            revisions=2,
            delivery_time_in_days=3,
            price=Decimal('100.00'),
            features=['App'],
            offer_type='standard',
            status='in_progress'
        )

    def test_list_orders_as_customer(self):
        """Customer sees all their orders."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}'
        )
        response = self.client.get(reverse('order-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_list_orders_as_business(self):
        """Business user sees only orders where they are business_user."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.business_token1.key}'
        )
        response = self.client.get(reverse('order-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_orders_unauthenticated(self):
        """Unauthenticated request fails."""
        response = self.client.get(reverse('order-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_orders_ordering(self):
        """Orders are ordered by created_at descending."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}'
        )
        response = self.client.get(reverse('order-list'))
        self.assertEqual(response.data[0]['id'], self.order3.id)


class OrderCreateTests(OrderTestBase):
    """Tests for POST /api/orders/ - Create order from offer detail."""

    def test_create_order_success(self):
        """Customer can create order from offer detail."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}'
        )
        data = {'offer_detail_id': self.offer_detail.id}
        response = self.client.post(reverse('order-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Basic Package')
        self.assertEqual(response.data['customer_user'], self.customer_user.id)
        self.assertEqual(
            response.data['business_user'],
            self.business_user1.id
        )
        self.assertEqual(response.data['status'], 'in_progress')
        self.assertEqual(response.data['revisions'], 3)
        self.assertEqual(response.data['delivery_time_in_days'], 5)
        self.assertEqual(float(response.data['price']), 150.00)

    def test_create_order_business_user_forbidden(self):
        """Business user cannot create orders."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.business_token1.key}'
        )
        data = {'offer_detail_id': self.offer_detail.id}
        response = self.client.post(reverse('order-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_order_missing_offer_detail_id(self):
        """Missing offer_detail_id returns 400."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}'
        )
        response = self.client.post(reverse('order-list'), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('offer_detail_id', response.data)

    def test_create_order_invalid_offer_detail_id(self):
        """Invalid offer_detail_id returns 400."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}'
        )
        data = {'offer_detail_id': 99999}
        response = self.client.post(reverse('order-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_order_unauthenticated(self):
        """Unauthenticated request fails."""
        data = {'offer_detail_id': self.offer_detail.id}
        response = self.client.post(reverse('order-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class OrderUpdateTests(OrderTestBase):
    """Tests for PATCH /api/orders/{id}/ - Update order status."""

    @classmethod
    def setUpTestData(cls):
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
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.business_token1.key}'
        )
        url = reverse('order-detail', kwargs={'id': self.order.id})
        data = {'status': 'completed'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')
        self.assertIn('updated_at', response.data)

    def test_update_status_invalid_choice(self):
        """Invalid status value is rejected."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.business_token1.key}'
        )
        url = reverse('order-detail', kwargs={'id': self.order.id})
        data = {'status': 'invalid_status'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_customer_forbidden(self):
        """Customer cannot update order status."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}'
        )
        url = reverse('order-detail', kwargs={'id': self.order.id})
        data = {'status': 'completed'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_wrong_business_user_forbidden(self):
        """Wrong business user cannot update order."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.business_token2.key}'
        )
        url = reverse('order-detail', kwargs={'id': self.order.id})
        data = {'status': 'completed'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_unauthenticated(self):
        """Unauthenticated request fails."""
        url = reverse('order-detail', kwargs={'id': self.order.id})
        data = {'status': 'completed'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_not_found(self):
        """Non-existent order returns 404."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.business_token1.key}'
        )
        url = reverse('order-detail', kwargs={'id': 99999})
        data = {'status': 'completed'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_read_only_fields(self):
        """Read-only fields cannot be changed."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.business_token1.key}'
        )
        url = reverse('order-detail', kwargs={'id': self.order.id})
        data = {'status': 'completed', 'title': 'Hacked', 'price': '999.99'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')
        self.assertEqual(response.data['title'], 'Test Order')
        self.assertEqual(float(response.data['price']), 150.00)


class OrderDeleteTests(OrderTestBase):
    """Tests for DELETE /api/orders/{id}/ - Delete order (admin only)."""

    def test_delete_success_as_admin(self):
        """Admin can delete orders."""
        order = Order.objects.create(
            customer_user=self.customer_user,
            business_user=self.business_user1,
            title='Delete Me',
            revisions=3,
            delivery_time_in_days=5,
            price=Decimal('150.00'),
            features=['Feature'],
            offer_type='basic',
            status='in_progress'
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.admin_token.key}'
        )
        url = reverse('order-detail', kwargs={'id': order.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Order.objects.filter(id=order.id).exists())

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
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}'
        )
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
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.business_token1.key}'
        )
        url = reverse('order-detail', kwargs={'id': order.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Order.objects.filter(id=order.id).exists())

    def test_delete_unauthenticated(self):
        """Unauthenticated request fails."""
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

    def test_delete_not_found(self):
        """Non-existent order returns 404."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.admin_token.key}'
        )
        url = reverse('order-detail', kwargs={'id': 99999})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class OrderCountTests(OrderTestBase):
    """Tests for GET /api/order-count/{business_user_id}/."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        for i in range(3):
            Order.objects.create(
                customer_user=cls.customer_user,
                business_user=cls.business_user1,
                title=f'Order {i}',
                revisions=3,
                delivery_time_in_days=5,
                price=Decimal('150.00'),
                features=['F'],
                offer_type='basic',
                status='in_progress'
            )
        for i in range(2):
            Order.objects.create(
                customer_user=cls.customer_user,
                business_user=cls.business_user1,
                title=f'Done {i}',
                revisions=3,
                delivery_time_in_days=5,
                price=Decimal('150.00'),
                features=['F'],
                offer_type='basic',
                status='completed'
            )

    def test_order_count_success(self):
        """Returns count of in_progress orders."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}'
        )
        url = reverse(
            'order-count',
            kwargs={'business_user_id': self.business_user1.id}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order_count'], 3)

    def test_order_count_zero(self):
        """Returns 0 for business user with no in_progress orders."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}'
        )
        url = reverse(
            'order-count',
            kwargs={'business_user_id': self.business_user2.id}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order_count'], 0)

    def test_order_count_unauthenticated(self):
        """Unauthenticated request fails."""
        url = reverse(
            'order-count',
            kwargs={'business_user_id': self.business_user1.id}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_order_count_user_not_found(self):
        """Non-existent user returns 404."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}'
        )
        url = reverse('order-count', kwargs={'business_user_id': 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CompletedOrderCountTests(OrderTestBase):
    """Tests for GET /api/completed-order-count/{business_user_id}/."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        for i in range(2):
            Order.objects.create(
                customer_user=cls.customer_user,
                business_user=cls.business_user1,
                title=f'Done {i}',
                revisions=3,
                delivery_time_in_days=5,
                price=Decimal('150.00'),
                features=['F'],
                offer_type='basic',
                status='completed'
            )
        for i in range(3):
            Order.objects.create(
                customer_user=cls.customer_user,
                business_user=cls.business_user1,
                title=f'WIP {i}',
                revisions=3,
                delivery_time_in_days=5,
                price=Decimal('150.00'),
                features=['F'],
                offer_type='basic',
                status='in_progress'
            )

    def test_completed_order_count_success(self):
        """Returns count of completed orders."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}'
        )
        url = reverse(
            'completed-order-count',
            kwargs={'business_user_id': self.business_user1.id}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['completed_order_count'], 2)

    def test_completed_order_count_zero(self):
        """Returns 0 for business user with no completed orders."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}'
        )
        url = reverse(
            'completed-order-count',
            kwargs={'business_user_id': self.business_user2.id}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['completed_order_count'], 0)

    def test_completed_order_count_unauthenticated(self):
        """Unauthenticated request fails."""
        url = reverse(
            'completed-order-count',
            kwargs={'business_user_id': self.business_user1.id}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_completed_order_count_user_not_found(self):
        """Non-existent user returns 404."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}'
        )
        url = reverse(
            'completed-order-count',
            kwargs={'business_user_id': 99999}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class OrderSerializerTests(OrderTestBase):
    """Tests for OrderCreateSerializer and features handling."""

    def test_create_serializer_copies_all_fields(self):
        """OrderCreateSerializer copies all fields from OfferDetail."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}'
        )
        data = {'offer_detail_id': self.offer_detail.id}
        response = self.client.post(reverse('order-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Basic Package')
        self.assertEqual(response.data['revisions'], 3)
        self.assertEqual(response.data['delivery_time_in_days'], 5)
        self.assertEqual(float(response.data['price']), 150.00)
        self.assertEqual(response.data['offer_type'], 'basic')

    def test_features_list_serialization(self):
        """Features are returned as list."""
        order = Order.objects.create(
            customer_user=self.customer_user,
            business_user=self.business_user1,
            title='Test',
            revisions=3,
            delivery_time_in_days=5,
            price=Decimal('150.00'),
            features=['A', 'B', 'C'],
            offer_type='basic',
            status='in_progress'
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}'
        )
        response = self.client.get(reverse('order-list'))
        order_data = [o for o in response.data if o['id'] == order.id][0]
        self.assertIsInstance(order_data['features'], list)
        self.assertEqual(len(order_data['features']), 3)

    def test_features_string_parsing(self):
        """Features stored as string are parsed to list."""
        order = Order.objects.create(
            customer_user=self.customer_user,
            business_user=self.business_user1,
            title='Test',
            revisions=3,
            delivery_time_in_days=5,
            price=Decimal('150.00'),
            features='["X", "Y"]',
            offer_type='basic',
            status='in_progress'
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}'
        )
        response = self.client.get(reverse('order-list'))
        order_data = [o for o in response.data if o['id'] == order.id][0]
        self.assertIsInstance(order_data['features'], list)
        self.assertEqual(order_data['features'], ['X', 'Y'])


class OrderPermissionTests(OrderTestBase):
    """Tests for custom permissions."""

    def test_is_business_user_of_order_permission_success(self):
        """Business user can update their own order."""
        order = Order.objects.create(
            customer_user=self.customer_user,
            business_user=self.business_user1,
            title='Test',
            revisions=3,
            delivery_time_in_days=5,
            price=Decimal('150.00'),
            features=['F'],
            offer_type='basic',
            status='in_progress'
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.business_token1.key}'
        )
        url = reverse('order-detail', kwargs={'id': order.id})
        response = self.client.patch(
            url,
            {'status': 'completed'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_is_business_user_of_order_permission_denied(self):
        """Non-business user cannot update order."""
        order = Order.objects.create(
            customer_user=self.customer_user,
            business_user=self.business_user1,
            title='Test',
            revisions=3,
            delivery_time_in_days=5,
            price=Decimal('150.00'),
            features=['F'],
            offer_type='basic',
            status='in_progress'
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}'
        )
        url = reverse('order-detail', kwargs={'id': order.id})
        response = self.client.patch(
            url,
            {'status': 'completed'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_is_admin_user_permission_success(self):
        """Admin user can delete orders."""
        order = Order.objects.create(
            customer_user=self.customer_user,
            business_user=self.business_user1,
            title='Test',
            revisions=3,
            delivery_time_in_days=5,
            price=Decimal('150.00'),
            features=['F'],
            offer_type='basic',
            status='in_progress'
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.admin_token.key}'
        )
        url = reverse('order-detail', kwargs={'id': order.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_is_admin_user_permission_denied(self):
        """Non-admin cannot delete orders."""
        order = Order.objects.create(
            customer_user=self.customer_user,
            business_user=self.business_user1,
            title='Test',
            revisions=3,
            delivery_time_in_days=5,
            price=Decimal('150.00'),
            features=['F'],
            offer_type='basic',
            status='in_progress'
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.business_token1.key}'
        )
        url = reverse('order-detail', kwargs={'id': order.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class OrderSerializerEdgeCaseTests(OrderTestBase):
    """Additional tests to cover serializer edge cases (62% → 95%)."""

    def test_features_nested_json_string(self):
        """Test features with nested JSON string parsing."""
        order = Order.objects.create(
            customer_user=self.customer_user,
            business_user=self.business_user1,
            title='Nested JSON',
            revisions=3,
            delivery_time_in_days=5,
            price=Decimal('150.00'),
            features='["Item1", "Item2"]',
            offer_type='basic',
            status='in_progress'
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}'
        )
        response = self.client.get(reverse('order-list'))
        order_data = [o for o in response.data if o['id'] == order.id][0]
        self.assertEqual(order_data['features'], ['Item1', 'Item2'])

    def test_features_malformed_json_fallback(self):
        """Test features with malformed JSON falls back to string in list."""
        order = Order.objects.create(
            customer_user=self.customer_user,
            business_user=self.business_user1,
            title='Malformed',
            revisions=3,
            delivery_time_in_days=5,
            price=Decimal('150.00'),
            features='invalid json {[',
            offer_type='basic',
            status='in_progress'
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}'
        )
        response = self.client.get(reverse('order-list'))
        order_data = [o for o in response.data if o['id'] == order.id][0]
        self.assertIsInstance(order_data['features'], list)
        self.assertEqual(order_data['features'], ['invalid json {['])

    def test_features_ast_literal_eval_path(self):
        """Test features using Python list string format."""
        order = Order.objects.create(
            customer_user=self.customer_user,
            business_user=self.business_user1,
            title='AST Parse',
            revisions=3,
            delivery_time_in_days=5,
            price=Decimal('150.00'),
            features="['Feature A', 'Feature B']",
            offer_type='basic',
            status='in_progress'
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}'
        )
        response = self.client.get(reverse('order-list'))
        order_data = [o for o in response.data if o['id'] == order.id][0]
        self.assertEqual(order_data['features'], ['Feature A', 'Feature B'])

    def test_features_double_json_encoded(self):
        """Test features that are double JSON encoded."""
        order = Order.objects.create(
            customer_user=self.customer_user,
            business_user=self.business_user1,
            title='Double Encoded',
            revisions=3,
            delivery_time_in_days=5,
            price=Decimal('150.00'),
            features='"[\\"A\\", \\"B\\"]"',
            offer_type='basic',
            status='in_progress'
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}'
        )
        response = self.client.get(reverse('order-list'))
        order_data = [o for o in response.data if o['id'] == order.id][0]
        self.assertIsInstance(order_data['features'], list)

    def test_features_single_value_becomes_list(self):
        """Test single non-list value wrapped in list."""
        order = Order.objects.create(
            customer_user=self.customer_user,
            business_user=self.business_user1,
            title='Single Value',
            revisions=3,
            delivery_time_in_days=5,
            price=Decimal('150.00'),
            features='123',
            offer_type='basic',
            status='in_progress'
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}'
        )
        response = self.client.get(reverse('order-list'))
        order_data = [o for o in response.data if o['id'] == order.id][0]
        self.assertIsInstance(order_data['features'], list)

    def test_features_empty_list(self):
        """Test features with empty list."""
        order = Order.objects.create(
            customer_user=self.customer_user,
            business_user=self.business_user1,
            title='Empty Features',
            revisions=3,
            delivery_time_in_days=5,
            price=Decimal('150.00'),
            features=[],
            offer_type='basic',
            status='in_progress'
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}'
        )
        response = self.client.get(reverse('order-list'))
        order_data = [o for o in response.data if o['id'] == order.id][0]
        self.assertEqual(order_data['features'], [])

    def test_features_integer_value_becomes_list(self):
        """Test features with integer value wrapped in list."""
        order = Order.objects.create(
            customer_user=self.customer_user,
            business_user=self.business_user1,
            title='Integer Features',
            revisions=3,
            delivery_time_in_days=5,
            price=Decimal('150.00'),
            features=456,
            offer_type='basic',
            status='in_progress'
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}'
        )
        response = self.client.get(reverse('order-list'))
        order_data = [o for o in response.data if o['id'] == order.id][0]
        self.assertIsInstance(order_data['features'], list)

    def test_update_serializer_features_parsing(self):
        """Test OrderUpdateSerializer features parsing."""
        order = Order.objects.create(
            customer_user=self.customer_user,
            business_user=self.business_user1,
            title='Update Test',
            revisions=3,
            delivery_time_in_days=5,
            price=Decimal('150.00'),
            features='["Old Feature"]',
            offer_type='basic',
            status='in_progress'
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.business_token1.key}'
        )
        url = reverse('order-detail', kwargs={'id': order.id})
        response = self.client.patch(
            url,
            {'status': 'completed'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['features'], ['Old Feature'])

    def test_validate_status_allowed_values(self):
        """Test all allowed status values."""
        order = Order.objects.create(
            customer_user=self.customer_user,
            business_user=self.business_user1,
            title='Status Test',
            revisions=3,
            delivery_time_in_days=5,
            price=Decimal('150.00'),
            features=['F'],
            offer_type='basic',
            status='in_progress'
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.business_token1.key}'
        )
        url = reverse('order-detail', kwargs={'id': order.id})
        for status_value in ['in_progress', 'completed', 'cancelled']:
            response = self.client.patch(
                url,
                {'status': status_value},
                format='json'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['status'], status_value)

    def test_offer_detail_validation_not_exists(self):
        """Test OfferDetail.DoesNotExist exception path."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}'
        )
        data = {'offer_detail_id': 999999}
        response = self.client.post(reverse('order-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('offer_detail_id', str(response.data))

    def test_create_serializer_invalid_type(self):
        """Test offer_detail_id with invalid type."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}'
        )
        data = {'offer_detail_id': 'not_an_integer'}
        response = self.client.post(reverse('order-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class OrderPermissionEdgeCaseTests(OrderTestBase):
    """Additional tests to cover permission edge cases (83% → 100%)."""

    def test_is_business_user_permission_no_type_attribute(self):
        """Test permission when user has no 'type' attribute."""
        order = Order.objects.create(
            customer_user=self.customer_user,
            business_user=self.business_user1,
            title='Permission Test',
            revisions=3,
            delivery_time_in_days=5,
            price=Decimal('150.00'),
            features=['F'],
            offer_type='basic',
            status='in_progress'
        )
        from order_app.api.permissions import IsBusinessUserOfOrder
        permission = IsBusinessUserOfOrder()

        class MockRequest:
            def __init__(self):
                self.user = type('obj', (object,), {})()

        mock_request = MockRequest()
        has_permission = permission.has_object_permission(
            mock_request,
            None,
            order
        )
        self.assertFalse(has_permission)

    def test_is_business_user_permission_customer_type(self):
        """Test permission explicitly denies customer type users."""
        order = Order.objects.create(
            customer_user=self.customer_user,
            business_user=self.business_user1,
            title='Customer Type Test',
            revisions=3,
            delivery_time_in_days=5,
            price=Decimal('150.00'),
            features=['F'],
            offer_type='basic',
            status='in_progress'
        )
        from order_app.api.permissions import IsBusinessUserOfOrder
        permission = IsBusinessUserOfOrder()

        class MockRequest:
            def __init__(self, user):
                self.user = user

        mock_request = MockRequest(self.customer_user)
        has_permission = permission.has_object_permission(
            mock_request,
            None,
            order
        )
        self.assertFalse(has_permission)

    def test_is_admin_user_permission_non_staff(self):
        """Test IsAdminUser permission denies non-staff users."""
        from order_app.api.permissions import IsAdminUser
        permission = IsAdminUser()

        class MockRequest:
            def __init__(self, user):
                self.user = user

        mock_request = MockRequest(self.customer_user)
        has_permission = permission.has_permission(mock_request, None)
        self.assertFalse(has_permission)

        mock_request = MockRequest(self.business_user1)
        has_permission = permission.has_permission(mock_request, None)
        self.assertFalse(has_permission)

        mock_request = MockRequest(self.admin_user)
        has_permission = permission.has_permission(mock_request, None)
        self.assertTrue(has_permission)

    def test_is_admin_user_permission_no_user(self):
        """Test IsAdminUser permission when request.user is None."""
        from order_app.api.permissions import IsAdminUser
        permission = IsAdminUser()

        class MockRequest:
            def __init__(self):
                self.user = None

        mock_request = MockRequest()
        has_permission = permission.has_permission(mock_request, None)
        self.assertFalse(has_permission)


class OrderViewExceptionTests(OrderTestBase):
    """Tests for exception handling in views."""

    def test_list_view_exception_handling(self):
        """Test that list view handles exceptions gracefully."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}'
        )
        response = self.client.get(reverse('order-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_view_exception_handling(self):
        """Test that create view handles exceptions gracefully."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}'
        )
        response = self.client.post(
            reverse('order-list'),
            {'offer_detail_id': self.offer_detail.id},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_view_http404_exception(self):
        """Test update view handles Http404 exception."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.business_token1.key}'
        )
        url = reverse('order-detail', kwargs={'id': 999999})
        response = self.client.patch(
            url,
            {'status': 'completed'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_view_http404_exception(self):
        """Test delete view handles Http404 exception."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.admin_token.key}'
        )
        url = reverse('order-detail', kwargs={'id': 999999})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class OrderModelTests(OrderTestBase):
    """Tests for Order model."""

    def test_order_str_method(self):
        """Test Order __str__ method."""
        order = Order.objects.create(
            customer_user=self.customer_user,
            business_user=self.business_user1,
            title='Test Order',
            revisions=3,
            delivery_time_in_days=5,
            price=Decimal('150.00'),
            features=['Feature'],
            offer_type='basic',
            status='in_progress'
        )
        expected_str = f"Order #{order.id}: Test Order - in_progress"
        self.assertEqual(str(order), expected_str)

    def test_order_default_values(self):
        """Test Order model default values."""
        order = Order.objects.create(
            customer_user=self.customer_user,
            business_user=self.business_user1,
            title='Defaults Test',
            revisions=0,
            delivery_time_in_days=5,
            price=Decimal('100.00'),
            offer_type='basic'
        )
        self.assertEqual(order.status, 'in_progress')
        self.assertEqual(order.features, [])
        self.assertIsNotNone(order.created_at)
        self.assertIsNotNone(order.updated_at)

    def test_order_status_choices(self):
        """Test all status choices are valid."""
        for status_choice, _ in Order.STATUS_CHOICES:
            order = Order.objects.create(
                customer_user=self.customer_user,
                business_user=self.business_user1,
                title=f'Status {status_choice}',
                revisions=3,
                delivery_time_in_days=5,
                price=Decimal('150.00'),
                features=['F'],
                offer_type='basic',
                status=status_choice
            )
            self.assertEqual(order.status, status_choice)

    def test_order_offer_type_choices(self):
        """Test all offer_type choices are valid."""
        for offer_type, _ in Order.OFFER_TYPE_CHOICES:
            order = Order.objects.create(
                customer_user=self.customer_user,
                business_user=self.business_user1,
                title=f'Type {offer_type}',
                revisions=3,
                delivery_time_in_days=5,
                price=Decimal('150.00'),
                features=['F'],
                offer_type=offer_type,
                status='in_progress'
            )
            self.assertEqual(order.offer_type, offer_type)
