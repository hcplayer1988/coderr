"""Tests for reviews API endpoints."""
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from reviews_app.models import Review

User = get_user_model()


class ReviewAPITestCase(APITestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.customer_user = User.objects.create_user(username='customer', email='customer@test.com', password='TestPass123!', type='customer')
        cls.business_user1 = User.objects.create_user(username='business1', email='business1@test.com', password='TestPass123!', type='business')
        cls.business_user2 = User.objects.create_user(username='business2', email='business2@test.com', password='TestPass123!', type='business')
        cls.reviewer2 = User.objects.create_user(username='reviewer2', email='reviewer2@test.com', password='TestPass123!', type='customer')
        cls.customer_token = Token.objects.create(user=cls.customer_user)
        cls.business_token1 = Token.objects.create(user=cls.business_user1)
        cls.business_token2 = Token.objects.create(user=cls.business_user2)
        cls.reviewer2_token = Token.objects.create(user=cls.reviewer2)
    
    def setUp(self):
        self.client = APIClient()


class ReviewListTests(ReviewAPITestCase):
    
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.review1 = Review.objects.create(business_user=cls.business_user1, reviewer=cls.customer_user, rating=4, description='Great service!')
        cls.review2 = Review.objects.create(business_user=cls.business_user1, reviewer=cls.reviewer2, rating=5, description='Excellent work!')
        cls.review3 = Review.objects.create(business_user=cls.business_user2, reviewer=cls.customer_user, rating=3, description='Good but could be better.')
    
    def test_list_reviews_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        response = self.client.get(reverse('review-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
    
    def test_list_reviews_unauthenticated(self):
        response = self.client.get(reverse('review-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_reviews_filter_by_business_user(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = f"{reverse('review-list')}?business_user_id={self.business_user1.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        for review in response.data:
            self.assertEqual(review['business_user'], self.business_user1.id)
    
    def test_list_reviews_filter_by_reviewer(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = f"{reverse('review-list')}?reviewer_id={self.customer_user.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        for review in response.data:
            self.assertEqual(review['reviewer'], self.customer_user.id)
    
    def test_list_reviews_ordering_by_rating(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = f"{reverse('review-list')}?ordering=rating"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['rating'], 5)
    
    def test_list_reviews_has_required_fields(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        response = self.client.get(reverse('review-list'))
        required_fields = ['id', 'business_user', 'reviewer', 'rating', 'description', 'created_at', 'updated_at']
        for review in response.data:
            for field in required_fields:
                self.assertIn(field, review)


class ReviewCreateTests(ReviewAPITestCase):
    
    def test_create_review_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        data = {'business_user': self.business_user1.id, 'rating': 4, 'description': 'Very professional service!'}
        response = self.client.post(reverse('review-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['business_user'], self.business_user1.id)
        self.assertEqual(response.data['reviewer'], self.customer_user.id)
        self.assertEqual(response.data['rating'], 4)
        self.assertEqual(response.data['description'], 'Very professional service!')
    
    def test_create_review_unauthenticated(self):
        data = {'business_user': self.business_user1.id, 'rating': 4, 'description': 'Test'}
        response = self.client.post(reverse('review-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_review_invalid_rating(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        data = {'business_user': self.business_user1.id, 'rating': 6, 'description': 'Test'}
        response = self.client.post(reverse('review-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_review_cannot_review_self(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token1.key}')
        data = {'business_user': self.business_user1.id, 'rating': 5, 'description': 'I am great!'}
        response = self.client.post(reverse('review-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_review_missing_fields(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        data = {'rating': 4}
        response = self.client.post(reverse('review-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_review_only_customer_can_review(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token2.key}')
        data = {'business_user': self.business_user1.id, 'rating': 4, 'description': 'Test review'}
        response = self.client.post(reverse('review-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('customer profile', str(response.data).lower())
    
    def test_create_review_duplicate_not_allowed(self):
        Review.objects.create(business_user=self.business_user1, reviewer=self.customer_user, rating=4, description='First review')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        data = {'business_user': self.business_user1.id, 'rating': 5, 'description': 'Trying to add another review'}
        response = self.client.post(reverse('review-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already reviewed', str(response.data).lower())


class ReviewUpdateTests(ReviewAPITestCase):
    
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.review = Review.objects.create(business_user=cls.business_user1, reviewer=cls.customer_user, rating=3, description='Original review')
    
    def test_update_review_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = reverse('review-detail', kwargs={'id': self.review.id})
        data = {'rating': 5, 'description': 'Updated review - much better!'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['rating'], 5)
        self.assertEqual(response.data['description'], 'Updated review - much better!')
    
    def test_update_review_unauthenticated(self):
        url = reverse('review-detail', kwargs={'id': self.review.id})
        data = {'rating': 5}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_update_review_not_owner(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.reviewer2_token.key}')
        url = reverse('review-detail', kwargs={'id': self.review.id})
        data = {'rating': 1}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_update_review_not_found(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = reverse('review-detail', kwargs={'id': 99999})
        data = {'rating': 5}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_review_invalid_rating(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = reverse('review-detail', kwargs={'id': self.review.id})
        data = {'rating': 0}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ReviewDeleteTests(ReviewAPITestCase):
    
    def test_delete_review_success(self):
        review = Review.objects.create(business_user=self.business_user1, reviewer=self.customer_user, rating=4, description='To be deleted')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = reverse('review-detail', kwargs={'id': review.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Review.objects.filter(id=review.id).exists())
    
    def test_delete_review_unauthenticated(self):
        review = Review.objects.create(business_user=self.business_user1, reviewer=self.customer_user, rating=4, description='Test')
        url = reverse('review-detail', kwargs={'id': review.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(Review.objects.filter(id=review.id).exists())
    
    def test_delete_review_not_owner(self):
        review = Review.objects.create(business_user=self.business_user1, reviewer=self.customer_user, rating=4, description='Test')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.reviewer2_token.key}')
        url = reverse('review-detail', kwargs={'id': review.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Review.objects.filter(id=review.id).exists())
    
    def test_delete_review_not_found(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = reverse('review-detail', kwargs={'id': 99999})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


