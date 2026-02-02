"""Tests for authentication API endpoints."""
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()

class LoginTests(APITestCase):
    """Test cases for user login endpoint."""
    
    def setUp(self):
        """Set up test client and create test user."""
        self.client = APIClient()
        self.login_url = reverse('login')
        
        # Create test user
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            type='customer'
        )
        
        # Valid login credentials
        self.valid_credentials = {
            'username': 'testuser',
            'password': 'TestPass123!'
        }
    
    def test_login_success(self):
        """Test successful login with correct credentials."""
        response = self.client.post(
            self.login_url,
            self.valid_credentials,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('username', response.data)
        self.assertIn('email', response.data)
        self.assertIn('user_id', response.data)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['user_id'], self.test_user.id)
        
        # Verify token exists
        token = Token.objects.get(user=self.test_user)
        self.assertEqual(response.data['token'], token.key)
    
    def test_login_wrong_password(self):
        """Test login fails with incorrect password."""
        credentials = {
            'username': 'testuser',
            'password': 'WrongPassword123!'
        }
        
        response = self.client.post(self.login_url, credentials, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
    
    def test_login_wrong_username(self):
        """Test login fails with non-existent username."""
        credentials = {
            'username': 'nonexistentuser',
            'password': 'TestPass123!'
        }
        
        response = self.client.post(self.login_url, credentials, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
    
    def test_login_missing_username(self):
        """Test login fails when username is missing."""
        credentials = {
            'password': 'TestPass123!'
        }
        
        response = self.client.post(self.login_url, credentials, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
    
    def test_login_missing_password(self):
        """Test login fails when password is missing."""
        credentials = {
            'username': 'testuser'
        }
        
        response = self.client.post(self.login_url, credentials, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
    
    def test_login_empty_credentials(self):
        """Test login fails with empty credentials."""
        credentials = {
            'username': '',
            'password': ''
        }
        
        response = self.client.post(self.login_url, credentials, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_login_inactive_user(self):
        """Test login fails for inactive user."""
        # Create inactive user
        inactive_user = User.objects.create_user(
            username='inactiveuser',
            email='inactive@example.com',
            password='TestPass123!',
            type='customer'
        )
        inactive_user.is_active = False
        inactive_user.save()
        
        credentials = {
            'username': 'inactiveuser',
            'password': 'TestPass123!'
        }
        
        response = self.client.post(self.login_url, credentials, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
    
    def test_login_returns_same_token_on_multiple_logins(self):
        """Test that multiple logins return the same token."""
        # First login
        response1 = self.client.post(
            self.login_url,
            self.valid_credentials,
            format='json'
        )
        token1 = response1.data['token']
        
        # Second login
        response2 = self.client.post(
            self.login_url,
            self.valid_credentials,
            format='json'
        )
        token2 = response2.data['token']
        
        # Tokens should be the same
        self.assertEqual(token1, token2)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)



