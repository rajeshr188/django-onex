from django.test import TestCase

# Create your tests here.
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

class RateViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.force_authenticate(user=self.user)

    def test_create_rate(self):
        url = reverse('rate-list')
        data = {
            'currency': 'USD',
            'value': 1.5
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['currency'], 'USD')
        self.assertEqual(response.data['value'], 1.5)

    def test_get_rate(self):
        rate = Rate.objects.create(currency='USD', value=1.5)
        url = reverse('rate-detail', args=[rate.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['currency'], 'USD')
        self.assertEqual(response.data['value'], 1.5)


class RateSourceViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.force_authenticate(user=self.user)

    def test_create_ratesource(self):
        url = reverse('ratesource-list')
        data = {
            'name': 'ExchangeRatesAPI',
            'url': 'https://api.exchangeratesapi.io/latest'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'ExchangeRatesAPI')
        self.assertEqual(response.data['url'], 'https://api.exchangeratesapi.io/latest')

    def test_get_ratesource(self):
        ratesource = RateSource.objects.create(name='ExchangeRatesAPI', url='https://api.exchangeratesapi.io/latest')
        url = reverse('ratesource-detail', args=[ratesource.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'ExchangeRatesAPI')
        self.assertEqual(response.data['url'], 'https://api.exchangeratesapi.io/latest')from django.test import TestCase
