"""Tests for profile API endpoints."""
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from profile_app.models import Profile

User = get_user_model()


class ProfileDetailTests(APITestCase):
    """Test cases for profile detail endpoint (GET)."""
    
    def setUp(self):
        """Set up test client and test users."""
        self.client = APIClient()
        
        # Create test customer user
        self.customer_user = User.objects.create_user(
            username='testcustomer',
            email='customer@test.com',
            password='TestPass123!',
            type='customer'
        )
        self.customer_token = Token.objects.create(user=self.customer_user)
        
        # Create test business user
        self.business_user = User.objects.create_user(
            username='testbusiness',
            email='business@test.com',
            password='TestPass123!',
            type='business'
        )
        self.business_token = Token.objects.create(user=self.business_user)
        
        # Update customer profile with data
        self.customer_profile = self.customer_user.profile
        self.customer_profile.first_name = 'John'
        self.customer_profile.last_name = 'Doe'
        self.customer_profile.location = 'Berlin'
        self.customer_profile.tel = '123456789'
        self.customer_profile.description = 'Customer description'
        self.customer_profile.save()
        
        # Update business profile with data
        self.business_profile = self.business_user.profile
        self.business_profile.first_name = 'Max'
        self.business_profile.last_name = 'Mustermann'
        self.business_profile.location = 'Berlin'
        self.business_profile.tel = '123456789'
        self.business_profile.description = 'Business description'
        self.business_profile.working_hours = '9-17'
        self.business_profile.save()
    
    def test_get_profile_success_authenticated(self):
        """Test getting profile while authenticated."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = reverse('profile-detail', kwargs={'pk': self.customer_user.id})
        
        response = self.client.get(url)
        
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
        """Test getting business profile."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('profile-detail', kwargs={'pk': self.business_user.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['type'], 'business')
        self.assertEqual(response.data['working_hours'], '9-17')
        self.assertEqual(response.data['first_name'], 'Max')
        self.assertEqual(response.data['last_name'], 'Mustermann')
    
    def test_get_profile_unauthenticated(self):
        """Test getting profile without authentication fails."""
        url = reverse('profile-detail', kwargs={'pk': self.customer_user.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_profile_not_found(self):
        """Test getting non-existent profile returns 404."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = reverse('profile-detail', kwargs={'pk': 99999})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_other_user_profile(self):
        """Test that authenticated user can view other user's profile."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = reverse('profile-detail', kwargs={'pk': self.business_user.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testbusiness')
    
    def test_profile_empty_fields_return_empty_strings(self):
        """Test that empty profile fields return empty strings, not null."""
        # Create user with empty profile
        empty_user = User.objects.create_user(
            username='emptyuser',
            email='empty@test.com',
            password='TestPass123!',
            type='customer'
        )
        empty_token = Token.objects.create(user=empty_user)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {empty_token.key}')
        url = reverse('profile-detail', kwargs={'pk': empty_user.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # These fields should be empty strings, not null
        self.assertEqual(response.data['first_name'], '')
        self.assertEqual(response.data['last_name'], '')
        self.assertEqual(response.data['location'], '')
        self.assertEqual(response.data['tel'], '')
        self.assertEqual(response.data['description'], '')
        self.assertEqual(response.data['working_hours'], '')
    
    def test_profile_created_automatically_on_user_creation(self):
        """Test that profile is automatically created when user is created."""
        new_user = User.objects.create_user(
            username='newuser',
            email='new@test.com',
            password='TestPass123!',
            type='customer'
        )
        
        # Check that profile exists
        self.assertTrue(hasattr(new_user, 'profile'))
        self.assertIsNotNone(new_user.profile)
        self.assertEqual(new_user.profile.user, new_user)
    
    def test_profile_response_has_all_required_fields(self):
        """Test that response contains all required fields."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = reverse('profile-detail', kwargs={'pk': self.customer_user.id})
        
        response = self.client.get(url)
        
        required_fields = [
            'user', 'username', 'first_name', 'last_name', 'file',
            'location', 'tel', 'description', 'working_hours',
            'type', 'email', 'created_at'
        ]
        
        for field in required_fields:
            self.assertIn(field, response.data, f"Field '{field}' missing in response")
            
