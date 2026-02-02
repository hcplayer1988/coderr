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


class ProfileUpdateTests(APITestCase):
    """Test cases for profile update endpoint (PATCH)."""
    
    def setUp(self):
        """Set up test client and test users."""
        self.client = APIClient()
        
        # Create test users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='TestPass123!',
            type='customer'
        )
        self.token1 = Token.objects.create(user=self.user1)
        
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@test.com',
            password='TestPass123!',
            type='business'
        )
        self.token2 = Token.objects.create(user=self.user2)
    
    def test_update_own_profile_success(self):
        """Test successful profile update by owner."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('profile-detail', kwargs={'pk': self.user1.id})
        
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'location': 'Munich',
            'tel': '987654321',
            'description': 'Updated description',
            'working_hours': '10-18'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')
        self.assertEqual(response.data['last_name'], 'Name')
        self.assertEqual(response.data['location'], 'Munich')
        self.assertEqual(response.data['tel'], '987654321')
        self.assertEqual(response.data['description'], 'Updated description')
        self.assertEqual(response.data['working_hours'], '10-18')
        
        # Verify database was updated
        self.user1.profile.refresh_from_db()
        self.assertEqual(self.user1.profile.first_name, 'Updated')
    
    def test_update_profile_partial(self):
        """Test partial profile update (only some fields)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('profile-detail', kwargs={'pk': self.user1.id})
        
        data = {
            'first_name': 'John',
            'location': 'Hamburg'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'John')
        self.assertEqual(response.data['location'], 'Hamburg')
    
    def test_update_email_in_profile(self):
        """Test updating email through profile endpoint."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('profile-detail', kwargs={'pk': self.user1.id})
        
        data = {
            'email': 'newemail@test.com'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'newemail@test.com')
        
        # Verify user email was updated
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.email, 'newemail@test.com')
    
    def test_update_other_user_profile_forbidden(self):
        """Test that user cannot update another user's profile."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('profile-detail', kwargs={'pk': self.user2.id})
        
        data = {
            'first_name': 'Hacked'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Verify profile was not updated
        self.user2.profile.refresh_from_db()
        self.assertNotEqual(self.user2.profile.first_name, 'Hacked')
    
    def test_update_profile_unauthenticated(self):
        """Test that unauthenticated users cannot update profiles."""
        url = reverse('profile-detail', kwargs={'pk': self.user1.id})
        
        data = {
            'first_name': 'Hacked'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_update_profile_not_found(self):
        """Test updating non-existent profile returns 404."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('profile-detail', kwargs={'pk': 99999})
        
        data = {
            'first_name': 'Test'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_profile_returns_all_fields(self):
        """Test that update response contains all profile fields."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('profile-detail', kwargs={'pk': self.user1.id})
        
        data = {
            'first_name': 'Test'
        }
        
        response = self.client.patch(url, data, format='json')
        
        required_fields = [
            'user', 'username', 'first_name', 'last_name', 'file',
            'location', 'tel', 'description', 'working_hours',
            'type', 'email', 'created_at'
        ]
        
        for field in required_fields:
            self.assertIn(field, response.data, f"Field '{field}' missing in response")
    
    def test_update_profile_empty_fields_return_empty_strings(self):
        """Test that empty fields in update response are empty strings."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('profile-detail', kwargs={'pk': self.user1.id})
        
        data = {
            'first_name': 'John'
        }
        
        response = self.client.patch(url, data, format='json')
        
        # Check that response has the required fields
        self.assertIn('last_name', response.data)
        self.assertIn('location', response.data)
        self.assertIn('tel', response.data)
        
        # Empty fields should be empty strings
        self.assertEqual(response.data['last_name'], '')
        self.assertEqual(response.data['location'], '')
        self.assertEqual(response.data['tel'], '')
        
        
        
