"""Tests for authentication API endpoints."""
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()


class RegistrationTests(APITestCase):
    """Test cases for user registration endpoint."""
    
    def setUp(self):
        """Set up test client and initial data."""
        self.client = APIClient()
        self.registration_url = reverse('registration')
        
        # Valid registration data
        self.valid_customer_data = {
            'username': 'testcustomer',
            'email': 'customer@example.com',
            'password': 'TestPass123!',
            'repeated_password': 'TestPass123!',
            'type': 'customer'
        }
        
        self.valid_business_data = {
            'username': 'testbusiness',
            'email': 'business@example.com',
            'password': 'TestPass123!',
            'repeated_password': 'TestPass123!',
            'type': 'business'
        }
    
    def test_register_customer_success(self):
        """Test successful customer registration."""
        response = self.client.post(
            self.registration_url,
            self.valid_customer_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertIn('username', response.data)
        self.assertIn('email', response.data)
        self.assertIn('user_id', response.data)
        self.assertEqual(response.data['username'], 'testcustomer')
        self.assertEqual(response.data['email'], 'customer@example.com')
        
        # Verify user was created in database
        user = User.objects.get(username='testcustomer')
        self.assertEqual(user.type, 'customer')
        self.assertTrue(user.check_password('TestPass123!'))
        
        # Verify token was created
        token = Token.objects.get(user=user)
        self.assertEqual(response.data['token'], token.key)
    
    def test_register_business_success(self):
        """Test successful business user registration."""
        response = self.client.post(
            self.registration_url,
            self.valid_business_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        
        # Verify user was created as business type
        user = User.objects.get(username='testbusiness')
        self.assertEqual(user.type, 'business')
    
    def test_register_password_mismatch(self):
        """Test registration fails when passwords don't match."""
        data = self.valid_customer_data.copy()
        data['repeated_password'] = 'DifferentPassword123!'
        
        response = self.client.post(self.registration_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('repeated_password', response.data)
    
    def test_register_duplicate_username(self):
        """Test registration fails with duplicate username."""
        # Create first user
        self.client.post(self.registration_url, self.valid_customer_data, format='json')
        
        # Try to create second user with same username
        data = self.valid_customer_data.copy()
        data['email'] = 'different@example.com'
        
        response = self.client.post(self.registration_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
    
    def test_register_duplicate_email(self):
        """Test registration fails with duplicate email."""
        # Create first user
        self.client.post(self.registration_url, self.valid_customer_data, format='json')
        
        # Try to create second user with same email
        data = self.valid_customer_data.copy()
        data['username'] = 'differentuser'
        
        response = self.client.post(self.registration_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_register_missing_fields(self):
        """Test registration fails when required fields are missing."""
        # Test missing username
        data = self.valid_customer_data.copy()
        del data['username']
        response = self.client.post(self.registration_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
        
        # Test missing email
        data = self.valid_customer_data.copy()
        del data['email']
        response = self.client.post(self.registration_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        
        # Test missing password
        data = self.valid_customer_data.copy()
        del data['password']
        response = self.client.post(self.registration_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
        
        # Test missing type
        data = self.valid_customer_data.copy()
        del data['type']
        response = self.client.post(self.registration_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('type', response.data)
    
    def test_register_invalid_type(self):
        """Test registration fails with invalid user type."""
        data = self.valid_customer_data.copy()
        data['type'] = 'invalid_type'
        
        response = self.client.post(self.registration_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('type', response.data)
    
    def test_register_invalid_email_format(self):
        """Test registration fails with invalid email format."""
        data = self.valid_customer_data.copy()
        data['email'] = 'not-an-email'
        
        response = self.client.post(self.registration_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_register_empty_fields(self):
        """Test registration fails with empty fields."""
        data = {
            'username': '',
            'email': '',
            'password': '',
            'repeated_password': '',
            'type': 'customer'
        }
        
        response = self.client.post(self.registration_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)