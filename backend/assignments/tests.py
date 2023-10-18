from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from datetime import date
from .models import Currency, CurrencyData


class CurrencyHistoryAPITest(APITestCase):
    def setUp(self):
        # Create a sample currency
        self.currency = Currency.objects.create(
            code='USD',
            name='US Dollar',
        )

        # Create sample currency data for testing
        CurrencyData.objects.create(
            currency=self.currency,
            date=date(2023, 9, 1),
            price=75.0,
        )
        CurrencyData.objects.create(
            currency=self.currency,
            date=date(2023, 9, 2),
            price=76.0,
        )

    def test_currency_history_endpoint(self):
        # Define the URL for the currency history endpoint with query parameters
        url = reverse('currency_analytics', args=[self.currency.id])
        query_parameters = {
            'threshold': 80.0,
            'start_date': '2023-09-01',
            'end_date': '2023-09-02',
        }

        # Make a GET request to the endpoint with query parameters
        response = self.client.get(url, query_parameters, format='json')

        # Check if the response status code is 200 (OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check the response data for correctness
        expected_data = [
            {
                'id': self.currency.id,
                'date': '2023-09-01',
                'charcode': self.currency.char_code,
                'value': '75.00',
                'is_threshold_exceeded': False,
                'threshold_match_type': 'less',
                'is_min_value': True,
                'is_max_value': False,
                'percentage_ratio': '93.75',

            },
            {
                'id': self.currency.id,
                'date': '2023-09-02',
                'charcode': self.currency.char_code,
                'value': '76.00',
                'is_threshold_exceeded': False,
                'threshold_match_type': 'less',
                'is_min_value': False,
                'is_max_value': True,
                'percentage_ratio': '95.00',
            },
        ]
        self.assertEqual(response.data, expected_data)
