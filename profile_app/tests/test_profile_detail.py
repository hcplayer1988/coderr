"""Tests for profile API endpoints."""
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from profile_app.models import Profile

User = get_user_model()

class ProfileDetailTests(APITestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.customer_user = User.objects.create_user(username='testcustomer', email='customer@test.com', password='TestPass123!', type='customer')
        cls.customer_token = Token.objects.create(user=cls.customer_user)
        cls.business_user = User.objects.create_user(username='testbusiness', email='business@test.com', password='TestPass123!', type='business')
        cls.business_token = Token.objects.create(user=cls.business_user)
        cls.customer_profile = cls.customer_user.profile
        cls.customer_profile.first_name = 'John'
        cls.customer_profile.last_name = 'Doe'
        cls.customer_profile.location = 'Berlin'
        cls.customer_profile.tel = '123456789'
        cls.customer_profile.description = 'Customer description'
        cls.customer_profile.save()
        cls.business_profile = cls.business_user.profile
        cls.business_profile.first_name = 'Max'
        cls.business_profile.last_name = 'Mustermann'
        cls.business_profile.location = 'Berlin'
        cls.business_profile.tel = '123456789'
        cls.business_profile.description = 'Business description'
        cls.business_profile.working_hours = '9-17'
        cls.business_profile.save()
    
    def setUp(self):
        self.client = APIClient()
    
    def test_get_profile_success_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        response = self.client.get(reverse('profile-detail', kwargs={'pk': self.customer_user.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user'], self.customer_user.id)
        self.assertEqual(response.data['username'], 'testcustomer')
        self.assertEqual(response.data['email'], 'customer@test.com')
        self.assertEqual(response.data['type'], 'customer')
        self.assertEqual(response.data['first_name'], 'John')
        self.assertEqual(response.data['last_name'], 'Doe')
        self.assertEqual(response.data['location'], 'Berlin')
        self.assertEqual(response.data['tel'], '123456789')
        self.assertEqual(response.data['description'], 'Customer description')
        self.assertIn('created_at', response.data)
    
    def test_get_business_profile_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        response = self.client.get(reverse('profile-detail', kwargs={'pk': self.business_user.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['type'], 'business')
        self.assertEqual(response.data['working_hours'], '9-17')
        self.assertEqual(response.data['first_name'], 'Max')
        self.assertEqual(response.data['last_name'], 'Mustermann')
    
    def test_get_profile_unauthenticated(self):
        response = self.client.get(reverse('profile-detail', kwargs={'pk': self.customer_user.id}))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_profile_not_found(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        response = self.client.get(reverse('profile-detail', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_other_user_profile(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        response = self.client.get(reverse('profile-detail', kwargs={'pk': self.business_user.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testbusiness')
    
    def test_profile_empty_fields_return_empty_strings(self):
        empty_user = User.objects.create_user(username='emptyuser', email='empty@test.com', password='TestPass123!', type='customer')
        empty_token = Token.objects.create(user=empty_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {empty_token.key}')
        response = self.client.get(reverse('profile-detail', kwargs={'pk': empty_user.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], '')
        self.assertEqual(response.data['last_name'], '')
        self.assertEqual(response.data['location'], '')
        self.assertEqual(response.data['tel'], '')
        self.assertEqual(response.data['description'], '')
        self.assertEqual(response.data['working_hours'], '')
    
    def test_profile_created_automatically_on_user_creation(self):
        new_user = User.objects.create_user(username='newuser', email='new@test.com', password='TestPass123!', type='customer')
        self.assertTrue(hasattr(new_user, 'profile'))
        self.assertIsNotNone(new_user.profile)
        self.assertEqual(new_user.profile.user, new_user)
    
    def test_profile_response_has_all_required_fields(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        response = self.client.get(reverse('profile-detail', kwargs={'pk': self.customer_user.id}))
        required_fields = ['user', 'username', 'first_name', 'last_name', 'file', 'location', 'tel', 'description', 'working_hours', 'type', 'email', 'created_at']
        for field in required_fields:
            self.assertIn(field, response.data, f"Field '{field}' missing in response")

class ProfileUpdateTests(APITestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create_user(username='user1', email='user1@test.com', password='TestPass123!', type='customer')
        cls.token1 = Token.objects.create(user=cls.user1)
        cls.user2 = User.objects.create_user(username='user2', email='user2@test.com', password='TestPass123!', type='business')
        cls.token2 = Token.objects.create(user=cls.user2)
    
    def setUp(self):
        self.client = APIClient()
    
    def test_update_own_profile_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('profile-detail', kwargs={'pk': self.user1.id})
        data = {'first_name': 'Updated', 'last_name': 'Name', 'location': 'Munich', 'tel': '987654321', 'description': 'Updated description', 'working_hours': '10-18'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')
        self.assertEqual(response.data['last_name'], 'Name')
        self.assertEqual(response.data['location'], 'Munich')
        self.assertEqual(response.data['tel'], '987654321')
        self.assertEqual(response.data['description'], 'Updated description')
        self.assertEqual(response.data['working_hours'], '10-18')
        self.user1.profile.refresh_from_db()
        self.assertEqual(self.user1.profile.first_name, 'Updated')
    
    def test_update_profile_partial(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('profile-detail', kwargs={'pk': self.user1.id})
        data = {'first_name': 'John', 'location': 'Hamburg'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'John')
        self.assertEqual(response.data['location'], 'Hamburg')
    
    def test_update_email_in_profile(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('profile-detail', kwargs={'pk': self.user1.id})
        data = {'email': 'newemail@test.com'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'newemail@test.com')
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.email, 'newemail@test.com')
    
    def test_update_other_user_profile_forbidden(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('profile-detail', kwargs={'pk': self.user2.id})
        data = {'first_name': 'Hacked'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.user2.profile.refresh_from_db()
        self.assertNotEqual(self.user2.profile.first_name, 'Hacked')
    
    def test_update_profile_unauthenticated(self):
        url = reverse('profile-detail', kwargs={'pk': self.user1.id})
        data = {'first_name': 'Hacked'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_update_profile_not_found(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('profile-detail', kwargs={'pk': 99999})
        data = {'first_name': 'Test'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_profile_returns_all_fields(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('profile-detail', kwargs={'pk': self.user1.id})
        data = {'first_name': 'Test'}
        response = self.client.patch(url, data, format='json')
        required_fields = ['user', 'username', 'first_name', 'last_name', 'file', 'location', 'tel', 'description', 'working_hours', 'type', 'email', 'created_at']
        for field in required_fields:
            self.assertIn(field, response.data, f"Field '{field}' missing in response")
    
    def test_update_profile_empty_fields_return_empty_strings(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('profile-detail', kwargs={'pk': self.user1.id})
        data = {'first_name': 'John'}
        response = self.client.patch(url, data, format='json')
        self.assertIn('last_name', response.data)
        self.assertIn('location', response.data)
        self.assertIn('tel', response.data)
        self.assertEqual(response.data['last_name'], '')
        self.assertEqual(response.data['location'], '')
        self.assertEqual(response.data['tel'], '')

class BusinessProfileListTests(APITestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.customer = User.objects.create_user(username='customer1', email='customer1@test.com', password='TestPass123!', type='customer')
        cls.customer_token = Token.objects.create(user=cls.customer)
        cls.business1 = User.objects.create_user(username='business1', email='business1@test.com', password='TestPass123!', type='business')
        cls.business1.profile.first_name = 'Business'
        cls.business1.profile.last_name = 'One'
        cls.business1.profile.save()
        cls.business2 = User.objects.create_user(username='business2', email='business2@test.com', password='TestPass123!', type='business')
        cls.business2.profile.first_name = 'Business'
        cls.business2.profile.last_name = 'Two'
        cls.business2.profile.save()
    
    def setUp(self):
        self.client = APIClient()
    
    def test_list_business_profiles_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        response = self.client.get(reverse('business-profiles'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 2)
        for profile in response.data:
            self.assertEqual(profile['type'], 'business')
    
    def test_list_business_profiles_unauthenticated(self):
        response = self.client.get(reverse('business-profiles'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_business_profiles_contains_all_fields(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        response = self.client.get(reverse('business-profiles'))
        required_fields = ['user', 'username', 'first_name', 'last_name', 'file', 'location', 'tel', 'description', 'working_hours', 'type']
        for profile in response.data:
            for field in required_fields:
                self.assertIn(field, profile, f"Field '{field}' missing in profile")

class CustomerProfileListTests(APITestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.business = User.objects.create_user(username='business1', email='business1@test.com', password='TestPass123!', type='business')
        cls.business_token = Token.objects.create(user=cls.business)
        cls.customer1 = User.objects.create_user(username='customer1', email='customer1@test.com', password='TestPass123!', type='customer')
        cls.customer1.profile.first_name = 'Customer'
        cls.customer1.profile.last_name = 'One'
        cls.customer1.profile.save()
        cls.customer2 = User.objects.create_user(username='customer2', email='customer2@test.com', password='TestPass123!', type='customer')
        cls.customer2.profile.first_name = 'Customer'
        cls.customer2.profile.last_name = 'Two'
        cls.customer2.profile.save()
    
    def setUp(self):
        self.client = APIClient()
    
    def test_list_customer_profiles_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        response = self.client.get(reverse('customer-profiles'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 2)
        for profile in response.data:
            self.assertEqual(profile['type'], 'customer')
    
    def test_list_customer_profiles_unauthenticated(self):
        response = self.client.get(reverse('customer-profiles'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_customer_profiles_contains_all_fields(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        response = self.client.get(reverse('customer-profiles'))
        required_fields = ['user', 'username', 'first_name', 'last_name', 'file', 'location', 'tel', 'description', 'working_hours', 'type']
        for profile in response.data:
            for field in required_fields:
                self.assertIn(field, profile, f"Field '{field}' missing in profile")
                


