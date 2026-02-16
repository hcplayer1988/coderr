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
    
    @classmethod
    def setUpTestData(cls):
        cls.business1 = User.objects.create_user(username='business1', email='business1@test.com', password='TestPass123!', type='business')
        cls.business1.profile.first_name = 'John'
        cls.business1.profile.last_name = 'Doe'
        cls.business1.profile.save()
        cls.business2 = User.objects.create_user(username='business2', email='business2@test.com', password='TestPass123!', type='business')
        cls.business2.profile.first_name = 'Jane'
        cls.business2.profile.last_name = 'Smith'
        cls.business2.profile.save()
        cls.customer = User.objects.create_user(username='customer1', email='customer1@test.com', password='TestPass123!', type='customer')
        cls.offer1 = Offer.objects.create(user=cls.business1, title='Website Design', description='Professional website design services')
        cls.offer2 = Offer.objects.create(user=cls.business1, title='Logo Design', description='Creative logo design')
        cls.offer3 = Offer.objects.create(user=cls.business2, title='Mobile App Development', description='iOS and Android app development')
        OfferDetail.objects.create(offer=cls.offer1, title='Basic Package', revisions=2, delivery_time_in_days=7, price=Decimal('100.00'), features='Basic features', offer_type='basic')
        OfferDetail.objects.create(offer=cls.offer1, title='Premium Package', revisions=5, delivery_time_in_days=14, price=Decimal('250.00'), features='Premium features', offer_type='premium')
        OfferDetail.objects.create(offer=cls.offer2, title='Standard Package', revisions=3, delivery_time_in_days=5, price=Decimal('150.00'), features='Standard features', offer_type='standard')
        OfferDetail.objects.create(offer=cls.offer3, title='Basic App', revisions=2, delivery_time_in_days=30, price=Decimal('2000.00'), features='Basic mobile app', offer_type='basic')
    
    def setUp(self):
        self.client = APIClient()

    def test_list_offers_success(self):
        response = self.client.get(reverse('offer-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

    def test_list_offers_has_required_fields(self):
        response = self.client.get(reverse('offer-list'))
        required_fields = ['id', 'user', 'title', 'image', 'description', 'created_at', 'updated_at', 'details', 'min_price', 'min_delivery_time', 'user_details']
        for offer in response.data['results']:
            for field in required_fields:
                self.assertIn(field, offer)

    def test_list_offers_user_details_structure(self):
        response = self.client.get(reverse('offer-list'))
        user_details = response.data['results'][0]['user_details']
        self.assertIn('id', user_details)
        self.assertIn('first_name', user_details)
        self.assertIn('last_name', user_details)
        self.assertIn('username', user_details)

    def test_list_offers_min_price_calculation(self):
        response = self.client.get(reverse('offer-list'))
        offer1_data = next(o for o in response.data['results'] if o['id'] == self.offer1.id)
        self.assertEqual(float(offer1_data['min_price']), 100.00)

    def test_list_offers_min_delivery_time_calculation(self):
        response = self.client.get(reverse('offer-list'))
        offer1_data = next(o for o in response.data['results'] if o['id'] == self.offer1.id)
        self.assertEqual(offer1_data['min_delivery_time'], 7)

    def test_filter_by_creator_id(self):
        response = self.client.get(reverse('offer-list'), {'creator_id': self.business1.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_filter_by_min_price(self):
        response = self.client.get(reverse('offer-list'), {'min_price': 200})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_by_max_delivery_time(self):
        response = self.client.get(reverse('offer-list'), {'max_delivery_time': 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_by_title(self):
        response = self.client.get(reverse('offer-list'), {'search': 'Website'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 1)

    def test_search_by_description(self):
        response = self.client.get(reverse('offer-list'), {'search': 'Creative'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_ordering_by_updated_at(self):
        response = self.client.get(reverse('offer-list'), {'ordering': 'updated_at'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_ordering_by_updated_at_desc(self):
        response = self.client.get(reverse('offer-list'), {'ordering': '-updated_at'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_pagination_with_page_size(self):
        response = self.client.get(reverse('offer-list'), {'page_size': 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_pagination_next_page(self):
        response1 = self.client.get(reverse('offer-list'), {'page_size': 2, 'page': 1})
        response2 = self.client.get(reverse('offer-list'), {'page_size': 2, 'page': 2})
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

    def test_combined_filters(self):
        response = self.client.get(reverse('offer-list'), {'creator_id': self.business1.id, 'min_price': 100, 'search': 'Design'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_details_urls_in_response(self):
        response = self.client.get(reverse('offer-list'))
        first_offer = response.data['results'][0]
        self.assertIsInstance(first_offer['details'], list)


class OfferCreateTests(APITestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.business_user = User.objects.create_user(username='business1', email='business1@test.com', password='TestPass123!', type='business')
        cls.business_user.profile.first_name = 'John'
        cls.business_user.profile.last_name = 'Doe'
        cls.business_user.profile.save()
        cls.business_token = Token.objects.create(user=cls.business_user)
        cls.customer_user = User.objects.create_user(username='customer1', email='customer1@test.com', password='TestPass123!', type='customer')
        cls.customer_token = Token.objects.create(user=cls.customer_user)
        cls.valid_offer_data = {
            'title': 'Website Design',
            'description': 'Professional website design services',
            'details': [
                {'title': 'Basic Package', 'revisions': 2, 'delivery_time_in_days': 7, 'price': '100.00', 'features': 'Basic website design', 'offer_type': 'basic'},
                {'title': 'Premium Package', 'revisions': 5, 'delivery_time_in_days': 14, 'price': '250.00', 'features': 'Premium website design', 'offer_type': 'premium'}
            ]
        }
    
    def setUp(self):
        self.client = APIClient()

    def test_create_offer_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        response = self.client.post(reverse('offer-list'), self.valid_offer_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)

    def test_create_offer_response_structure(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        response = self.client.post(reverse('offer-list'), self.valid_offer_data, format='json')
        required_fields = ['id', 'user', 'title', 'image', 'description', 'created_at', 'updated_at', 'details', 'min_price', 'min_delivery_time', 'user_details']
        for field in required_fields:
            self.assertIn(field, response.data)

    def test_create_offer_min_values_calculated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        response = self.client.post(reverse('offer-list'), self.valid_offer_data, format='json')
        self.assertEqual(float(response.data['min_price']), 100.00)
        self.assertEqual(response.data['min_delivery_time'], 7)

    def test_create_offer_user_details_included(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        response = self.client.post(reverse('offer-list'), self.valid_offer_data, format='json')
        self.assertIn('user_details', response.data)

    def test_create_offer_unauthenticated(self):
        response = self.client.post(reverse('offer-list'), self.valid_offer_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_offer_customer_forbidden(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        response = self.client.post(reverse('offer-list'), self.valid_offer_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_offer_missing_title(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        data = self.valid_offer_data.copy()
        del data['title']
        response = self.client.post(reverse('offer-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_offer_missing_description(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        data = self.valid_offer_data.copy()
        del data['description']
        response = self.client.post(reverse('offer-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_offer_missing_details(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        data = self.valid_offer_data.copy()
        del data['details']
        response = self.client.post(reverse('offer-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_offer_empty_details(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        data = self.valid_offer_data.copy()
        data['details'] = []
        response = self.client.post(reverse('offer-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_offer_single_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        data = {'title': 'Logo Design', 'description': 'Professional logo design', 'details': [{'title': 'Standard Package', 'revisions': 3, 'delivery_time_in_days': 5, 'price': '150.00', 'features': 'Logo design', 'offer_type': 'standard'}]}
        response = self.client.post(reverse('offer-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_offer_invalid_price(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        data = self.valid_offer_data.copy()
        data['details'][0]['price'] = 'invalid'
        response = self.client.post(reverse('offer-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_offer_negative_price(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        data = self.valid_offer_data.copy()
        data['details'][0]['price'] = '-50.00'
        response = self.client.post(reverse('offer-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_offer_without_image(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        response = self.client.post(reverse('offer-list'), self.valid_offer_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class OfferDetailViewTests(APITestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.business_user = User.objects.create_user(username='business1', email='business1@test.com', password='TestPass123!', type='business')
        cls.business_user.profile.first_name = 'John'
        cls.business_user.profile.last_name = 'Doe'
        cls.business_user.profile.save()
        cls.business_token = Token.objects.create(user=cls.business_user)
        cls.customer_user = User.objects.create_user(username='customer1', email='customer1@test.com', password='TestPass123!', type='customer')
        cls.customer_token = Token.objects.create(user=cls.customer_user)
        cls.offer = Offer.objects.create(user=cls.business_user, title='Grafikdesign-Paket', description='Ein umfassendes Grafikdesign-Paket für Unternehmen')
        cls.detail1 = OfferDetail.objects.create(offer=cls.offer, title='Basic Package', revisions=2, delivery_time_in_days=5, price=Decimal('50.00'), features='Basic design', offer_type='basic')
        cls.detail2 = OfferDetail.objects.create(offer=cls.offer, title='Premium Package', revisions=5, delivery_time_in_days=10, price=Decimal('200.00'), features='Premium design', offer_type='premium')
        cls.detail3 = OfferDetail.objects.create(offer=cls.offer, title='Enterprise Package', revisions=10, delivery_time_in_days=15, price=Decimal('201.00'), features='Enterprise design', offer_type='enterprise')
    
    def setUp(self):
        self.client = APIClient()

    def test_get_offer_detail_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        response = self.client.get(reverse('offer-detail', kwargs={'id': self.offer.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.offer.id)

    def test_get_offer_detail_has_all_fields(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        response = self.client.get(reverse('offer-detail', kwargs={'id': self.offer.id}))
        required_fields = ['id', 'user', 'title', 'image', 'description', 'created_at', 'updated_at', 'details', 'min_price', 'min_delivery_time']
        for field in required_fields:
            self.assertIn(field, response.data)

    def test_get_offer_detail_has_details_array(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        response = self.client.get(reverse('offer-detail', kwargs={'id': self.offer.id}))
        self.assertIsInstance(response.data['details'], list)
        self.assertEqual(len(response.data['details']), 3)

    def test_get_offer_detail_min_values(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        response = self.client.get(reverse('offer-detail', kwargs={'id': self.offer.id}))
        self.assertEqual(float(response.data['min_price']), 50.00)
        self.assertEqual(response.data['min_delivery_time'], 5)

    def test_get_offer_detail_unauthenticated(self):
        response = self.client.get(reverse('offer-detail', kwargs={'id': self.offer.id}))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_offer_detail_not_found(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        response = self.client.get(reverse('offer-detail', kwargs={'id': 99999}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_offer_detail_customer_can_view(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        response = self.client.get(reverse('offer-detail', kwargs={'id': self.offer.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_offer_detail_another_business_can_view(self):
        other_business = User.objects.create_user(username='business2', email='business2@test.com', password='TestPass123!', type='business')
        other_token = Token.objects.create(user=other_business)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {other_token.key}')
        response = self.client.get(reverse('offer-detail', kwargs={'id': self.offer.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class OfferUpdateTests(APITestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.business_user = User.objects.create_user(username='business1', email='business1@test.com', password='TestPass123!', type='business')
        cls.business_user.profile.first_name = 'John'
        cls.business_user.profile.last_name = 'Doe'
        cls.business_user.profile.save()
        cls.business_token = Token.objects.create(user=cls.business_user)
        cls.other_business = User.objects.create_user(username='business2', email='business2@test.com', password='TestPass123!', type='business')
        cls.other_business_token = Token.objects.create(user=cls.other_business)
        cls.customer_user = User.objects.create_user(username='customer1', email='customer1@test.com', password='TestPass123!', type='customer')
        cls.customer_token = Token.objects.create(user=cls.customer_user)
    
    def setUp(self):
        self.offer = Offer.objects.create(user=self.business_user, title='Grafikdesign-Paket', description='Ein umfassendes Grafikdesign-Paket für Unternehmen')
        self.detail1 = OfferDetail.objects.create(offer=self.offer, title='Basic Design', revisions=3, delivery_time_in_days=6, price=Decimal('120.00'), features='Logo Design, Flyer', offer_type='basic')
        self.detail2 = OfferDetail.objects.create(offer=self.offer, title='Standard Design', revisions=5, delivery_time_in_days=10, price=Decimal('120.00'), features='Logo Design, Visitenkarte, Briefpapier', offer_type='standard')
        self.detail3 = OfferDetail.objects.create(offer=self.offer, title='Premium Design', revisions=10, delivery_time_in_days=10, price=Decimal('150.00'), features='Logo Design, Visitenkarte, Briefpapier, Flyer', offer_type='premium')
        self.client = APIClient()

    def test_update_offer_title_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        response = self.client.patch(reverse('offer-detail', kwargs={'id': self.offer.id}), {'title': 'Updated Grafikdesign-Paket'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Grafikdesign-Paket')

    def test_update_offer_description_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        response = self.client.patch(reverse('offer-detail', kwargs={'id': self.offer.id}), {'description': 'Updated description'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Updated description')

    def test_update_offer_title_and_description(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        response = self.client.patch(reverse('offer-detail', kwargs={'id': self.offer.id}), {'title': 'New Title', 'description': 'New Description'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'New Title')
        self.assertEqual(response.data['description'], 'New Description')

    def test_update_offer_user_field_ignored(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        response = self.client.patch(reverse('offer-detail', kwargs={'id': self.offer.id}), {'title': 'Updated Title', 'user': self.other_business.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.user.id, self.business_user.id)

    def test_update_offer_unauthenticated(self):
        response = self.client.patch(reverse('offer-detail', kwargs={'id': self.offer.id}), {'title': 'Should Fail'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_offer_not_owner_forbidden(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.other_business_token.key}')
        response = self.client.patch(reverse('offer-detail', kwargs={'id': self.offer.id}), {'title': 'Hacked Title'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_offer_customer_forbidden(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        response = self.client.patch(reverse('offer-detail', kwargs={'id': self.offer.id}), {'title': 'Customer Update'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_offer_not_found(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        response = self.client.patch(reverse('offer-detail', kwargs={'id': 99999}), {'title': 'Not Found'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_offer_empty_title(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        response = self.client.patch(reverse('offer-detail', kwargs={'id': self.offer.id}), {'title': ''}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class OfferDeleteTests(APITestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.business_user = User.objects.create_user(username='business1', email='business1@test.com', password='TestPass123!', type='business')
        cls.business_token = Token.objects.create(user=cls.business_user)
        cls.other_business = User.objects.create_user(username='business2', email='business2@test.com', password='TestPass123!', type='business')
        cls.other_business_token = Token.objects.create(user=cls.other_business)
        cls.customer_user = User.objects.create_user(username='customer1', email='customer1@test.com', password='TestPass123!', type='customer')
        cls.customer_token = Token.objects.create(user=cls.customer_user)
    
    def setUp(self):
        self.offer = Offer.objects.create(user=self.business_user, title='Test Offer', description='Test description')
        self.detail = OfferDetail.objects.create(offer=self.offer, title='Basic Package', revisions=3, delivery_time_in_days=7, price=Decimal('100.00'), features='Test features', offer_type='basic')
        self.client = APIClient()

    def test_delete_offer_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        offer_id = self.offer.id
        response = self.client.delete(reverse('offer-detail', kwargs={'id': self.offer.id}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Offer.objects.filter(id=offer_id).exists())

    def test_delete_offer_cascades_to_details(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        detail_id = self.detail.id
        response = self.client.delete(reverse('offer-detail', kwargs={'id': self.offer.id}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(OfferDetail.objects.filter(id=detail_id).exists())

    def test_delete_offer_returns_no_content(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        response = self.client.delete(reverse('offer-detail', kwargs={'id': self.offer.id}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(response.data)

    def test_delete_offer_unauthenticated(self):
        response = self.client.delete(reverse('offer-detail', kwargs={'id': self.offer.id}))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(Offer.objects.filter(id=self.offer.id).exists())

    def test_delete_offer_not_owner_forbidden(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.other_business_token.key}')
        response = self.client.delete(reverse('offer-detail', kwargs={'id': self.offer.id}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Offer.objects.filter(id=self.offer.id).exists())

    def test_delete_offer_customer_forbidden(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        response = self.client.delete(reverse('offer-detail', kwargs={'id': self.offer.id}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Offer.objects.filter(id=self.offer.id).exists())

    def test_delete_offer_not_found(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        response = self.client.delete(reverse('offer-detail', kwargs={'id': 99999}))
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
        response = self.client.delete(reverse('offer-detail', kwargs={'id': self.offer.id}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(OfferDetail.objects.filter(offer_id=self.offer.id).count(), 0)


class OfferDetailSingleTests(APITestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.business_user = User.objects.create_user(username='business1', email='business1@test.com', password='TestPass123!', type='business')
        cls.business_token = Token.objects.create(user=cls.business_user)
        cls.customer_user = User.objects.create_user(username='customer1', email='customer1@test.com', password='TestPass123!', type='customer')
        cls.customer_token = Token.objects.create(user=cls.customer_user)
        cls.offer = Offer.objects.create(user=cls.business_user, title='Test Offer', description='Test description')
        cls.detail = OfferDetail.objects.create(offer=cls.offer, title='Basic Design', revisions=2, delivery_time_in_days=5, price=Decimal('100.00'), features='Logo Design, Visitenkarte', offer_type='basic')
    
    def setUp(self):
        self.client = APIClient()

    def test_get_offerdetail_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        response = self.client.get(reverse('offerdetail-single', kwargs={'id': self.detail.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.detail.id)
        self.assertEqual(response.data['title'], 'Basic Design')

    def test_get_offerdetail_has_all_fields(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        response = self.client.get(reverse('offerdetail-single', kwargs={'id': self.detail.id}))
        required_fields = ['id', 'title', 'revisions', 'delivery_time_in_days', 'price', 'features', 'offer_type']
        for field in required_fields:
            self.assertIn(field, response.data)

    def test_get_offerdetail_features_is_array(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        response = self.client.get(reverse('offerdetail-single', kwargs={'id': self.detail.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data['features'], list)
        self.assertEqual(response.data['features'], ['Logo Design', 'Visitenkarte'])

    def test_get_offerdetail_price_is_integer(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        response = self.client.get(reverse('offerdetail-single', kwargs={'id': self.detail.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data['price'], int)
        self.assertEqual(response.data['price'], 100)

    def test_get_offerdetail_customer_can_view(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        response = self.client.get(reverse('offerdetail-single', kwargs={'id': self.detail.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.detail.id)

    def test_get_offerdetail_unauthenticated(self):
        response = self.client.get(reverse('offerdetail-single', kwargs={'id': self.detail.id}))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_offerdetail_not_found(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        response = self.client.get(reverse('offerdetail-single', kwargs={'id': 99999}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class OfferModelTests(APITestCase):
    """Tests for Offer model properties and methods."""
    
    @classmethod
    def setUpTestData(cls):
        cls.business_user = User.objects.create_user(username='business1', email='business1@test.com', password='TestPass123!', type='business')
        cls.customer_user = User.objects.create_user(username='customer1', email='customer1@test.com', password='TestPass123!', type='customer')
    
    def test_offer_str_method(self):
        """Test Offer __str__ method."""
        offer = Offer.objects.create(user=self.business_user, title='Website Design', description='Professional website design')
        expected_str = f"Website Design by {self.business_user.username}"
        self.assertEqual(str(offer), expected_str)
    
    def test_offer_min_price_with_details(self):
        """Test min_price property returns lowest price."""
        offer = Offer.objects.create(user=self.business_user, title='Design Services', description='Various design services')
        OfferDetail.objects.create(offer=offer, title='Basic', revisions=2, delivery_time_in_days=5, price=Decimal('100.00'), features='Basic', offer_type='basic')
        OfferDetail.objects.create(offer=offer, title='Standard', revisions=5, delivery_time_in_days=10, price=Decimal('250.00'), features='Standard', offer_type='standard')
        OfferDetail.objects.create(offer=offer, title='Premium', revisions=10, delivery_time_in_days=15, price=Decimal('500.00'), features='Premium', offer_type='premium')
        self.assertEqual(float(offer.min_price), 100.00)
    
    def test_offer_min_price_without_details(self):
        """Test min_price property returns 0 when no details exist."""
        offer = Offer.objects.create(user=self.business_user, title='Empty Offer', description='No details yet')
        self.assertEqual(offer.min_price, 0)
    
    def test_offer_min_delivery_time_with_details(self):
        """Test min_delivery_time property returns shortest delivery time."""
        offer = Offer.objects.create(user=self.business_user, title='Development Services', description='Software development')
        OfferDetail.objects.create(offer=offer, title='Quick', revisions=2, delivery_time_in_days=3, price=Decimal('200.00'), features='Quick delivery', offer_type='basic')
        OfferDetail.objects.create(offer=offer, title='Standard', revisions=5, delivery_time_in_days=7, price=Decimal('300.00'), features='Standard', offer_type='standard')
        OfferDetail.objects.create(offer=offer, title='Detailed', revisions=10, delivery_time_in_days=14, price=Decimal('500.00'), features='Detailed work', offer_type='premium')
        self.assertEqual(offer.min_delivery_time, 3)
    
    def test_offer_min_delivery_time_without_details(self):
        """Test min_delivery_time property returns 0 when no details exist."""
        offer = Offer.objects.create(user=self.business_user, title='Empty Offer', description='No details yet')
        self.assertEqual(offer.min_delivery_time, 0)
    
    def test_offer_min_price_single_detail(self):
        """Test min_price with only one detail."""
        offer = Offer.objects.create(user=self.business_user, title='Single Package', description='One package only')
        OfferDetail.objects.create(offer=offer, title='Only Package', revisions=5, delivery_time_in_days=7, price=Decimal('175.50'), features='All features', offer_type='standard')
        self.assertEqual(float(offer.min_price), 175.50)
    
    def test_offer_min_delivery_time_single_detail(self):
        """Test min_delivery_time with only one detail."""
        offer = Offer.objects.create(user=self.business_user, title='Single Package', description='One package only')
        OfferDetail.objects.create(offer=offer, title='Only Package', revisions=5, delivery_time_in_days=12, price=Decimal('200.00'), features='All features', offer_type='standard')
        self.assertEqual(offer.min_delivery_time, 12)
    
    def test_offer_min_price_updates_after_detail_added(self):
        """Test min_price updates when new cheaper detail is added."""
        offer = Offer.objects.create(user=self.business_user, title='Evolving Offer', description='Prices change')
        OfferDetail.objects.create(offer=offer, title='Expensive', revisions=10, delivery_time_in_days=15, price=Decimal('500.00'), features='Premium', offer_type='premium')
        self.assertEqual(float(offer.min_price), 500.00)
        OfferDetail.objects.create(offer=offer, title='Cheap', revisions=2, delivery_time_in_days=5, price=Decimal('50.00'), features='Basic', offer_type='basic')
        self.assertEqual(float(offer.min_price), 50.00)
    
    def test_offer_min_delivery_time_updates_after_detail_added(self):
        """Test min_delivery_time updates when new faster detail is added."""
        offer = Offer.objects.create(user=self.business_user, title='Evolving Offer', description='Delivery times change')
        OfferDetail.objects.create(offer=offer, title='Slow', revisions=10, delivery_time_in_days=20, price=Decimal('500.00'), features='Detailed', offer_type='premium')
        self.assertEqual(offer.min_delivery_time, 20)
        OfferDetail.objects.create(offer=offer, title='Fast', revisions=2, delivery_time_in_days=2, price=Decimal('200.00'), features='Quick', offer_type='basic')
        self.assertEqual(offer.min_delivery_time, 2)
    
    def test_offer_created_at_auto_set(self):
        """Test created_at is automatically set."""
        offer = Offer.objects.create(user=self.business_user, title='Test Offer', description='Test')
        self.assertIsNotNone(offer.created_at)
    
    def test_offer_updated_at_auto_set(self):
        """Test updated_at is automatically set."""
        offer = Offer.objects.create(user=self.business_user, title='Test Offer', description='Test')
        self.assertIsNotNone(offer.updated_at)
    
    def test_offer_ordering_by_created_at(self):
        """Test offers are ordered by created_at descending."""
        offer1 = Offer.objects.create(user=self.business_user, title='First Offer', description='First')
        offer2 = Offer.objects.create(user=self.business_user, title='Second Offer', description='Second')
        offer3 = Offer.objects.create(user=self.business_user, title='Third Offer', description='Third')
        offers = Offer.objects.all()
        self.assertEqual(offers[0].id, offer3.id)
        self.assertEqual(offers[1].id, offer2.id)
        self.assertEqual(offers[2].id, offer1.id)
    
    def test_offer_cascade_delete_details(self):
        """Test deleting offer cascades to details."""
        offer = Offer.objects.create(user=self.business_user, title='Test Offer', description='Test')
        detail1 = OfferDetail.objects.create(offer=offer, title='Detail 1', revisions=2, delivery_time_in_days=5, price=Decimal('100.00'), features='Features', offer_type='basic')
        detail2 = OfferDetail.objects.create(offer=offer, title='Detail 2', revisions=5, delivery_time_in_days=10, price=Decimal('200.00'), features='Features', offer_type='standard')
        offer_id = offer.id
        detail1_id = detail1.id
        detail2_id = detail2.id
        offer.delete()
        self.assertFalse(Offer.objects.filter(id=offer_id).exists())
        self.assertFalse(OfferDetail.objects.filter(id=detail1_id).exists())
        self.assertFalse(OfferDetail.objects.filter(id=detail2_id).exists())


class OfferDetailModelTests(APITestCase):
    """Tests for OfferDetail model properties and methods."""
    
    @classmethod
    def setUpTestData(cls):
        cls.business_user = User.objects.create_user(username='business1', email='business1@test.com', password='TestPass123!', type='business')
        cls.offer = Offer.objects.create(user=cls.business_user, title='Test Offer', description='Test description')
    
    def test_offerdetail_str_method(self):
        """Test OfferDetail __str__ method."""
        detail = OfferDetail.objects.create(offer=self.offer, title='Basic Package', revisions=2, delivery_time_in_days=5, price=Decimal('100.00'), features='Features', offer_type='basic')
        expected_str = f"{self.offer.title} - Basic Package"
        self.assertEqual(str(detail), expected_str)
    
    def test_offerdetail_created_at_auto_set(self):
        """Test created_at is automatically set."""
        detail = OfferDetail.objects.create(offer=self.offer, title='Package', revisions=2, delivery_time_in_days=5, price=Decimal('100.00'), features='Features', offer_type='basic')
        self.assertIsNotNone(detail.created_at)
    
    def test_offerdetail_updated_at_auto_set(self):
        """Test updated_at is automatically set."""
        detail = OfferDetail.objects.create(offer=self.offer, title='Package', revisions=2, delivery_time_in_days=5, price=Decimal('100.00'), features='Features', offer_type='basic')
        self.assertIsNotNone(detail.updated_at)
    
    def test_offerdetail_ordering_by_price(self):
        """Test offer details are ordered by price ascending."""
        detail1 = OfferDetail.objects.create(offer=self.offer, title='Expensive', revisions=10, delivery_time_in_days=15, price=Decimal('500.00'), features='Premium', offer_type='premium')
        detail2 = OfferDetail.objects.create(offer=self.offer, title='Cheap', revisions=2, delivery_time_in_days=5, price=Decimal('100.00'), features='Basic', offer_type='basic')
        detail3 = OfferDetail.objects.create(offer=self.offer, title='Medium', revisions=5, delivery_time_in_days=10, price=Decimal('250.00'), features='Standard', offer_type='standard')
        details = OfferDetail.objects.filter(offer=self.offer)
        self.assertEqual(details[0].id, detail2.id)
        self.assertEqual(details[1].id, detail3.id)
        self.assertEqual(details[2].id, detail1.id)
    
    def test_offerdetail_default_revisions(self):
        """Test default revisions value is 0."""
        detail = OfferDetail.objects.create(offer=self.offer, title='Package', delivery_time_in_days=5, price=Decimal('100.00'), features='Features', offer_type='basic')
        self.assertEqual(detail.revisions, 0)
    
    def test_offerdetail_price_decimal_places(self):
        """Test price stores decimal values correctly."""
        detail = OfferDetail.objects.create(offer=self.offer, title='Package', revisions=3, delivery_time_in_days=7, price=Decimal('123.45'), features='Features', offer_type='standard')
        self.assertEqual(float(detail.price), 123.45)
    
    def test_offerdetail_related_name_details(self):
        """Test offer.details related name works."""
        detail1 = OfferDetail.objects.create(offer=self.offer, title='Detail 1', revisions=2, delivery_time_in_days=5, price=Decimal('100.00'), features='Features', offer_type='basic')
        detail2 = OfferDetail.objects.create(offer=self.offer, title='Detail 2', revisions=5, delivery_time_in_days=10, price=Decimal('200.00'), features='Features', offer_type='standard')
        details = self.offer.details.all()
        self.assertEqual(details.count(), 2)
        self.assertIn(detail1, details)
        self.assertIn(detail2, details)
        
