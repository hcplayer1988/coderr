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
        self.client = APIClient()
        self.business1 = User.objects.create_user(username='business1', email='business1@test.com', password='TestPass123!', type='business')
        self.business1.profile.first_name = 'John'
        self.business1.profile.last_name = 'Doe'
        self.business1.profile.save()
        self.business2 = User.objects.create_user(username='business2', email='business2@test.com', password='TestPass123!', type='business')
        self.business2.profile.first_name = 'Jane'
        self.business2.profile.last_name = 'Smith'
        self.business2.profile.save()
        self.customer = User.objects.create_user(username='customer1', email='customer1@test.com', password='TestPass123!', type='customer')
        self.offer1 = Offer.objects.create(user=self.business1, title='Website Design', description='Professional website design services')
        self.offer2 = Offer.objects.create(user=self.business1, title='Logo Design', description='Creative logo design')
        self.offer3 = Offer.objects.create(user=self.business2, title='Mobile App Development', description='iOS and Android app development')
        OfferDetail.objects.create(offer=self.offer1, title='Basic Package', revisions=2, delivery_time_in_days=7, price=Decimal('100.00'), features='Basic features', offer_type='basic')
        OfferDetail.objects.create(offer=self.offer1, title='Premium Package', revisions=5, delivery_time_in_days=14, price=Decimal('250.00'), features='Premium features', offer_type='premium')
        OfferDetail.objects.create(offer=self.offer2, title='Standard Package', revisions=3, delivery_time_in_days=5, price=Decimal('150.00'), features='Standard features', offer_type='standard')
        OfferDetail.objects.create(offer=self.offer3, title='Basic App', revisions=2, delivery_time_in_days=30, price=Decimal('2000.00'), features='Basic mobile app', offer_type='basic')

    def test_list_offers_success(self):
        url = reverse('offer-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

    def test_list_offers_has_required_fields(self):
        url = reverse('offer-list')
        response = self.client.get(url)
        required_fields = ['id', 'user', 'title', 'image', 'description', 'created_at', 'updated_at', 'details', 'min_price', 'min_delivery_time', 'user_details']
        for offer in response.data['results']:
            for field in required_fields:
                self.assertIn(field, offer)

    def test_list_offers_user_details_structure(self):
        url = reverse('offer-list')
        response = self.client.get(url)
        user_details = response.data['results'][0]['user_details']
        self.assertIn('id', user_details)
        self.assertIn('first_name', user_details)
        self.assertIn('last_name', user_details)
        self.assertIn('username', user_details)

    def test_list_offers_min_price_calculation(self):
        url = reverse('offer-list')
        response = self.client.get(url)
        offer1_data = next(o for o in response.data['results'] if o['id'] == self.offer1.id)
        self.assertEqual(float(offer1_data['min_price']), 100.00)

    def test_list_offers_min_delivery_time_calculation(self):
        url = reverse('offer-list')
        response = self.client.get(url)
        offer1_data = next(o for o in response.data['results'] if o['id'] == self.offer1.id)
        self.assertEqual(offer1_data['min_delivery_time'], 7)

    def test_filter_by_creator_id(self):
        url = reverse('offer-list')
        response = self.client.get(url, {'creator_id': self.business1.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_filter_by_min_price(self):
        url = reverse('offer-list')
        response = self.client.get(url, {'min_price': 200})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_by_max_delivery_time(self):
        url = reverse('offer-list')
        response = self.client.get(url, {'max_delivery_time': 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_by_title(self):
        url = reverse('offer-list')
        response = self.client.get(url, {'search': 'Website'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 1)

    def test_search_by_description(self):
        url = reverse('offer-list')
        response = self.client.get(url, {'search': 'Creative'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_ordering_by_updated_at(self):
        url = reverse('offer-list')
        response = self.client.get(url, {'ordering': 'updated_at'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_ordering_by_updated_at_desc(self):
        url = reverse('offer-list')
        response = self.client.get(url, {'ordering': '-updated_at'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_pagination_with_page_size(self):
        url = reverse('offer-list')
        response = self.client.get(url, {'page_size': 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_pagination_next_page(self):
        url = reverse('offer-list')
        response1 = self.client.get(url, {'page_size': 2, 'page': 1})
        response2 = self.client.get(url, {'page_size': 2, 'page': 2})
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

    def test_combined_filters(self):
        url = reverse('offer-list')
        response = self.client.get(url, {'creator_id': self.business1.id, 'min_price': 100, 'search': 'Design'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_details_urls_in_response(self):
        url = reverse('offer-list')
        response = self.client.get(url)
        first_offer = response.data['results'][0]
        self.assertIsInstance(first_offer['details'], list)


class OfferCreateTests(APITestCase):
    """Test cases for offer create endpoint (POST)."""
    
    def setUp(self):
        self.client = APIClient()
        self.business_user = User.objects.create_user(username='business1', email='business1@test.com', password='TestPass123!', type='business')
        self.business_user.profile.first_name = 'John'
        self.business_user.profile.last_name = 'Doe'
        self.business_user.profile.save()
        self.business_token = Token.objects.create(user=self.business_user)
        self.customer_user = User.objects.create_user(username='customer1', email='customer1@test.com', password='TestPass123!', type='customer')
        self.customer_token = Token.objects.create(user=self.customer_user)
        self.valid_offer_data = {
            'title': 'Website Design',
            'description': 'Professional website design services',
            'details': [
                {'title': 'Basic Package', 'revisions': 2, 'delivery_time_in_days': 7, 'price': '100.00', 'features': 'Basic website design', 'offer_type': 'basic'},
                {'title': 'Premium Package', 'revisions': 5, 'delivery_time_in_days': 14, 'price': '250.00', 'features': 'Premium website design', 'offer_type': 'premium'}
            ]
        }

    def test_create_offer_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-list')
        response = self.client.post(url, self.valid_offer_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)

    def test_create_offer_response_structure(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-list')
        response = self.client.post(url, self.valid_offer_data, format='json')
        required_fields = ['id', 'user', 'title', 'image', 'description', 'created_at', 'updated_at', 'details', 'min_price', 'min_delivery_time', 'user_details']
        for field in required_fields:
            self.assertIn(field, response.data)

    def test_create_offer_min_values_calculated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-list')
        response = self.client.post(url, self.valid_offer_data, format='json')
        self.assertEqual(float(response.data['min_price']), 100.00)
        self.assertEqual(response.data['min_delivery_time'], 7)

    def test_create_offer_user_details_included(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-list')
        response = self.client.post(url, self.valid_offer_data, format='json')
        self.assertIn('user_details', response.data)

    def test_create_offer_unauthenticated(self):
        url = reverse('offer-list')
        response = self.client.post(url, self.valid_offer_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_offer_customer_forbidden(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = reverse('offer-list')
        response = self.client.post(url, self.valid_offer_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_offer_missing_title(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-list')
        data = self.valid_offer_data.copy()
        del data['title']
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_offer_missing_description(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-list')
        data = self.valid_offer_data.copy()
        del data['description']
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_offer_missing_details(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-list')
        data = self.valid_offer_data.copy()
        del data['details']
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_offer_empty_details(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-list')
        data = self.valid_offer_data.copy()
        data['details'] = []
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_offer_single_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-list')
        data = {'title': 'Logo Design', 'description': 'Professional logo design', 'details': [{'title': 'Standard Package', 'revisions': 3, 'delivery_time_in_days': 5, 'price': '150.00', 'features': 'Logo design', 'offer_type': 'standard'}]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_offer_invalid_price(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-list')
        data = self.valid_offer_data.copy()
        data['details'][0]['price'] = 'invalid'
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_offer_negative_price(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-list')
        data = self.valid_offer_data.copy()
        data['details'][0]['price'] = '-50.00'
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_offer_without_image(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-list')
        response = self.client.post(url, self.valid_offer_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class OfferDetailViewTests(APITestCase):
    """Test cases for single offer detail endpoint (GET)."""
    
    def setUp(self):
        self.client = APIClient()
        self.business_user = User.objects.create_user(username='business1', email='business1@test.com', password='TestPass123!', type='business')
        self.business_user.profile.first_name = 'John'
        self.business_user.profile.last_name = 'Doe'
        self.business_user.profile.save()
        self.business_token = Token.objects.create(user=self.business_user)
        self.customer_user = User.objects.create_user(username='customer1', email='customer1@test.com', password='TestPass123!', type='customer')
        self.customer_token = Token.objects.create(user=self.customer_user)
        self.offer = Offer.objects.create(user=self.business_user, title='Grafikdesign-Paket', description='Ein umfassendes Grafikdesign-Paket für Unternehmen')
        self.detail1 = OfferDetail.objects.create(offer=self.offer, title='Basic Package', revisions=2, delivery_time_in_days=5, price=Decimal('50.00'), features='Basic design', offer_type='basic')
        self.detail2 = OfferDetail.objects.create(offer=self.offer, title='Premium Package', revisions=5, delivery_time_in_days=10, price=Decimal('200.00'), features='Premium design', offer_type='premium')
        self.detail3 = OfferDetail.objects.create(offer=self.offer, title='Enterprise Package', revisions=10, delivery_time_in_days=15, price=Decimal('201.00'), features='Enterprise design', offer_type='enterprise')

    def test_get_offer_detail_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.offer.id)

    def test_get_offer_detail_has_all_fields(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        response = self.client.get(url)
        required_fields = ['id', 'user', 'title', 'image', 'description', 'created_at', 'updated_at', 'details', 'min_price', 'min_delivery_time']
        for field in required_fields:
            self.assertIn(field, response.data)

    def test_get_offer_detail_has_details_array(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        response = self.client.get(url)
        self.assertIsInstance(response.data['details'], list)
        self.assertEqual(len(response.data['details']), 3)

    def test_get_offer_detail_min_values(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        response = self.client.get(url)
        self.assertEqual(float(response.data['min_price']), 50.00)
        self.assertEqual(response.data['min_delivery_time'], 5)

    def test_get_offer_detail_unauthenticated(self):
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_offer_detail_not_found(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_offer_detail_customer_can_view(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_offer_detail_another_business_can_view(self):
        other_business = User.objects.create_user(username='business2', email='business2@test.com', password='TestPass123!', type='business')
        other_token = Token.objects.create(user=other_business)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {other_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class OfferUpdateTests(APITestCase):
    """Test cases for offer update endpoint (PATCH)."""
    
    def setUp(self):
        self.client = APIClient()
        self.business_user = User.objects.create_user(username='business1', email='business1@test.com', password='TestPass123!', type='business')
        self.business_user.profile.first_name = 'John'
        self.business_user.profile.last_name = 'Doe'
        self.business_user.profile.save()
        self.business_token = Token.objects.create(user=self.business_user)
        self.other_business = User.objects.create_user(username='business2', email='business2@test.com', password='TestPass123!', type='business')
        self.other_business_token = Token.objects.create(user=self.other_business)
        self.customer_user = User.objects.create_user(username='customer1', email='customer1@test.com', password='TestPass123!', type='customer')
        self.customer_token = Token.objects.create(user=self.customer_user)
        self.offer = Offer.objects.create(user=self.business_user, title='Grafikdesign-Paket', description='Ein umfassendes Grafikdesign-Paket für Unternehmen')
        self.detail1 = OfferDetail.objects.create(offer=self.offer, title='Basic Design', revisions=3, delivery_time_in_days=6, price=Decimal('120.00'), features='Logo Design, Flyer', offer_type='basic')
        self.detail2 = OfferDetail.objects.create(offer=self.offer, title='Standard Design', revisions=5, delivery_time_in_days=10, price=Decimal('120.00'), features='Logo Design, Visitenkarte, Briefpapier', offer_type='standard')
        self.detail3 = OfferDetail.objects.create(offer=self.offer, title='Premium Design', revisions=10, delivery_time_in_days=10, price=Decimal('150.00'), features='Logo Design, Visitenkarte, Briefpapier, Flyer', offer_type='premium')

    def test_update_offer_title_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        response = self.client.patch(url, {'title': 'Updated Grafikdesign-Paket'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Grafikdesign-Paket')

    def test_update_offer_description_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        response = self.client.patch(url, {'description': 'Updated description'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Updated description')

    def test_update_offer_title_and_description(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        response = self.client.patch(url, {'title': 'New Title', 'description': 'New Description'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'New Title')
        self.assertEqual(response.data['description'], 'New Description')

    def test_update_single_detail_field(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        data = {'details': [{'id': self.detail1.id, 'title': 'Basic Design Updated', 'revisions': 3, 'delivery_time_in_days': 6, 'price': '120.00', 'features': ['Logo Design', 'Flyer'], 'offer_type': 'basic'}]}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_multiple_details(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        data = {'details': [{'id': self.detail1.id, 'title': 'Basic Updated', 'revisions': 5, 'delivery_time_in_days': 8, 'price': '150.00', 'features': ['Logo Design', 'Flyer', 'Poster'], 'offer_type': 'basic'}, {'id': self.detail2.id, 'title': 'Standard Updated', 'revisions': 7, 'delivery_time_in_days': 12, 'price': '200.00', 'features': ['Logo Design', 'Visitenkarte', 'Briefpapier', 'Flyer'], 'offer_type': 'standard'}]}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_offer_min_values_recalculated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        data = {'details': [{'id': self.detail1.id, 'title': 'Basic Design', 'revisions': 3, 'delivery_time_in_days': 3, 'price': '50.00', 'features': ['Logo Design'], 'offer_type': 'basic'}]}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_offer_user_field_ignored(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        response = self.client.patch(url, {'title': 'Updated Title', 'user': self.other_business.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.user.id, self.business_user.id)

    def test_update_offer_details_unchanged_when_not_provided(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        initial_details_count = OfferDetail.objects.filter(offer=self.offer).count()
        response = self.client.patch(url, {'title': 'Updated Title Only'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['details']), initial_details_count)

    def test_update_offer_response_has_required_fields(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        response = self.client.patch(url, {'title': 'Updated Title'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('id', response.data)
        self.assertIn('title', response.data)
        self.assertIn('details', response.data)

    def test_update_offer_features_returned_as_array(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        response = self.client.patch(url, {'title': 'Updated'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for detail in response.data['details']:
            self.assertIsInstance(detail['features'], list)

    def test_update_offer_price_returned_as_integer(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        response = self.client.patch(url, {'title': 'Updated Title'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for detail in response.data['details']:
            self.assertIsInstance(detail['price'], int)

    def test_update_offer_unauthenticated(self):
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        response = self.client.patch(url, {'title': 'Should Fail'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_offer_not_owner_forbidden(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.other_business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        response = self.client.patch(url, {'title': 'Hacked Title'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_offer_customer_forbidden(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        response = self.client.patch(url, {'title': 'Customer Update'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_offer_not_found(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': 99999})
        response = self.client.patch(url, {'title': 'Not Found'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_detail_with_invalid_id(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        data = {'details': [{'id': 99999, 'title': 'Invalid Detail', 'revisions': 3, 'delivery_time_in_days': 5, 'price': '100.00', 'features': ['Test'], 'offer_type': 'basic'}]}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_offer_empty_title(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        response = self.client.patch(url, {'title': ''}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_detail_negative_price(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        data = {'details': [{'id': self.detail1.id, 'title': 'Basic', 'revisions': 3, 'delivery_time_in_days': 5, 'price': '-50.00', 'features': ['Test'], 'offer_type': 'basic'}]}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_detail_zero_delivery_time(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        data = {'details': [{'id': self.detail1.id, 'title': 'Basic', 'revisions': 3, 'delivery_time_in_days': 0, 'price': '100.00', 'features': ['Test'], 'offer_type': 'basic'}]}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class OfferDeleteTests(APITestCase):
    """Test cases for offer delete endpoint (DELETE)."""
    
    def setUp(self):
        self.client = APIClient()
        self.business_user = User.objects.create_user(username='business1', email='business1@test.com', password='TestPass123!', type='business')
        self.business_token = Token.objects.create(user=self.business_user)
        self.other_business = User.objects.create_user(username='business2', email='business2@test.com', password='TestPass123!', type='business')
        self.other_business_token = Token.objects.create(user=self.other_business)
        self.customer_user = User.objects.create_user(username='customer1', email='customer1@test.com', password='TestPass123!', type='customer')
        self.customer_token = Token.objects.create(user=self.customer_user)
        self.offer = Offer.objects.create(user=self.business_user, title='Test Offer', description='Test description')
        self.detail = OfferDetail.objects.create(offer=self.offer, title='Basic Package', revisions=3, delivery_time_in_days=7, price=Decimal('100.00'), features='Test features', offer_type='basic')

    def test_delete_offer_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        offer_id = self.offer.id
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Offer.objects.filter(id=offer_id).exists())

    def test_delete_offer_cascades_to_details(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        detail_id = self.detail.id
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(OfferDetail.objects.filter(id=detail_id).exists())

    def test_delete_offer_returns_no_content(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(response.data)

    def test_delete_offer_unauthenticated(self):
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(Offer.objects.filter(id=self.offer.id).exists())

    def test_delete_offer_not_owner_forbidden(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.other_business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Offer.objects.filter(id=self.offer.id).exists())

    def test_delete_offer_customer_forbidden(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Offer.objects.filter(id=self.offer.id).exists())

    def test_delete_offer_not_found(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': 99999})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_offer_twice_returns_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        response1 = self.client.delete(url)
        self.assertEqual(response1.status_code, status.HTTP_204_NO_CONTENT)
        response2 = self.client.delete(url)
        self.assertEqual(response2.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_offer_with_multiple_details(self):
        OfferDetail.objects.create(offer=self.offer, title='Standard Package', revisions=5, delivery_time_in_days=10, price=Decimal('200.00'), features='Standard features', offer_type='standard')
        OfferDetail.objects.create(offer=self.offer, title='Premium Package', revisions=10, delivery_time_in_days=14, price=Decimal('350.00'), features='Premium features', offer_type='premium')
        self.assertEqual(OfferDetail.objects.filter(offer=self.offer).count(), 3)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offer-detail', kwargs={'id': self.offer.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(OfferDetail.objects.filter(offer_id=self.offer.id).count(), 0)


class OfferDetailSingleTests(APITestCase):
    """Test cases for single offer detail endpoint (GET /api/offerdetails/{id}/)."""
    
    def setUp(self):
        self.client = APIClient()
        self.business_user = User.objects.create_user(username='business1', email='business1@test.com', password='TestPass123!', type='business')
        self.business_token = Token.objects.create(user=self.business_user)
        self.customer_user = User.objects.create_user(username='customer1', email='customer1@test.com', password='TestPass123!', type='customer')
        self.customer_token = Token.objects.create(user=self.customer_user)
        self.offer = Offer.objects.create(user=self.business_user, title='Test Offer', description='Test description')
        self.detail = OfferDetail.objects.create(offer=self.offer, title='Basic Design', revisions=2, delivery_time_in_days=5, price=Decimal('100.00'), features='Logo Design, Visitenkarte', offer_type='basic')

    def test_get_offerdetail_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offerdetail-single', kwargs={'id': self.detail.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.detail.id)
        self.assertEqual(response.data['title'], 'Basic Design')

    def test_get_offerdetail_has_all_fields(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offerdetail-single', kwargs={'id': self.detail.id})
        response = self.client.get(url)
        required_fields = ['id', 'title', 'revisions', 'delivery_time_in_days', 'price', 'features', 'offer_type']
        for field in required_fields:
            self.assertIn(field, response.data)

    def test_get_offerdetail_features_is_array(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offerdetail-single', kwargs={'id': self.detail.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data['features'], list)
        self.assertEqual(response.data['features'], ['Logo Design', 'Visitenkarte'])

    def test_get_offerdetail_price_is_integer(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offerdetail-single', kwargs={'id': self.detail.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data['price'], int)
        self.assertEqual(response.data['price'], 100)

    def test_get_offerdetail_customer_can_view(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        url = reverse('offerdetail-single', kwargs={'id': self.detail.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.detail.id)

    def test_get_offerdetail_other_business_can_view(self):
        other_business = User.objects.create_user(username='business2', email='business2@test.com', password='TestPass123!', type='business')
        other_token = Token.objects.create(user=other_business)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {other_token.key}')
        url = reverse('offerdetail-single', kwargs={'id': self.detail.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_offerdetail_correct_values(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offerdetail-single', kwargs={'id': self.detail.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.detail.id)
        self.assertEqual(response.data['title'], 'Basic Design')
        self.assertEqual(response.data['revisions'], 2)
        self.assertEqual(response.data['delivery_time_in_days'], 5)
        self.assertEqual(response.data['price'], 100)
        self.assertEqual(response.data['features'], ['Logo Design', 'Visitenkarte'])
        self.assertEqual(response.data['offer_type'], 'basic')

    def test_get_offerdetail_unauthenticated(self):
        url = reverse('offerdetail-single', kwargs={'id': self.detail.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_offerdetail_not_found(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offerdetail-single', kwargs={'id': 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_offerdetail_empty_features(self):
        detail_empty = OfferDetail.objects.create(offer=self.offer, title='Empty Features', revisions=1, delivery_time_in_days=3, price=Decimal('50.00'), features='', offer_type='basic')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offerdetail-single', kwargs={'id': detail_empty.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['features'], [])

    def test_get_offerdetail_multiple_features(self):
        detail_multi = OfferDetail.objects.create(offer=self.offer, title='Multi Features', revisions=5, delivery_time_in_days=10, price=Decimal('200.00'), features='Logo Design, Visitenkarte, Briefpapier, Flyer, Poster', offer_type='premium')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        url = reverse('offerdetail-single', kwargs={'id': detail_multi.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['features']), 5)
        self.assertIn('Logo Design', response.data['features'])
        self.assertIn('Poster', response.data['features'])
        
